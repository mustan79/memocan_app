$ErrorActionPreference = 'Stop'
$ProjectDir = $PSScriptRoot
$Exe = Join-Path $ProjectDir 'dist\Memocan.exe'
if (-not (Test-Path -LiteralPath $Exe)) { throw 'Run build.ps1 first.' }
$Stage = Join-Path $ProjectDir ('dist\package-' + [guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Path $Stage | Out-Null
# Explicit allowlist: never include .env, config.json, conversations or databases.
Copy-Item -LiteralPath $Exe -Destination (Join-Path $Stage 'Memocan.exe')
foreach ($Name in @('Install-Memocan.bat','install.ps1','README.md','LICENSE','.env.example')) {
    Copy-Item -LiteralPath (Join-Path $ProjectDir $Name) -Destination (Join-Path $Stage $Name)
}
$Zip = Join-Path $ProjectDir 'dist\Memocan-Windows.zip'
Compress-Archive -Path (Join-Path $Stage '*') -DestinationPath $Zip -Force
$Hash = (Get-FileHash -LiteralPath $Zip -Algorithm SHA256).Hash.ToLowerInvariant()
"$Hash  Memocan-Windows.zip" | Set-Content -LiteralPath (Join-Path $ProjectDir 'dist\SHA256SUMS.txt') -Encoding ASCII
Write-Host "Package ready: $Zip"
