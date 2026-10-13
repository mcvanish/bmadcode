#!/usr/bin/env python3
"""CleanTranscriber.

Maakt van een opname met achtergrondgeluid een bestand waarin alleen stemmen
overblijven, bedoeld als invoer voor transcriptie.

Pipeline (alles lokaal, er verlaat geen audio de machine):

  1. Decoderen naar 48 kHz mono (ffmpeg), hoogdoorlaatfilter 80 Hz
  2. RNNoise: neuraal netwerk dat spraak van ruis scheidt (ook onder de spraak)
  3. Silero VAD: bepaalt per 32 ms of er een stem klinkt. Alles wat geen stem
     is (deurslag, muziek, verkeer, stilte) wordt gedempt
  4. Optioneel: extra spectrale ruisreductie
  5. Loudness-normalisatie op de stemfragmenten
  6. WAV-uitvoer (16 kHz mono) plus een JSON-rapport met checksums

De tijdlijn blijft standaard intact: stilte wordt gedempt, niet verwijderd,
zodat tijdstempels uit de transcriptie kloppen met het originele bestand.
Het originele bestand wordt nooit aangepast.
"""
from __future__ import annotations

import argparse
import ctypes
import datetime as dt
import hashlib
import json
import platform
import subprocess
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path

import numpy as np
from scipy import signal

__version__ = "1.0.0"

PROC_SR = 48_000  # RNNoise werkt op 48 kHz
RNNOISE_DELAY = 960  # interne vertraging van RNNoise (20 ms), wordt gecompenseerd
VAD_SR = 16_000  # Silero werkt op 16 kHz
VAD_WINDOW = 512  # samples per VAD-venster bij 16 kHz (32 ms)
VAD_CONTEXT = 64
MODEL_PATH = Path(__file__).parent / "models" / "silero_vad.onnx"
AUDIO_EXTS = {".wav", ".mp3", ".m4a", ".aac", ".ogg", ".opus", ".flac", ".wma", ".amr", ".mp4", ".mov", ".3gp", ".webm", ".mkv"}


@dataclass
class Options:
    vad_threshold: float = 0.5  # kans waarboven een venster als stem telt
    min_speech_ms: int = 200  # kortere stemfragmenten worden weggegooid
    min_gap_ms: int = 350  # kortere pauzes tussen stem worden overbrugd
    pad_ms: int = 150  # marge rond elk stemfragment (voorkomt afgekapte woorden)
    fade_ms: int = 20  # zachte overgang bij dempen (voorkomt klikken)
    denoise_passes: int = 1  # aantal RNNoise-rondes (2 = agressiever)
    extra_denoise: bool = False  # extra spectrale ruisreductie na RNNoise
    keep_noise_db: float | None = None  # None = niet-stem volledig stil; anders restniveau in dB (bv. -50)
    trim_silence: bool = False  # niet-stem wegknippen i.p.v. dempen (tijdlijn verschuift!)
    target_dbfs: float = -20.0  # doelniveau (RMS over stemfragmenten)
    out_sr: int = 16_000
    vad_source: str = "both"  # "clean", "original" of "both" (vereniging van beide)


@dataclass
class Report:
    tool_version: str
    created_utc: str
    input_file: str
    input_sha256: str
    output_file: str
    output_sha256: str
    duration_s: float
    speech_s: float
    speech_ratio: float
    segments: list = field(default_factory=list)  # [{"start": s, "end": s}] in tijdlijn van het origineel
    options: dict = field(default_factory=dict)
    warnings: list = field(default_factory=list)
    environment: dict = field(default_factory=dict)


# --------------------------------------------------------------------------- IO


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def decode(path: Path, sr: int = PROC_SR) -> np.ndarray:
    """Decodeer elk formaat dat ffmpeg kent naar mono float32 in [-1, 1]."""
    cmd = ["ffmpeg", "-v", "error", "-nostdin", "-i", str(path), "-vn", "-ac", "1", "-ar", str(sr), "-f", "f32le", "-"]
    try:
        proc = subprocess.run(cmd, capture_output=True, check=True)
    except FileNotFoundError:
        raise SystemExit("ffmpeg niet gevonden. Installeer ffmpeg (bv. `apt install ffmpeg`).")
    except subprocess.CalledProcessError as e:
        raise ValueError(f"Kan {path.name} niet decoderen: {e.stderr.decode(errors='replace').strip()}") from e
    audio = np.frombuffer(proc.stdout, dtype="<f4").astype(np.float32)
    if audio.size == 0:
        raise ValueError(f"{path.name} bevat geen audio")
    return audio


