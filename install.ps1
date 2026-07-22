$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$PyLauncher = Get-Command py -ErrorAction SilentlyContinue
$Python = Get-Command python -ErrorAction SilentlyContinue
if (-not $PyLauncher -and -not $Python) {
    throw "Python 3 was not found. Install Python 3 from python.org and rerun install.ps1."
}

if ($PyLauncher) {
    & $PyLauncher.Source -3 -m venv (Join-Path $Root ".venv")
} else {
    & $Python.Source -m venv (Join-Path $Root ".venv")
}
$VenvPython = Join-Path $Root ".venv\Scripts\python.exe"
& $VenvPython -m pip install --upgrade pip
& $VenvPython -m pip install -r (Join-Path $Root "requirements.txt")

Write-Host ""
Write-Host "Installed. Use:"
Write-Host "  .\image_studio.py --help"
Write-Host "  .\image_studio.py detect"
