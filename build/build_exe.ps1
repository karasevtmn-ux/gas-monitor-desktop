# Build GASMonitor.exe on Windows using PyInstaller
# Usage:
#   powershell -ExecutionPolicy Bypass -File .\build\build_exe.ps1
#
# Requirements:
#   - Python 3.11+
#   - Run in project root (where app.py is)

$ErrorActionPreference = "Stop"

if (!(Test-Path ".\.venv\Scripts\python.exe")) {
  Write-Host "Creating venv..."
  python -m venv .venv
}

Write-Host "Activating venv..."
.\.venv\Scripts\Activate.ps1

Write-Host "Upgrading pip..."
python -m pip install --upgrade pip

Write-Host "Installing requirements..."
pip install -r requirements.txt

Write-Host "Installing PyInstaller..."
pip install pyinstaller

Write-Host "Building one-file EXE (no console)..."
pyinstaller --noconsole --onefile --name GASMonitor app.py

Write-Host ""
Write-Host "Done. EXE is here: .\dist\GASMonitor.exe"
