import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

import numpy as np
import soundfile as sf

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import evaluate as ev  # noqa: E402
import voxclarity as vc  # noqa: E402


class MetricTests(unittest.TestCase):
    def test_normalize(self):
        self.assertEqual(ev.normalize("Ik wil, aangifte doen!  Café-tje"), ["ik", "wil", "aangifte", "doen", "café", "tje"])

    def test_wer_counts(self):
        r = ev.wer("ik wil aangifte doen".split(), "ik wil graag doen".split())
        self.assertEqual((r.substitutions, r.deletions, r.insertions), (1, 0, 0))
        self.assertAlmostEqual(r.wer, 0.25)
        r = ev.wer("a b c d".split(), "a d".split())
        self.assertEqual((r.deletions, r.insertions), (2, 0))
        r = ev.wer("a b".split(), "a b c".split())
        self.assertEqual(r.insertions, 1)

    def test_wer_edge_cases(self):
        self.assertEqual(ev.wer([], []).wer, 0.0)
        self.assertEqual(ev.wer([], ["x"]).wer, 1.0)
        self.assertEqual(ev.wer(["x", "y"], []).wer, 1.0)

    def test_compare_finds_dropped_and_added(self):
        orig = [("Ik", 0, .2), ("wil", .2, .4), ("niet", .4, .6), ("weg", .6, .9)]
        clean = [("Ik", 0, .2), ("wil", .2, .4), ("weg", .6, .9), ("nu", 1, 1.2)]
        c = ev.compare_transcripts(orig, clean)
        self.assertEqual([d["word"] for d in c["dropped"]], ["niet"])
        self.assertEqual([a["word"] for a in c["added"]], ["nu"])

    def test_group_passages(self):
        items = [{"word": "a", "start": 1, "end": 1.2}, {"word": "b", "start": 1.5, "end": 1.7}, {"word": "c", "start": 9, "end": 9.2}]
        g = ev.group_passages(items)
        self.assertEqual([p["text"] for p in g], ["a b", "c"])


class PipelineTests(unittest.TestCase):
    def test_end_to_end_with_fake_whisper(self):
        tmp = Path(tempfile.mkdtemp())
        rng = np.random.default_rng(0)
        sf.write(tmp / "a.wav", rng.normal(0, 0.1, 16000 * 3).astype(np.float32), 16000)
        (tmp / "refs").mkdir()
        (tmp / "refs" / "a.txt").write_text("Ik wil aangifte doen.", encoding="utf-8")

        def fake(path: Path):
            if path.name.endswith(".schoon.wav"):
                return [("Ik", 0, .2), ("aangifte", .5, .9), ("doen", .9, 1.1)]  # 'wil' weggevallen
            return [("Ik", 0, .2), ("wil", .2, .5), ("aangifte", .5, .9), ("doen", .9, 1.1)]

        (tmp / "work").mkdir()
        row = ev.evaluate_file(tmp / "a.wav", tmp / "work", fake, vc.Options(), tmp / "refs" / "a.txt")
        self.assertEqual(row["wer_original"], 0.0)
        self.assertEqual(row["wer_clean"], 0.25)
        self.assertEqual(row["words_dropped"], 1)
        self.assertEqual(row["_detail"]["dropped_passages"][0]["text"], "wil")
        md = ev.render_markdown([row], vc.Options(), "fake", redact=False)
        self.assertIn("slechter door opschonen", md)
        self.assertIn("“wil”", md)
        self.assertIn("(verborgen)", ev.render_markdown([row], vc.Options(), "fake", redact=True))
        shutil.rmtree(tmp)


if __name__ == "__main__":
    unittest.main()
