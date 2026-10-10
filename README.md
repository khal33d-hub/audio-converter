# Audio Converter

A Windows desktop app for converting recordings and other audio files locally. Turn an M4A recording into a WAV file, convert a collection to MP3, or save lossless audio as FLAC. Select files, choose an output format and folder, and click **Convert files**.

Audio processing takes place entirely on your computer. The app has no upload service, account, telemetry, or internet requirement after installation.

## Use the desktop app

1. Extract the Windows app ZIP into a folder on your PC.
2. Keep **AudioConverter.exe** and its **_internal** folder together.
3. Double-click **AudioConverter.exe**. Python and a separate FFmpeg installation are not needed in the packaged version.
4. Click **Add audio files** and select one or more recordings.
5. Choose the output format, optionally change the sample rate or channels, and select a destination with **Browse**.
6. Click **Convert files**. The progress bar advances after each file. The log shows each saved file or a useful error; one failed file does not stop the remaining batch.

The default destination is `Music/Audio Converter` in your user folder. Original files are preserved. Existing names receive a numbered suffix, such as `recording (1).wav`, instead of being overwritten. Duplicate selections are ignored; **Clear list** starts a fresh selection. Let a running batch finish before closing the app.

## Supported formats

Common inputs include M4A, AAC, WAV, MP3, FLAC, OGG, Opus, WMA, AIFF, and other audio that the bundled FFmpeg build can decode. Protected/DRM files are not supported. For a file with several audio tracks, the first audio track is used; video and artwork are excluded.

| Output | Encoding | Typical use |
| --- | --- | --- |
| WAV | 16-bit PCM | Editing and broad compatibility |
| MP3 | 192 kbps | Smaller files for listening and sharing |
| M4A | AAC, 192 kbps | Compressed audio in an M4A container |
| FLAC | Lossless FLAC | Lossless storage |
| OGG | Vorbis quality 5 | Open compressed audio format |

Sample rate and channel count are preserved by default where supported by the chosen encoder. Optional rates: 16,000, 22,050, 44,100, 48,000, or 96,000 Hz. Optional channels: mono or stereo. Some codec/rate/channel combinations are unsupported and will produce an error; try 44,100 or 48,000 Hz and stereo. WAV files can be substantially larger than M4A or MP3. Converting lossy audio to WAV or FLAC does not restore information already lost.

## Run from source (optional)

Install Python 3.12 or newer from [python.org](https://www.python.org/downloads/windows/), including Tcl/Tk. Open this folder in VS Code or a terminal:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe app.py
```

`imageio-ffmpeg` supplies FFmpeg on supported platforms, including 64-bit Windows. Dependency installation requires internet access; subsequent conversions do not. You can use an existing FFmpeg executable by setting `IMAGEIO_FFMPEG_EXE` to its full path before launching.

The desktop app is the main interface. An optional developer interface remains in `converter.py`; run it with `--help` to inspect its arguments.

## Build the Windows desktop app

From an activated virtual environment on 64-bit Windows:

```powershell
python -m pip install -r requirements.txt -r requirements-build.txt
python -m PyInstaller --noconfirm --clean --windowed --onedir --name AudioConverter --collect-all imageio_ffmpeg app.py
```

Alternatively, run `./build.ps1` from that environment. The complete application is in `dist/AudioConverter/`. Zip the entire folder for transfer; copying only the executable will not work. Builds are unsigned and Windows may display a reputation warning. The build output and local environment are excluded from Git.

## Tests

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

The integration tests generate a short synthetic recording and perform real conversions. They check all output formats, M4A-to-WAV sample properties, collision handling, source preservation, invalid inputs, cleanup, and a failed CLI batch. No personal recordings are needed.

## Troubleshooting and limitations

- **Missing FFmpeg:** reinstall the requirements, or check `IMAGEIO_FFMPEG_EXE`. For the packaged app, extract the entire ZIP again.
- **No audio stream / invalid data:** the input may be damaged, protected, or contain no audio. Try another file.
- **Cannot write output:** choose a local writable folder and check free disk space. Atomic publication requires a filesystem that supports hard links, such as NTFS; FAT/exFAT and some network shares are unsupported. Convert to a local NTFS folder first, then copy the result if needed.
- **Long conversion:** progress is per file, not a percentage within the current file. Conversions run sequentially in a background thread so the window stays responsive. There is no cancel or trim feature.
- Tags and metadata are handled by FFmpeg defaults and may vary by output container. This is not a bit-perfect metadata migration tool.

## Project structure

- `app.py`: desktop interface, file selection, background worker, progress, and status log.
- `converter.py`: input validation, FFmpeg encoding, safe output naming, and optional CLI.
- `tests/test_converter.py`: real conversion and error-path tests.
- `build.ps1`: repeatable Windows build command.

## Third-party components

Uses Python/Tkinter, [imageio-ffmpeg](https://github.com/imageio/imageio-ffmpeg), [FFmpeg](https://ffmpeg.org/), and [PyInstaller](https://pyinstaller.org/). These components have their own licenses. The packaged FFmpeg executable's license and build configuration can be inspected with its `-L` and `-buildconf` flags. Consult those licenses before redistributing a bundled application.
