$ErrorActionPreference = "Stop"
$ProjectDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$VenvDir = Join-Path $ProjectDir ".venv"

if (-not (Test-Path $VenvDir)) {
    python -m venv $VenvDir
}

$PythonExe = Join-Path $VenvDir "Scripts\python.exe"
& $PythonExe -m pip install --upgrade pip
& $PythonExe -m pip install -r (Join-Path $ProjectDir "requirements.txt")

Write-Host "Kurulum tamam. Başlatmak için: .\.venv\Scripts\python.exe main.py"
