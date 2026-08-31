$ErrorActionPreference = "Stop"
$ProjectDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$SourceExe = Join-Path $ProjectDir "dist\Memocan.exe"
$PortableExe = Join-Path $ProjectDir "Memocan.exe"
if ((-not (Test-Path -LiteralPath $SourceExe)) -and (Test-Path -LiteralPath $PortableExe)) { $SourceExe = $PortableExe }
if (-not (Test-Path -LiteralPath $SourceExe)) {
    & (Join-Path $ProjectDir "build.ps1")
    $SourceExe = Join-Path $ProjectDir "dist\Memocan.exe"
}

$InstallDir = Join-Path $env:LOCALAPPDATA "Memocan"
$ConfigDir = Join-Path $env:APPDATA "Memocan"
$InstalledExe = Join-Path $InstallDir "Memocan.exe"
New-Item -ItemType Directory -Path $InstallDir -Force | Out-Null
New-Item -ItemType Directory -Path $ConfigDir -Force | Out-Null
Copy-Item -LiteralPath $SourceExe -Destination $InstalledExe -Force

$ProjectEnv = Join-Path $ProjectDir ".env"
if (Test-Path -LiteralPath $ProjectEnv) {
    Copy-Item -LiteralPath $ProjectEnv -Destination (Join-Path $ConfigDir ".env") -Force
}

$Shell = New-Object -ComObject WScript.Shell
$Desktop = [Environment]::GetFolderPath("Desktop")
$StartMenu = Join-Path $env:APPDATA "Microsoft\Windows\Start Menu\Programs"
foreach ($ShortcutPath in @((Join-Path $Desktop "Memocan.lnk"), (Join-Path $StartMenu "Memocan.lnk"))) {
    $Shortcut = $Shell.CreateShortcut($ShortcutPath)
    $Shortcut.TargetPath = $InstalledExe
    $Shortcut.WorkingDirectory = $InstallDir
    $Shortcut.Description = "Memocan erişilebilir masaüstü asistanı"
    $Shortcut.Save()
}

$RunKey = "HKCU:\Software\Microsoft\Windows\CurrentVersion\Run"
New-Item -Path $RunKey -Force | Out-Null
Set-ItemProperty -Path $RunKey -Name "Memocan" -Value ('"' + $InstalledExe + '"')

$ConfigPath = Join-Path $ConfigDir "config.json"
if (Test-Path -LiteralPath $ConfigPath) {
    $Config = Get-Content -LiteralPath $ConfigPath -Raw -Encoding UTF8 | ConvertFrom-Json
    $Config.startup_enabled = $true
    $Config | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $ConfigPath -Encoding UTF8
}

Start-Process -FilePath $InstalledExe
Write-Host "Memocan kuruldu ve başlatıldı: $InstalledExe"
Write-Host "Masaüstü ve Başlat menüsü kısayolları oluşturuldu; oturum açılışında otomatik başlayacak."
