#!/usr/bin/env python3
"""VoxClarity evaluatie: helpt het opschonen echt, en gaan er geen woorden verloren?

Per opname:
  1. transcribeer het origineel met Whisper (lokaal, faster-whisper)
  2. maak met VoxClarity de schone versie en transcribeer die ook
  3. vergelijk. Met een handmatige referentie (<naam>.txt) wordt de woordfoutscore (WER)
     van beide berekend. Zonder referentie worden origineel en schoon met elkaar vergeleken

Uitvoer in --out: results.csv, report.md en details/<naam>.json.

BELANGRIJK bij lezen van de resultaten
  * Zonder referentie is het origineel niet de waarheid. "Weggevallen woorden" kunnen echte
    spraak zijn die VoxClarity ten onrechte dempte, maar ook ruis die Whisper in het origineel
    als woorden hoorde. Luister bij elke weggevallen passage naar het tijdstip in het origineel.
  * De rapporten bevatten volledige transcripties van aangiftemateriaal. Bewaar ze net zo
    beveiligd als de opnames, of gebruik --redact om alleen aantallen op te slaan.
"""
from __future__ import annotations

import argparse
import csv
import difflib
import json
import re
import statistics
import sys
import unicodedata
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

sys.path.insert(0, str(Path(__file__).resolve().parent))
import voxclarity as vc  # noqa: E402

Word = tuple[str, float, float]  # (woord, start_s, eind_s)
Transcriber = Callable[[Path], list[Word]]


# ------------------------------------------------------------------ tekstmaat


def normalize(text: str) -> list[str]:
    """Kleine letters, geen leestekens, vaste unicode-vorm. Cijfers blijven staan."""
    text = unicodedata.normalize("NFKC", text).lower()
    text = re.sub(r"[^\w\s']", " ", text)
    text = text.replace("_", " ")
    return text.split()


@dataclass
class Wer:
    wer: float
    substitutions: int
    deletions: int
    insertions: int
    ref_words: int


def wer(ref: list[str], hyp: list[str]) -> Wer:
    """Woordfoutscore via Levenshtein met backtrace (S, D, I)."""
    n, m = len(ref), len(hyp)
    d = [[0] * (m + 1) for _ in range(n + 1)]
    for i in range(n + 1):
        d[i][0] = i
    for j in range(m + 1):
        d[0][j] = j
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            cost = 0 if ref[i - 1] == hyp[j - 1] else 1
            d[i][j] = min(d[i - 1][j] + 1, d[i][j - 1] + 1, d[i - 1][j - 1] + cost)
    i, j, s, dele, ins = n, m, 0, 0, 0
    while i > 0 or j > 0:
        if i > 0 and j > 0 and d[i][j] == d[i - 1][j - 1] + (0 if ref[i - 1] == hyp[j - 1] else 1):
            s += ref[i - 1] != hyp[j - 1]
            i, j = i - 1, j - 1
        elif i > 0 and d[i][j] == d[i - 1][j] + 1:
            dele += 1
            i -= 1
        else:
            ins += 1
            j -= 1
    return Wer((s + dele + ins) / n if n else float(m > 0), s, dele, ins, n)


def compare_transcripts(orig: list[Word], clean: list[Word]) -> dict:
    """Wat staat alleen in het origineel (mogelijk weggevallen) en wat alleen in de schone versie."""
    a = [normalize(w)[0] if normalize(w) else "" for w, _, _ in orig]
    b = [normalize(w)[0] if normalize(w) else "" for w, _, _ in clean]
    sm = difflib.SequenceMatcher(a=a, b=b, autojunk=False)
    dropped, added = [], []
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag in ("delete", "replace"):
            dropped += [{"word": orig[i][0], "start": round(orig[i][1], 2), "end": round(orig[i][2], 2)} for i in range(i1, i2)]
        if tag in ("insert", "replace"):
            added += [{"word": clean[j][0], "start": round(clean[j][1], 2), "end": round(clean[j][2], 2)} for j in range(j1, j2)]
    return {"dropped": dropped, "added": added, "similarity": round(sm.ratio(), 4)}


def group_passages(items: list[dict], gap_s: float = 1.5) -> list[dict]:
    """Voeg opeenvolgende woorden samen tot passages met tijdstip, om te kunnen luisteren."""
    out: list[dict] = []
    for it in items:
        if out and it["start"] - out[-1]["end"] <= gap_s:
            out[-1]["text"] += " " + it["word"]
            out[-1]["end"] = it["end"]
        else:
            out.append({"start": it["start"], "end": it["end"], "text": it["word"]})
    return out


