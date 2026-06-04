"""Transcriptiq desktop GUI (tkinter).

A small cross-platform window for transcribing research audio without the
command line. Launch it with the ``transcriptiq-gui`` command (installed with
the package) or via ``python -m transcriptiq.gui``.

The same module is the entry point for the bundled desktop installers built by
PyInstaller; when frozen it looks for a bundled Whisper model next to the
executable so it works offline.
"""

from __future__ import annotations

import os
import queue
import stat
import sys
import threading
from pathlib import Path
from typing import Optional

from . import __version__
from .transcriber import AUDIO_EXTENSIONS, DEFAULT_MODEL, Transcriber

MODEL_CHOICES = [
    "tiny.en",
    "tiny",
    "base.en",
    "base",
    "small.en",
    "small",
    "medium.en",
    "medium",
    "large",
]


def _bundle_base() -> Optional[Path]:
    """Root directory of bundled resources when frozen by PyInstaller."""
    if getattr(sys, "frozen", False):
        return Path(getattr(sys, "_MEIPASS", Path(sys.executable).parent))
    return None


def bundled_models_dir() -> Optional[str]:
    """Return a bundled models directory when running as a frozen app.

    PyInstaller extracts added data to ``sys._MEIPASS``; the desktop build
    places the pre-downloaded Whisper model under ``models/`` there so Whisper
    finds it instead of downloading.
    """
    base = _bundle_base()
    if base is not None and (base / "models").is_dir():
        return str(base / "models")
    return None


