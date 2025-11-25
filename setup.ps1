<#
Setup script for Gemini Powerpoint Sage (Windows)
Creates a Python virtual environment and installs dependencies
#>

Set-Location -Path $PSScriptRoot

Write-Host "========================================"  -ForegroundColor Cyan
Write-Host "Gemini Powerpoint Sage - Setup"  -ForegroundColor Cyan
Write-Host "========================================"  -ForegroundColor Cyan
Write-Host ""

# Check if Python is available
$pythonCmd = if (Get-Command python -ErrorAction SilentlyContinue) { 
    'python' 
} elseif (Get-Command python3 -ErrorAction SilentlyContinue) { 
    'python3' 
} else { 
    $null 
}

if (-not $pythonCmd) {
    Write-Host "Error: Python is not installed or not in PATH" -ForegroundColor Red
    exit 1
}

$pythonVersion = & $pythonCmd --version
Write-Host "Found Python: $pythonVersion" -ForegroundColor Green
Write-Host ""

# Check if virtual environment already exists
if (Test-Path ".venv") {
    Write-Host "Virtual environment already exists at .venv" -ForegroundColor Yellow
    $response = Read-Host "Do you want to recreate it? (y/N)"
    if ($response -eq 'y' -or $response -eq 'Y') {
        Write-Host "Removing existing virtual environment..." -ForegroundColor Yellow
        Remove-Item -Recurse -Force .venv
    } else {
        Write-Host "Using existing virtual environment." -ForegroundColor Green
    }
}

# Create virtual environment if it doesn't exist
if (-not (Test-Path ".venv")) {
    Write-Host "Creating virtual environment..." -ForegroundColor Cyan
    & $pythonCmd -m venv .venv
    Write-Host "Virtual environment created at .venv" -ForegroundColor Green
}

# Activate virtual environment
Write-Host ""
Write-Host "Activating virtual environment..." -ForegroundColor Cyan
& .\.venv\Scripts\Activate.ps1

# Upgrade pip
Write-Host ""
Write-Host "Upgrading pip..." -ForegroundColor Cyan
& python -m pip install --upgrade pip

# Install requirements
Write-Host ""
Write-Host "Installing dependencies from requirements.txt..." -ForegroundColor Cyan
& pip install -r requirements.txt

Write-Host ""
Write-Host "========================================"  -ForegroundColor Green
Write-Host "Setup completed successfully!"  -ForegroundColor Green
Write-Host "========================================"  -ForegroundColor Green
Write-Host ""
Write-Host "To use the tool:" -ForegroundColor Cyan
Write-Host "  1. Run: .\.venv\Scripts\Activate.ps1" -ForegroundColor White
Write-Host "  2. Run: .\run.ps1 --pptx <file.pptx> --pdf <file.pdf>" -ForegroundColor White
Write-Host ""
Write-Host "Or simply use .\run.ps1 which will auto-activate the venv" -ForegroundColor Cyan
Write-Host ""
