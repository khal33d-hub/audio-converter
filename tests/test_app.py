"""Exercise the desktop worker and UI event loop without displaying a window."""
from pathlib import Path
import tempfile
import time
import tkinter as tk
import unittest
import wave

from app import App


class DesktopTests(unittest.TestCase):
    def test_batch_reports_success_and_error_and_reenables_controls(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "input.wav"
            with wave.open(str(source), "wb") as audio:
                audio.setnchannels(1)
                audio.setsampwidth(2)
                audio.setframerate(16000)
                audio.writeframes(b"\x00\x01" * 1600)
            root = tk.Tk()
            root.withdraw()
            try:
                app = App(root)
                app.files = [str(source), str(Path(directory) / "missing.m4a")]
                app.output.set(str(Path(directory) / "results"))
                app.run()
                self.assertTrue(app.busy)
                self.assertTrue(app.start.instate(["disabled"]))
                deadline = time.monotonic() + 20
                while app.busy and time.monotonic() < deadline:
                    root.update()
                    time.sleep(0.02)
                self.assertFalse(app.busy)
                self.assertTrue(app.start.instate(["!disabled"]))
                self.assertEqual(app.status.cget("text"), "Finished: 1 converted, 1 failed.")
                self.assertIn("Saved:", app.log.get("1.0", "end"))
                self.assertIn("Failed:", app.log.get("1.0", "end"))
            finally:
                root.destroy()
