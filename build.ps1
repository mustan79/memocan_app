$ErrorActionPreference = "Stop"
$ProjectDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$PythonExe = Join-Path $ProjectDir ".venv\Scripts\python.exe"
if (-not (Test-Path $PythonExe)) { & (Join-Path $ProjectDir "setup.ps1") }
& $PythonExe -m pip install -r (Join-Path $ProjectDir "requirements-build.txt")
if ($LASTEXITCODE -ne 0) { throw "Bağımlılık kurulumu başarısız oldu: $LASTEXITCODE" }
& $PythonExe -m PyInstaller --noconfirm --clean (Join-Path $ProjectDir "Memocan.spec")
if ($LASTEXITCODE -ne 0) { throw "Paketleme başarısız oldu: $LASTEXITCODE" }
Write-Host "Paket hazır: $ProjectDir\dist\Memocan.exe"
