Param(
  [string]$Name = "RepApp",
  [ValidateSet('onedir','onefile')][string]$Mode = "onedir"
)

$ErrorActionPreference = 'Stop'

$repo = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $repo

$py = Join-Path $repo '.venv\Scripts\python.exe'
if (-not (Test-Path $py)) {
  Write-Host "[ERRORE] Venv non trovato: $py"
  Write-Host "Crea prima il venv e installa le dipendenze:"
  Write-Host "  python -m venv .venv"
  Write-Host "  .\.venv\Scripts\pip install -r requirements.txt"
  exit 1
}

Write-Host "[1/3] Installo PyInstaller nel venv (se manca)..."
& $py -m pip install -U pip | Out-Host
& $py -m pip install -U pyinstaller | Out-Host

$addData = @(
  "pwa;pwa",
  "src;src",
  "pwa_data;pwa_data"
)

$modeFlag = if ($Mode -eq 'onefile') { '--onefile' } else { '--onedir' }

Write-Host "[2/3] Build EXE ($Mode)..."
$cmd = @(
  '-m','PyInstaller',
  '--noconfirm',
  '--clean',
  $modeFlag,
  '--name', $Name,
  '--add-data', $addData[0],
  '--add-data', $addData[1],
  '--add-data', $addData[2],
  'app_pwa.py'
)
& $py @cmd | Out-Host

Write-Host "[3/3] Output:"
Write-Host "  dist\\$Name\\$Name.exe"
if ($Mode -eq 'onefile') {
  Write-Host "  dist\\$Name.exe"
}
Write-Host "\nAvvio:"
if ($Mode -eq 'onefile') {
  Write-Host "  .\\dist\\$Name.exe"
} else {
  Write-Host "  .\\dist\\$Name\\$Name.exe"
}
Write-Host "\nPoi apri: http://localhost:5000"
