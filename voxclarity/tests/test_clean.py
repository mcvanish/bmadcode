import hashlib
import json
import sys
import unittest
from pathlib import Path
import tempfile

import numpy as np
import soundfile as sf

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import voxclarity as sh  # noqa: E402


def noise_file(path, seconds=6, sr=16000):
    rng = np.random.default_rng(0)
    x = rng.normal(0, 0.1, seconds * sr).astype(np.float32)
    x[sr * 2 : sr * 2 + 4000] += rng.normal(0, 0.8, 4000).astype(np.float32)  # "deurslag"
    sf.write(path, x, sr)


class CleanTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.src = self.tmp / "ruis.wav"
        noise_file(self.src)

    def test_noise_only_becomes_silent_and_timeline_is_kept(self):
        out = self.tmp / "out.wav"
        r = sh.clean_audio(self.src, out)
        y, sr = sf.read(out)
        self.assertEqual(sr, 16000)
        self.assertAlmostEqual(len(y) / sr, 6.0, places=1)
        self.assertLess(np.max(np.abs(y)), 0.01)
        self.assertEqual(r.segments, [])
        self.assertTrue(r.warnings)

    def test_original_untouched_and_report_hashes(self):
        before = hashlib.sha256(self.src.read_bytes()).hexdigest()
        out = self.tmp / "out.wav"
        sh.clean_audio(self.src, out)
        self.assertEqual(hashlib.sha256(self.src.read_bytes()).hexdigest(), before)
        rep = json.loads((self.tmp / "out.wav.json").read_text())
        self.assertEqual(rep["input_sha256"], before)
        self.assertEqual(rep["output_sha256"], hashlib.sha256(out.read_bytes()).hexdigest())

    def test_refuses_to_overwrite_input(self):
        with self.assertRaises(ValueError):
            sh.clean_audio(self.src, self.src)

    def test_segment_logic(self):
        o = sh.Options(min_speech_ms=200, min_gap_ms=350, pad_ms=0)
        w = sh.VAD_WINDOW / sh.VAD_SR
        p = np.zeros(100, dtype=np.float32)
        p[10:30] = 0.9   # 0,64 s stem
        p[35:50] = 0.9   # pauze < 350 ms wordt overbrugd
        p[70:72] = 0.9   # 64 ms: te kort, vervalt
        segs = sh.probs_to_segments(p, o)
        self.assertEqual(len(segs), 1)
        self.assertAlmostEqual(segs[0][0], 10 * w, places=3)
        self.assertAlmostEqual(segs[0][1], 50 * w, places=3)


if __name__ == "__main__":
    unittest.main()
