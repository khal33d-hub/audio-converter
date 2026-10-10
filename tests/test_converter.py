import hashlib
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import wave

from converter import FORMATS, convert, ffmpeg_path


class ConversionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.source = self.root / "recording with spaces.wav"
        with wave.open(str(self.source), "wb") as audio:
            audio.setnchannels(2)
            audio.setsampwidth(2)
            audio.setframerate(44100)
            audio.writeframes(b"\x00\x01\x00\x01" * 44100)
        self.output = self.root / "output"

    def test_all_formats_decode(self):
        before = hashlib.sha256(self.source.read_bytes()).digest()
        for fmt in FORMATS:
            with self.subTest(fmt=fmt):
                output = convert(self.source, self.output, fmt)
                self.assertGreater(output.stat().st_size, 100)
                result = subprocess.run([ffmpeg_path(), "-v", "error", "-i", str(output), "-f", "null", "-"], capture_output=True)
                self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(before, hashlib.sha256(self.source.read_bytes()).digest())

    def test_m4a_to_wav_properties(self):
        m4a = convert(self.source, self.output, "m4a")
        wav = convert(m4a, self.output, "wav", 16000, 1)
        with wave.open(str(wav), "rb") as audio:
            self.assertEqual(audio.getframerate(), 16000)
            self.assertEqual(audio.getnchannels(), 1)
            self.assertEqual(audio.getsampwidth(), 2)
            self.assertAlmostEqual(audio.getnframes() / 16000, 1.0, delta=0.1)

    def test_collision_preserves_existing_and_source(self):
        before = self.source.read_bytes()
        first = convert(self.source, self.root)
        second = convert(self.source, self.root)
        self.assertEqual(first.stem, "recording with spaces (1)")
        self.assertEqual(second.stem, "recording with spaces (2)")
        self.assertEqual(before, self.source.read_bytes())

    def test_bad_input_leaves_no_output(self):
        bad = self.root / "bad.m4a"
        bad.write_text("not audio")
        with self.assertRaises(RuntimeError):
            convert(bad, self.output)
        self.assertEqual(list(self.output.iterdir()), [])

    def test_validation(self):
        for kwargs in ({"fmt": "exe"}, {"sample_rate": 0}, {"channels": 7}):
            with self.assertRaises(ValueError):
                convert(self.source, self.output, **kwargs)
        with self.assertRaises(ValueError):
            convert(self.root / "missing.m4a", self.output)

    def test_cli_continues_after_failure(self):
        result = subprocess.run([sys.executable, "converter.py", str(self.root / "missing"), str(self.source), "-o", str(self.output)], capture_output=True, text=True)
        self.assertEqual(result.returncode, 1)
        self.assertTrue((self.output / self.source.name).is_file())


if __name__ == "__main__":
    unittest.main()
