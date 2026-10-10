$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot
python -m pip install -r requirements.txt -r requirements-build.txt
if ($LASTEXITCODE -ne 0) { throw 'Dependency installation failed' }
python -m PyInstaller --noconfirm --clean --windowed --onedir --name AudioConverter --collect-all imageio_ffmpeg app.py
if ($LASTEXITCODE -ne 0) { throw 'Build failed' }
Write-Host 'Built dist/AudioConverter/AudioConverter.exe. Keep the entire folder together.'
