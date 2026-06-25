# SPDX-License-Identifier: Apache-2.0
# Windows cp1252 / path pre-flight for the eldercouncil wheel.
# Run inside Windows Sandbox (via eldercouncil.wsb). Catches the Windows
# console-encoding class of bug locally before spending Windows CI minutes.

$ErrorActionPreference = "Stop"
$env:PYTHONIOENCODING = "cp1252"   # the trap: a cp1252 console + verdict glyphs

Write-Host "Installing Python..."
winget install -e --id Python.Python.3.12 --silent --accept-source-agreements --accept-package-agreements

$work = "$env:TEMP\ec-preflight"
New-Item -ItemType Directory -Force -Path $work | Out-Null
Copy-Item "C:\eldercouncil\dist\*.whl" $work -ErrorAction SilentlyContinue

python -m venv "$work\venv"
& "$work\venv\Scripts\python.exe" -m pip install --quiet (Get-ChildItem "$work\*.whl").FullName
$ec = "$work\venv\Scripts\eldercouncil.exe"

# These print verdict glyphs (✓ ✗ →) — must NOT raise UnicodeEncodeError under cp1252.
& $ec version
& $ec convene supply-chain --demo --question "x" --no-audit
& $ec models check
Write-Host "cp1252 pre-flight passed — no UnicodeEncodeError."