# -------------------------------------------------------------------- Whisper


def make_whisper(model: str, language: str | None, device: str, compute_type: str) -> Transcriber:
    try:
        from faster_whisper import WhisperModel
    except ImportError:
        raise SystemExit("faster-whisper ontbreekt. Installeer met: pip install faster-whisper")
    m = WhisperModel(model, device=device, compute_type=compute_type)

    def transcribe(path: Path) -> list[Word]:
        # Deterministisch: temperature 0, geen context uit eerdere tekst (beperkt hallucinaties op stilte)
        segs, _ = m.transcribe(
            str(path), language=language, beam_size=5, temperature=0.0,
            condition_on_previous_text=False, word_timestamps=True, vad_filter=False,
        )
        return [(w.word.strip(), w.start, w.end) for s in segs for w in (s.words or []) if w.word.strip()]

    return transcribe


# ------------------------------------------------------------------- pipeline


def evaluate_file(src: Path, workdir: Path, transcribe: Transcriber, opt: vc.Options, ref_path: Path | None) -> dict:
    clean_path = workdir / (src.stem + ".schoon.wav")
    report = vc.clean_audio(src, clean_path, opt)
    orig_words = transcribe(src)
    clean_words = transcribe(clean_path)

    row: dict = {
        "file": src.name,
        "duration_s": report.duration_s,
        "speech_ratio": report.speech_ratio,
        "words_original": len(orig_words),
        "words_clean": len(clean_words),
    }
    cmp = compare_transcripts(orig_words, clean_words)
    row.update(words_dropped=len(cmp["dropped"]), words_added=len(cmp["added"]), similarity=cmp["similarity"])

    detail: dict = {
        "file": src.name,
        "voxclarity_report": json.loads(Path(str(clean_path) + ".json").read_text()),
        "transcript_original": " ".join(w for w, _, _ in orig_words),
        "transcript_clean": " ".join(w for w, _, _ in clean_words),
        "dropped_passages": group_passages(cmp["dropped"]),
        "added_passages": group_passages(cmp["added"]),
    }
    if ref_path and ref_path.exists():
        ref = normalize(ref_path.read_text(encoding="utf-8"))
        wo = wer(ref, normalize(detail["transcript_original"]))
        wc = wer(ref, normalize(detail["transcript_clean"]))
        row.update(wer_original=round(wo.wer, 4), wer_clean=round(wc.wer, 4), wer_delta=round(wc.wer - wo.wer, 4),
                   del_original=wo.deletions, del_clean=wc.deletions, ref_words=wo.ref_words)
        detail["wer"] = {"original": wo.__dict__, "clean": wc.__dict__}
    return row | {"_detail": detail}


def pct(x: float) -> str:
    return f"{x * 100:.1f}%"