def prepare_frozen_runtime() -> None:
    """Make a bundled ffmpeg discoverable when running as a frozen app.

    Whisper shells out to ``ffmpeg`` on PATH. The desktop build ships an ffmpeg
    binary at the bundle root, so we prepend that directory to PATH (and ensure
    the binary is executable on Unix) before any transcription happens.
    """
    base = _bundle_base()
    if base is None:
        return
    os.environ["PATH"] = str(base) + os.pathsep + os.environ.get("PATH", "")
    if os.name != "nt":
        ffmpeg = base / "ffmpeg"
        if ffmpeg.exists():
            try:
                ffmpeg.chmod(ffmpeg.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
            except OSError:
                pass


class TranscriptiqApp:
    """The main application window."""

    def __init__(self, root) -> None:
        import tkinter as tk
        from tkinter import ttk

        self.tk = tk
        self.ttk = ttk
        self.root = root
        self.root.title(f"Transcriptiq {__version__}")
        self.root.minsize(640, 520)

        self._inputs: list[Path] = []
        self._output_dir: Optional[Path] = None
        self._queue: "queue.Queue[tuple[str, object]]" = queue.Queue()
        self._worker: Optional[threading.Thread] = None

        self._build_ui()
        self.root.after(100, self._drain_queue)

    # -- UI construction ------------------------------------------------

    def _build_ui(self) -> None:
        tk, ttk = self.tk, self.ttk
        pad = {"padx": 8, "pady": 4}

        header = ttk.Frame(self.root)
        header.pack(fill="x", **pad)
        ttk.Label(
            header,
            text="🎙️ Transcriptiq",
            font=("Segoe UI", 16, "bold"),
        ).pack(side="left")
        ttk.Label(
            header,
            text="Audio → text for interviews, focus groups & lectures",
            foreground="#666",
        ).pack(side="left", padx=12)

        # Input selection
        inputs = ttk.LabelFrame(self.root, text="1 · Choose audio")
        inputs.pack(fill="x", **pad)
        btns = ttk.Frame(inputs)
        btns.pack(fill="x", **pad)
        ttk.Button(btns, text="Add files…", command=self._add_files).pack(side="left")
        ttk.Button(btns, text="Add folder…", command=self._add_folder).pack(
            side="left", padx=6
        )
        ttk.Button(btns, text="Clear", command=self._clear_inputs).pack(side="left")
        self.files_var = tk.StringVar(value="No files selected.")
        ttk.Label(inputs, textvariable=self.files_var, foreground="#444").pack(
            anchor="w", **pad
        )

        # Options
        opts = ttk.LabelFrame(self.root, text="2 · Options")
        opts.pack(fill="x", **pad)
        grid = ttk.Frame(opts)
        grid.pack(fill="x", **pad)

        ttk.Label(grid, text="Model:").grid(row=0, column=0, sticky="w")
        self.model_var = tk.StringVar(value=DEFAULT_MODEL)
        ttk.Combobox(
            grid,
            textvariable=self.model_var,
            values=MODEL_CHOICES,
            state="readonly",
            width=12,
        ).grid(row=0, column=1, sticky="w", padx=6)

        ttk.Label(grid, text="Language:").grid(row=0, column=2, sticky="w", padx=(16, 0))
        self.lang_var = tk.StringVar(value="")
        ttk.Entry(grid, textvariable=self.lang_var, width=8).grid(
            row=0, column=3, sticky="w", padx=6
        )
        ttk.Label(grid, text="(blank = auto)", foreground="#888").grid(
            row=0, column=4, sticky="w"
        )

        self.timestamps_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            grid, text="Include timestamps", variable=self.timestamps_var
        ).grid(row=1, column=0, columnspan=2, sticky="w", pady=(6, 0))

        outrow = ttk.Frame(opts)
        outrow.pack(fill="x", **pad)
        ttk.Button(outrow, text="Output folder…", command=self._choose_output).pack(
            side="left"
        )
        self.out_var = tk.StringVar(value="Save next to each source file")
        ttk.Label(outrow, textvariable=self.out_var, foreground="#444").pack(
            side="left", padx=8
        )

        # Action
        action = ttk.Frame(self.root)
        action.pack(fill="x", **pad)
        self.run_btn = ttk.Button(
            action, text="Transcribe", command=self._start
        )
        self.run_btn.pack(side="left")
        self.progress = ttk.Progressbar(action, mode="determinate")
        self.progress.pack(side="left", fill="x", expand=True, padx=10)

        # Log
        logframe = ttk.LabelFrame(self.root, text="Progress")
        logframe.pack(fill="both", expand=True, **pad)
        self.log = tk.Text(logframe, height=12, wrap="word", state="disabled")
        self.log.pack(fill="both", expand=True, padx=6, pady=6)

        device_note = bundled_models_dir() and " (bundled model available)" or ""
        self._append_log(
            f"Ready.{device_note} Choose audio, then click Transcribe."
        )

    # -- input handlers -------------------------------------------------

    def _add_files(self) -> None:
        from tkinter import filedialog

        patterns = " ".join(f"*{ext}" for ext in AUDIO_EXTENSIONS)
        paths = filedialog.askopenfilenames(
            title="Select audio files",
            filetypes=[("Audio/Video", patterns), ("All files", "*.*")],
        )
        for p in paths:
            path = Path(p)
            if path not in self._inputs:
                self._inputs.append(path)
        self._refresh_inputs()

    def _add_folder(self) -> None:
        from tkinter import filedialog

        folder = filedialog.askdirectory(title="Select a folder of audio")
        if folder:
            found = Transcriber.find_audio_files(folder, recursive=True)
            for path in found:
                if path not in self._inputs:
                    self._inputs.append(path)
            self._append_log(f"Added {len(found)} file(s) from {folder}")
        self._refresh_inputs()

    def _clear_inputs(self) -> None:
        self._inputs.clear()
        self._refresh_inputs()

    def _refresh_inputs(self) -> None:
        if not self._inputs:
            self.files_var.set("No files selected.")
        else:
            names = ", ".join(p.name for p in self._inputs[:3])
            extra = f" (+{len(self._inputs) - 3} more)" if len(self._inputs) > 3 else ""
            self.files_var.set(f"{len(self._inputs)} file(s): {names}{extra}")

    def _choose_output(self) -> None:
        from tkinter import filedialog

        folder = filedialog.askdirectory(title="Choose output folder")
        if folder:
            self._output_dir = Path(folder)
            self.out_var.set(str(self._output_dir))

    # -- transcription --------------------------------------------------

    def _start(self) -> None:
        if self._worker and self._worker.is_alive():
            return
        if not self._inputs:
            from tkinter import messagebox

            messagebox.showinfo("Transcriptiq", "Please add at least one audio file.")
            return

        self.run_btn.config(state="disabled")
        self.progress.config(value=0, maximum=len(self._inputs))
        files = list(self._inputs)
        model = self.model_var.get()
        language = self.lang_var.get().strip() or None
        with_timestamps = self.timestamps_var.get()
        output_dir = self._output_dir

        self._worker = threading.Thread(
            target=self._run_job,
            args=(files, model, language, with_timestamps, output_dir),
            daemon=True,
        )
        self._worker.start()

    def _run_job(self, files, model, language, with_timestamps, output_dir) -> None:
        try:
            self._post("log", f"Loading model '{model}'… (first use may download)")
            transcriber = Transcriber(
                model=model,
                device="auto",
                download_root=bundled_models_dir(),
                verbose=False,
            )
            for index, audio in enumerate(files, start=1):
                self._post("log", f"[{index}/{len(files)}] Transcribing {audio.name}…")
                result = transcriber.transcribe_file(audio, language=language)
                target = (
                    output_dir / (audio.stem + "_transcribed.txt")
                    if output_dir is not None
                    else None
                )
                if output_dir is not None:
                    output_dir.mkdir(parents=True, exist_ok=True)
                written = result.save(target, with_timestamps=with_timestamps)
                secs = result.processing_seconds or 0.0
                self._post("log", f"    ✓ {secs:.1f}s → {written}")
                self._post("progress", index)
            self._post("log", "Done.")
            self._post("done", f"Transcribed {len(files)} file(s).")
        except Exception as exc:  # report on the GUI thread
            self._post("error", str(exc))

    # -- thread-safe GUI updates ---------------------------------------

    def _post(self, kind: str, payload: object) -> None:
        self._queue.put((kind, payload))

    def _drain_queue(self) -> None:
        from tkinter import messagebox

        try:
            while True:
                kind, payload = self._queue.get_nowait()
                if kind == "log":
                    self._append_log(str(payload))
                elif kind == "progress":
                    self.progress.config(value=int(payload))  # type: ignore[arg-type]
                elif kind == "done":
                    self.run_btn.config(state="normal")
                    messagebox.showinfo("Transcriptiq", str(payload))
                elif kind == "error":
                    self.run_btn.config(state="normal")
                    self._append_log(f"ERROR: {payload}")
                    messagebox.showerror("Transcriptiq", str(payload))
        except queue.Empty:
            pass
        self.root.after(100, self._drain_queue)

    def _append_log(self, message: str) -> None:
        self.log.config(state="normal")
        self.log.insert("end", message + "\n")
        self.log.see("end")
        self.log.config(state="disabled")


def main() -> int:
    """Launch the desktop GUI."""
    try:
        import tkinter as tk
    except ImportError:  # pragma: no cover - depends on Python build
        print(
            "tkinter is not available in this Python installation. "
            "On Linux install python3-tk; on macOS/Windows use the official "
            "python.org build.",
            file=sys.stderr,
        )
        return 1

    prepare_frozen_runtime()
    root = tk.Tk()
    TranscriptiqApp(root)
    root.mainloop()
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
