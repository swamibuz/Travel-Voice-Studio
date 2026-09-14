# First-run setup script for BookWriting Travel Voice App (Windows / PowerShell)
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$root    = $PSScriptRoot
$backend = Join-Path $root 'backend'
$frontend = Join-Path $root 'frontend'

Write-Host "`n=== BookWriting Setup ===" -ForegroundColor Cyan

# --- .env ---
$envFile = Join-Path $backend '.env'
$envExample = Join-Path $backend '.env.example'
if (-not (Test-Path $envFile)) {
    Copy-Item $envExample $envFile
    Write-Host "[1/4] Created backend\.env from .env.example" -ForegroundColor Green
} else {
    Write-Host "[1/4] backend\.env already exists — skipped" -ForegroundColor Yellow
}

# --- Python deps ---
Write-Host "[2/4] Installing Python dependencies..." -ForegroundColor Cyan
$python = (Get-Command python -ErrorAction SilentlyContinue)?.Source
if (-not $python) { $python = (Get-Command py -ErrorAction SilentlyContinue)?.Source }
if (-not $python) { Write-Error "Python not found. Install Python 3.11+ and retry."; exit 1 }
& $python -m pip install -q -r (Join-Path $backend 'requirements.txt')
Write-Host "    Python dependencies installed." -ForegroundColor Green

# --- Pre-download Whisper model ---
Write-Host "[3/4] Pre-downloading Whisper model (small, ~250 MB)..." -ForegroundColor Cyan
& $python -c @"
import os, warnings
warnings.filterwarnings('ignore')
from faster_whisper import WhisperModel
WhisperModel('small', device='cpu', compute_type='int8')
print('    Whisper small model ready.')
"@

# --- Node deps ---
Write-Host "[4/4] Installing frontend Node.js dependencies..." -ForegroundColor Cyan
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
Push-Location $frontend
try {
    npm install --silent
    Write-Host "    Node.js dependencies installed." -ForegroundColor Green
} finally {
    Pop-Location
}

Write-Host "`n=== Setup complete! ===" -ForegroundColor Green
Write-Host ""
Write-Host "To start the app, open two terminals and run:" -ForegroundColor White
Write-Host "  Terminal 1 (backend):  cd backend ; python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000" -ForegroundColor Yellow
Write-Host "  Terminal 2 (frontend): cd frontend ; npm run dev" -ForegroundColor Yellow
Write-Host ""
Write-Host "Then open http://127.0.0.1:5175 and log in with admin / admin123" -ForegroundColor White