def render_markdown(rows: list[dict], opt: vc.Options, model: str, redact: bool) -> str:
    L = ["# VoxClarity evaluatie", "", f"Whisper-model: `{model}` · VAD-drempel: {opt.vad_threshold} · passes: {opt.denoise_passes} · extra denoise: {opt.extra_denoise}", ""]
    with_ref = [r for r in rows if "wer_original" in r]
    L += ["## Samenvatting", "", f"- Opnames: {len(rows)} (met handmatige referentie: {len(with_ref)})"]
    if with_ref:
        mo = statistics.mean(r["wer_original"] for r in with_ref)
        mc = statistics.mean(r["wer_clean"] for r in with_ref)
        better = sum(r["wer_delta"] < -0.005 for r in with_ref)
        worse = sum(r["wer_delta"] > 0.005 for r in with_ref)
        L += [f"- Gemiddelde WER origineel: **{pct(mo)}** · schoon: **{pct(mc)}**",
              f"- Beter: {better} · slechter: {worse} · gelijk: {len(with_ref) - better - worse}"]
        if worse:
            L += ["", f"> **{worse} opname(n) werden slechter door opschonen.** Bekijk die eerst (tabel hieronder) voordat je VoxClarity inzet."]
    else:
        L += ["- Geen referenties: alleen origineel-versus-schoon vergelijking. Dit toont wat er verandert, niet wat goed is."]
    L += ["", "## Per opname", ""]
    cols = ["Opname", "Duur", "Spraak", "WER orig.", "WER schoon", "Δ", "Woorden weg", "Woorden erbij"]
    L += ["| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)]
    for r in sorted(rows, key=lambda r: -r.get("wer_delta", -9)):
        L.append("| {} | {:.0f}s | {} | {} | {} | {} | {} | {} |".format(
            r["file"], r["duration_s"], pct(r["speech_ratio"]),
            pct(r["wer_original"]) if "wer_original" in r else "-", pct(r["wer_clean"]) if "wer_clean" in r else "-",
            f"{r['wer_delta'] * 100:+.1f}" if "wer_delta" in r else "-", r["words_dropped"], r["words_added"]))
    L += ["", "## Weggevallen passages (staan wel in het origineel, niet in de schone versie)", "",
          "Luister naar het origineel op het genoemde tijdstip. Is het echte spraak, dan dempt VoxClarity te hard: verlaag `--threshold` of verhoog `--pad-ms`.", ""]
    for r in rows:
        ps = r["_detail"]["dropped_passages"]
        if not ps:
            continue
        L.append(f"**{r['file']}**")
        for p in ps[:15]:
            txt = "(verborgen)" if redact else f"“{p['text']}”"
            L.append(f"- {p['start']:.1f}s tot {p['end']:.1f}s: {txt}")
        L.append("")
    L += ["## Hoe te lezen", "",
          "- Negatieve Δ = schoon is beter. Positieve Δ = schoon is slechter.",
          "- WER telt vervangingen, weglatingen en toevoegingen als fout. Whisper voegt op stilte of ruis soms zelf tekst toe (hallucinatie), dat verklaart vaak een betere score na opschonen.",
          "- Een kleine set (minder dan 20 opnames) geeft een indicatie, geen bewijs. Kijk naar de uitschieters, niet alleen naar het gemiddelde."]
    return "\n".join(L) + "\n"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="evaluate", description="Vergelijk transcripties van origineel en VoxClarity-versie met Whisper.")
    ap.add_argument("audio_dir", type=Path, help="map met opnames")
    ap.add_argument("--refs", type=Path, help="map met handmatige transcripties: <opnamenaam zonder extensie>.txt")
    ap.add_argument("--out", type=Path, default=Path("voxclarity_eval"))
    ap.add_argument("--model", default="large-v3", help="faster-whisper model (large-v3, medium, small ...)")
    ap.add_argument("--language", default="nl", help="taalcode, of 'auto'")
    ap.add_argument("--device", default="auto", help="auto, cpu of cuda")
    ap.add_argument("--compute-type", default="default", help="bv. int8 voor snelle cpu-run")
    ap.add_argument("--redact", action="store_true", help="geen transcriptietekst in report.md (details/*.json bevatten die nog wel)")
    ap.add_argument("--threshold", type=float, default=vc.Options().vad_threshold)
    ap.add_argument("--passes", type=int, default=1)
    ap.add_argument("--extra-denoise", action="store_true")
    ap.add_argument("--pad-ms", type=int, default=vc.Options().pad_ms)
    args = ap.parse_args(argv)

    files = vc.collect_inputs(args.audio_dir)
    if not files:
        print("Geen audiobestanden gevonden", file=sys.stderr)
        return 2
    opt = vc.Options(vad_threshold=args.threshold, denoise_passes=args.passes, extra_denoise=args.extra_denoise, pad_ms=args.pad_ms)
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / "details").mkdir(exist_ok=True)
    work = args.out / "schoon"
    work.mkdir(exist_ok=True)
    transcribe = make_whisper(args.model, None if args.language == "auto" else args.language, args.device, args.compute_type)

    rows = []
    for i, f in enumerate(files, 1):
        print(f"[{i}/{len(files)}] {f.name}", flush=True)
        ref = args.refs / (f.stem + ".txt") if args.refs else None
        try:
            r = evaluate_file(f, work, transcribe, opt, ref)
        except Exception as e:  # noqa: BLE001
            print(f"  MISLUKT: {e}", file=sys.stderr)
            continue
        (args.out / "details" / (f.stem + ".json")).write_text(json.dumps(r["_detail"], indent=2, ensure_ascii=False), encoding="utf-8")
        rows.append(r)

    if not rows:
        return 1
    fields = [k for k in rows[0] if k != "_detail"]
    for r in rows:
        fields += [k for k in r if k not in fields and k != "_detail"]
    with open(args.out / "results.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)
    (args.out / "report.md").write_text(render_markdown(rows, opt, args.model, args.redact), encoding="utf-8")
    print(f"Klaar. Open {args.out / 'report.md'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