def write_wav(path: Path, audio: np.ndarray, sr: int) -> None:
    import soundfile as sf

    sf.write(str(path), np.clip(audio, -1.0, 1.0), sr, subtype="PCM_16")


# ------------------------------------------------------------------ denoising


def highpass(audio: np.ndarray, sr: int, cutoff: float = 80.0) -> np.ndarray:
    sos = signal.butter(4, cutoff, btype="highpass", fs=sr, output="sos")
    return signal.sosfiltfilt(sos, audio).astype(np.float32)


def rnnoise_denoise(audio: np.ndarray, passes: int = 1) -> np.ndarray:
    """RNNoise via de meegeleverde C-bibliotheek van pyrnnoise (48 kHz, mono)."""
    from pyrnnoise import rnnoise as rn

    frame = rn.FRAME_SIZE  # 480 samples = 10 ms
    out = audio
    for _ in range(max(1, passes)):
        pcm = np.clip(out, -1.0, 1.0)
        pcm = (pcm * 32767.0).astype(np.float32)
        n = (len(pcm) + RNNOISE_DELAY + frame - 1) // frame * frame
        pcm = np.pad(pcm, (0, n - len(pcm)))
        res = np.empty_like(pcm)
        state = rn.create()
        try:
            for i in range(0, n, frame):
                buf = np.ascontiguousarray(pcm[i : i + frame])
                rn.lib.rnnoise_process_frame(state, buf.ctypes.data_as(ctypes.POINTER(ctypes.c_float)), buf.ctypes.data_as(ctypes.POINTER(ctypes.c_float)))
                res[i : i + frame] = buf
        finally:
            rn.destroy(state)
        out = (res[RNNOISE_DELAY : RNNOISE_DELAY + len(audio)] / 32767.0).astype(np.float32)  # vertraging eruit: tijdlijn blijft gelijk
    return out


def spectral_denoise(audio: np.ndarray, sr: int) -> np.ndarray:
    import noisereduce as nr

    return nr.reduce_noise(y=audio, sr=sr, stationary=False, prop_decrease=0.85).astype(np.float32)


# ------------------------------------------------------------------------ VAD


