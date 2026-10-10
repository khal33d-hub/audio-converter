"""Local audio conversion, shared by the desktop app and command line."""
import argparse
import os
from pathlib import Path
import subprocess
import tempfile

FORMATS = {
    "wav": ["-c:a", "pcm_s16le"],
    "mp3": ["-c:a", "libmp3lame", "-b:a", "192k"],
    "m4a": ["-c:a", "aac", "-b:a", "192k"],
    "flac": ["-c:a", "flac"],
    "ogg": ["-c:a", "libvorbis", "-q:a", "5"],
}


def ffmpeg_path():
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except (ImportError, RuntimeError) as exc:
        raise RuntimeError("FFmpeg unavailable. Run: python -m pip install -r requirements.txt") from exc


def convert(source, output_dir, fmt="wav", sample_rate=None, channels=None):
    """Convert one file; never overwrite an existing file or the source."""
    source = Path(source).expanduser().resolve()
    output_dir = Path(output_dir).expanduser().resolve()
    if not source.is_file():
        raise ValueError(f"Input file does not exist: {source}")
    if fmt not in FORMATS:
        raise ValueError(f"Unsupported output format: {fmt}")
    if sample_rate is not None and sample_rate not in (16000, 22050, 44100, 48000, 96000):
        raise ValueError("Unsupported sample rate")
    if channels not in (None, 1, 2):
        raise ValueError("Channels must be 1 or 2")
    executable = ffmpeg_path()
    output_dir.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=".audio-converter-", suffix="." + fmt, dir=output_dir)
    os.close(fd)
    temporary = Path(temporary)
    try:
        command = [executable, "-hide_banner", "-loglevel", "error", "-nostdin", "-y",
                   "-i", str(source), "-map", "0:a:0", "-vn", *FORMATS[fmt]]
        if sample_rate:
            command += ["-ar", str(sample_rate)]
        if channels:
            command += ["-ac", str(channels)]
        command += [str(temporary)]
        result = subprocess.run(command, capture_output=True, text=True, encoding="utf-8",
                                errors="replace", creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        if result.returncode:
            raise RuntimeError(result.stderr.strip() or "FFmpeg could not convert this file.")
        # Hard-link publication is atomic and refuses to replace an existing name.
        # Both files are in the same directory/filesystem.
        index = 0
        while True:
            suffix = f" ({index})" if index else ""
            destination = output_dir / f"{source.stem}{suffix}.{fmt}"
            try:
                os.link(temporary, destination)
                return destination
            except FileExistsError:
                index += 1
    finally:
        temporary.unlink(missing_ok=True)


def main():
    parser = argparse.ArgumentParser(description="Convert audio locally without overwriting files.")
    parser.add_argument("files", nargs="+", type=Path)
    parser.add_argument("-f", "--format", choices=FORMATS, default="wav")
    parser.add_argument("-o", "--output", type=Path, default=Path("converted"))
    parser.add_argument("--sample-rate", type=int, choices=[16000, 22050, 44100, 48000, 96000])
    parser.add_argument("--channels", type=int, choices=[1, 2])
    args = parser.parse_args()
    failed = 0
    for source in args.files:
        try:
            print(f"Saved: {convert(source, args.output, args.format, args.sample_rate, args.channels)}")
        except (OSError, ValueError, RuntimeError) as exc:
            failed += 1
            print(f"Failed: {source}: {exc}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
