"""Tkinter desktop interface. Run with python app.py."""
from pathlib import Path
import queue
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from converter import FORMATS, convert


class App:
    def __init__(self, root):
        self.root = root
        root.title("Audio Converter")
        root.geometry("780x600")
        root.minsize(620, 480)
        self.files = []
        self.events = queue.Queue()
        self.busy = False
        self.output = tk.StringVar(value=str(Path.home() / "Music" / "Audio Converter"))
        self.format = tk.StringVar(value="wav")
        self.rate = tk.StringVar(value="Keep original")
        self.channels = tk.StringVar(value="Keep original")
        frame = ttk.Frame(root, padding=24)
        frame.pack(fill="both", expand=True)
        ttk.Label(frame, text="Audio Converter", font=("Segoe UI", 22, "bold")).pack(anchor="w")
        ttk.Label(frame, text="Convert on your PC. Your recordings stay on your PC.").pack(anchor="w", pady=(4, 16))
        actions = ttk.Frame(frame)
        actions.pack(fill="x")
        self.add = ttk.Button(actions, text="Add audio files", command=self.choose_files)
        self.add.pack(side="left")
        self.clear = ttk.Button(actions, text="Clear list", command=self.clear_files)
        self.clear.pack(side="left", padx=8)
        self.listbox = tk.Listbox(frame, height=8)
        self.listbox.pack(fill="both", expand=True, pady=10)
        options = ttk.Frame(frame)
        options.pack(fill="x")
        self.combos = []
        for label, variable, values in [
            ("Output format", self.format, list(FORMATS)),
            ("Sample rate (Hz)", self.rate, ["Keep original", "16000", "22050", "44100", "48000", "96000"]),
            ("Channels", self.channels, ["Keep original", "Mono", "Stereo"]),
        ]:
            group = ttk.Frame(options)
            group.pack(side="left", padx=(0, 16))
            ttk.Label(group, text=label).pack(anchor="w")
            combo = ttk.Combobox(group, textvariable=variable, values=values, state="readonly", width=17)
            combo.pack(pady=4)
            self.combos.append(combo)
        ttk.Label(frame, text="Save to folder").pack(anchor="w", pady=(12, 2))
        folder = ttk.Frame(frame)
        folder.pack(fill="x")
        self.entry = ttk.Entry(folder, textvariable=self.output)
        self.entry.pack(side="left", fill="x", expand=True)
        self.browse = ttk.Button(folder, text="Browse", command=self.choose_folder)
        self.browse.pack(side="right", padx=(8, 0))
        self.start = ttk.Button(frame, text="Convert files", command=self.run)
        self.start.pack(anchor="w", pady=16)
        self.progress = ttk.Progressbar(frame, mode="determinate")
        self.progress.pack(fill="x")
        self.status = ttk.Label(frame, text="Ready. Existing files are never overwritten.")
        self.status.pack(anchor="w", pady=8)
        self.log = tk.Text(frame, height=5, wrap="word", state="disabled")
        self.log.pack(fill="both", expand=True)
        root.protocol("WM_DELETE_WINDOW", self.close)
        root.after(100, self.poll)

    def choose_files(self):
        for name in filedialog.askopenfilenames(title="Choose audio files", filetypes=[
            ("Audio files", "*.m4a *.wav *.mp3 *.aac *.flac *.ogg *.opus *.wma *.aiff *.aif"), ("All files", "*.*")]):
            if name not in self.files:
                self.files.append(name)
                self.listbox.insert("end", name)

    def clear_files(self):
        self.files.clear()
        self.listbox.delete(0, "end")

    def choose_folder(self):
        value = filedialog.askdirectory(title="Choose output folder")
        if value:
            self.output.set(value)

    def run(self):
        if not self.files or not self.output.get().strip():
            messagebox.showinfo("Choose files and folder", "Add audio files and choose an output folder first.")
            return
        self.busy = True
        for widget in [self.add, self.clear, self.browse, self.entry, self.start, *self.combos]:
            widget.configure(state="disabled")
        self.progress.configure(maximum=len(self.files), value=0)
        self.status.configure(text="Converting…")
        rate = None if self.rate.get() == "Keep original" else int(self.rate.get())
        channels = {"Keep original": None, "Mono": 1, "Stereo": 2}[self.channels.get()]
        threading.Thread(target=self.worker, args=(list(self.files), self.output.get(), self.format.get(), rate, channels), daemon=True).start()

    def worker(self, files, output, fmt, rate, channels):
        failed = 0
        for index, name in enumerate(files, 1):
            try:
                destination = convert(name, output, fmt, rate, channels)
                message = f"Saved: {destination}"
            except Exception as exc:
                failed += 1
                message = f"Failed: {Path(name).name}: {exc}"
            self.events.put(("progress", index, message))
        self.events.put(("done", len(files), failed))

    def poll(self):
        try:
            while True:
                kind, count, detail = self.events.get_nowait()
                if kind == "progress":
                    self.progress.configure(value=count)
                    self.log.configure(state="normal")
                    self.log.insert("end", detail + "\n")
                    self.log.see("end")
                    self.log.configure(state="disabled")
                else:
                    self.busy = False
                    self.status.configure(text=f"Finished: {count - detail} converted, {detail} failed.")
                    for widget in [self.add, self.clear, self.browse, self.entry, self.start]:
                        widget.configure(state="normal")
                    for combo in self.combos:
                        combo.configure(state="readonly")
        except queue.Empty:
            pass
        self.root.after(100, self.poll)

    def close(self):
        if self.busy:
            messagebox.showinfo("Conversion running", "Please wait for the current batch to finish before closing.")
        else:
            self.root.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    App(root)
    root.mainloop()