class SileroVAD:
    def __init__(self, model_path: Path = MODEL_PATH):
        import onnxruntime as ort

        if not model_path.exists():
            raise FileNotFoundError(f"VAD-model ontbreekt: {model_path}")
        opts = ort.SessionOptions()
        opts.inter_op_num_threads = 1
        opts.intra_op_num_threads = 1
        self.session = ort.InferenceSession(str(model_path), sess_options=opts, providers=["CPUExecutionProvider"])

    def probabilities(self, audio16k: np.ndarray) -> np.ndarray:
        """Stemkans per venster van 32 ms."""
        n = (len(audio16k) + VAD_WINDOW - 1) // VAD_WINDOW * VAD_WINDOW
        x = np.pad(audio16k.astype(np.float32), (0, n - len(audio16k)))
        state = np.zeros((2, 1, 128), dtype=np.float32)
        context = np.zeros((1, VAD_CONTEXT), dtype=np.float32)
        sr = np.array(VAD_SR, dtype=np.int64)
        probs = np.empty(n // VAD_WINDOW, dtype=np.float32)
        for k in range(len(probs)):
            chunk = x[k * VAD_WINDOW : (k + 1) * VAD_WINDOW][None, :]
            inp = np.concatenate([context, chunk], axis=1)
            out, state = self.session.run(None, {"input": inp, "state": state, "sr": sr})
            probs[k] = out[0, 0]
            context = inp[:, -VAD_CONTEXT:]
        return probs


def probs_to_segments(probs: np.ndarray, opt: Options) -> list[tuple[float, float]]:
    """Kansen -> stemfragmenten (seconden), met hysterese, pauze-overbrugging en marge."""
    win_s = VAD_WINDOW / VAD_SR
    on, off = opt.vad_threshold, max(opt.vad_threshold - 0.15, 0.05)
    segs: list[list[float]] = []
    active = False
    start = 0.0
    for i, p in enumerate(probs):
        t = i * win_s
        if not active and p >= on:
            active, start = True, t
        elif active and p < off:
            active = False
            segs.append([start, t])
    if active:
        segs.append([start, len(probs) * win_s])

    gap = opt.min_gap_ms / 1000
    merged: list[list[float]] = []
    for s in segs:
        if merged and s[0] - merged[-1][1] < gap:
            merged[-1][1] = s[1]
        else:
            merged.append(s)
    min_len = opt.min_speech_ms / 1000
    kept = [s for s in merged if s[1] - s[0] >= min_len]

    pad = opt.pad_ms / 1000
    total = len(probs) * win_s
    padded: list[list[float]] = []
    for s in kept:
        a, b = max(0.0, s[0] - pad), min(total, s[1] + pad)
        if padded and a <= padded[-1][1]:
            padded[-1][1] = b
        else:
            padded.append([a, b])
    return [(a, b) for a, b in padded]


def detect_speech(vad: SileroVAD, clean48: np.ndarray, orig48: np.ndarray, opt: Options) -> list[tuple[float, float]]:
    def to16(x):
        return signal.resample_poly(x, 1, PROC_SR // VAD_SR).astype(np.float32)

    probs = []
    if opt.vad_source in ("clean", "both"):
        probs.append(vad.probabilities(to16(clean48)))
    if opt.vad_source in ("original", "both"):
        probs.append(vad.probabilities(to16(orig48)))
    p = np.maximum.reduce(probs)  # "both": stem in een van beide = stem
    return probs_to_segments(p, opt)


# ------------------------------------------------------------------- masking


def build_gain(n: int, segments: list[tuple[float, float]], opt: Options) -> np.ndarray:
    floor = 0.0 if opt.keep_noise_db is None else 10 ** (opt.keep_noise_db / 20)
    gain = np.full(n, floor, dtype=np.float32)
    for a, b in segments:
        gain[int(a * PROC_SR) : int(b * PROC_SR)] = 1.0
    fade = int(opt.fade_ms / 1000 * PROC_SR)
    if fade > 1:
        win = np.hanning(fade * 2 + 1).astype(np.float32)
        gain = np.convolve(gain, win / win.sum(), mode="same")
    return gain


def normalize(audio: np.ndarray, gain: np.ndarray, target_dbfs: float) -> np.ndarray:
    voiced = audio[gain > 0.9]
    if voiced.size < 1000:
        return audio
    rms = float(np.sqrt(np.mean(voiced**2)))
    if rms < 1e-6:
        return audio
    g = min(10 ** (target_dbfs / 20) / rms, 10 ** (24 / 20))  # max +24 dB
    out = audio * g
    peak = float(np.max(np.abs(out)))
    if peak > 0.97:
        out *= 0.97 / peak
    return out.astype(np.float32)


# ------------------------------------------------------------------- pipeline


def clean_audio(input_path: str | Path, output_path: str | Path, opt: Options | None = None, vad: SileroVAD | None = None) -> Report:
    """Schoon één bestand op. Schrijft `output_path` en `<output_path>.json`."""
    opt = opt or Options()
    src, dst = Path(input_path).resolve(), Path(output_path).resolve()
    if src == dst:
        raise ValueError("Uitvoer mag niet hetzelfde zijn als het originele bestand")
    dst.parent.mkdir(parents=True, exist_ok=True)

    warnings: list[str] = []
    input_hash = sha256_file(src)
    orig = decode(src)
    duration = len(orig) / PROC_SR
    if duration < 0.5:
        warnings.append("Opname is korter dan 0,5 seconde")

    hp = highpass(orig, PROC_SR)
    clean = rnnoise_denoise(hp, opt.denoise_passes)
    if opt.extra_denoise:
        clean = spectral_denoise(clean, PROC_SR)

    vad = vad or SileroVAD()
    segments = detect_speech(vad, clean, hp, opt)
    if not segments:
        warnings.append("Geen spraak gedetecteerd. Uitvoer is stil. Controleer het origineel of verlaag --threshold")

    gain = build_gain(len(clean), segments, opt)
    result = normalize(clean * gain, gain, opt.target_dbfs)

    if opt.trim_silence and segments:
        warnings.append("--trim-silence actief: tijdstempels in de uitvoer wijken af van het origineel (zie segments in dit rapport)")
        result = np.concatenate([result[int(a * PROC_SR) : int(b * PROC_SR)] for a, b in segments])

    if opt.out_sr != PROC_SR:
        g = np.gcd(PROC_SR, opt.out_sr)
        result = signal.resample_poly(result, opt.out_sr // g, PROC_SR // g).astype(np.float32)
    write_wav(dst, result, opt.out_sr)

    speech_s = sum(b - a for a, b in segments)
    report = Report(
        tool_version=__version__,
        created_utc=dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        input_file=src.name,
        input_sha256=input_hash,
        output_file=dst.name,
        output_sha256=sha256_file(dst),
        duration_s=round(duration, 3),
        speech_s=round(speech_s, 3),
        speech_ratio=round(speech_s / duration, 4) if duration else 0.0,
        segments=[{"start": round(a, 3), "end": round(b, 3)} for a, b in segments],
        options=asdict(opt),
        warnings=warnings,
        environment={"python": platform.python_version(), "numpy": np.__version__, "models": ["RNNoise (pyrnnoise)", "Silero VAD v5"]},
    )
    Path(str(dst) + ".json").write_text(json.dumps(asdict(report), indent=2, ensure_ascii=False), encoding="utf-8")
    return report


# ------------------------------------------------------------------------ CLI


def collect_inputs(p: Path) -> list[Path]:
    if p.is_dir():
        return sorted(f for f in p.rglob("*") if f.suffix.lower() in AUDIO_EXTS)
    return [p]


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="cleantranscriber", description="Verwijder achtergrondgeluid en laat alleen stemmen over, voor transcriptie.")
    ap.add_argument("input", type=Path, help="audiobestand of map met audiobestanden")
    ap.add_argument("-o", "--output", type=Path, help="uitvoerbestand (.wav) of map. Standaard: <naam>.schoon.wav naast het origineel")
    d = Options()
    ap.add_argument("--threshold", type=float, default=d.vad_threshold, help="stemgevoeligheid 0-1. Lager = meer wordt behouden (standaard %(default)s)")
    ap.add_argument("--pad-ms", type=int, default=d.pad_ms, help="marge rond stemfragmenten (standaard %(default)s)")
    ap.add_argument("--min-gap-ms", type=int, default=d.min_gap_ms)
    ap.add_argument("--min-speech-ms", type=int, default=d.min_speech_ms)
    ap.add_argument("--passes", type=int, default=d.denoise_passes, help="aantal RNNoise-rondes (standaard %(default)s)")
    ap.add_argument("--extra-denoise", action="store_true", help="extra spectrale ruisreductie voor zeer rumoerige opnames")
    ap.add_argument("--keep-noise-db", type=float, default=None, help="laat niet-stem op dit niveau staan i.p.v. volledig stil (bv. -50)")
    ap.add_argument("--trim-silence", action="store_true", help="knip niet-stem weg. Let op: tijdstempels verschuiven")
    ap.add_argument("--sample-rate", type=int, default=d.out_sr, choices=[16000, 24000, 48000], help="samplefrequentie van de uitvoer (standaard %(default)s)")
    ap.add_argument("--target-dbfs", type=float, default=d.target_dbfs)
    ap.add_argument("--vad-source", choices=["clean", "original", "both"], default=d.vad_source)
    args = ap.parse_args(argv)

    opt = Options(
        vad_threshold=args.threshold, min_speech_ms=args.min_speech_ms, min_gap_ms=args.min_gap_ms, pad_ms=args.pad_ms,
        denoise_passes=args.passes, extra_denoise=args.extra_denoise, keep_noise_db=args.keep_noise_db,
        trim_silence=args.trim_silence, target_dbfs=args.target_dbfs, out_sr=args.sample_rate, vad_source=args.vad_source,
    )
    if not args.input.exists():
        print(f"Niet gevonden: {args.input}", file=sys.stderr)
        return 2
    files = collect_inputs(args.input)
    if not files:
        print("Geen audiobestanden gevonden", file=sys.stderr)
        return 2

    vad = SileroVAD()
    failed = 0
    for f in files:
        if args.output and (len(files) > 1 or args.output.is_dir() or args.output.suffix == ""):
            out = args.output / (f.stem + ".schoon.wav")
        elif args.output:
            out = args.output
        else:
            out = f.with_name(f.stem + ".schoon.wav")
        if f.name.endswith(".schoon.wav"):
            continue
        try:
            r = clean_audio(f, out, opt, vad)
            print(f"{f.name} -> {out.name}  spraak {r.speech_s:.1f}s van {r.duration_s:.1f}s ({r.speech_ratio:.0%})")
            for w in r.warnings:
                print(f"  LET OP: {w}")
        except Exception as e:  # noqa: BLE001 - per bestand doorgaan bij batchverwerking
            failed += 1
            print(f"{f.name}: MISLUKT. {e}", file=sys.stderr)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
