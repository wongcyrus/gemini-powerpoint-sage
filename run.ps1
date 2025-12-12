<#
PowerShell helper script to run the Gemini Powerpoint Sage
Updated for the new three-mode system

🌟 All Styles Processing (recommended):
    ./run.ps1 --styles
    ./run.ps1                    # defaults to --styles

🎨 Single Style Processing:
    ./run.ps1 --style-config cyberpunk
    ./run.ps1 --style-config professional
    ./run.ps1 --style-config gundam

📄 Single File Processing:
    ./run.ps1 --pptx file.pptx --language en --style Professional
    ./run.ps1 --pptx file.pptx --language "en,zh-CN" --style Cyberpunk

🔧 Other Options:
    ./run.ps1 --refine progress.json

ℹ️  All configuration is now handled through YAML files in styles/ directory
   Use --styles or --style-config for organized processing
#>

# Ensure we are running from the script's directory
Set-Location -Path $PSScriptRoot

# Activate virtual environment if it exists
if (Test-Path ".venv\Scripts\Activate.ps1") {
    Write-Host "Activating virtual environment..." -ForegroundColor Cyan
    & .\.venv\Scripts\Activate.ps1
} else {
    Write-Host "Warning: Virtual environment not found. Run .\setup.ps1 first." -ForegroundColor Yellow
    Write-Host "Continuing with system Python..." -ForegroundColor Yellow
}

# Show usage if no arguments or help requested
if ($args.Count -eq 0 -or $args[0] -eq "--help" -or $args[0] -eq "-h") {
    Write-Host "Gemini PowerPoint Sage - Three Processing Modes" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "🌟 All Styles Processing (recommended):" -ForegroundColor Green
    Write-Host "  ./run.ps1 --styles" -ForegroundColor White
    Write-Host "  ./run.ps1                    # defaults to --styles" -ForegroundColor White
    Write-Host ""
    Write-Host "🎨 Single Style Processing:" -ForegroundColor Yellow
    Write-Host "  ./run.ps1 --style-config cyberpunk" -ForegroundColor White
    Write-Host "  ./run.ps1 --style-config professional" -ForegroundColor White
    Write-Host "  ./run.ps1 --style-config gundam" -ForegroundColor White
    Write-Host ""
    Write-Host "📄 Single File Processing:" -ForegroundColor Magenta
    Write-Host "  ./run.ps1 --pptx file.pptx --language en --style Professional" -ForegroundColor White
    Write-Host "  ./run.ps1 --pptx file.pptx --language 'en,zh-CN' --style Cyberpunk" -ForegroundColor White
    Write-Host ""
    Write-Host "🔧 Other Options:" -ForegroundColor Blue
    Write-Host "  ./run.ps1 --refine progress.json" -ForegroundColor White
    Write-Host ""
    Write-Host "ℹ️  All configuration is now handled through YAML files in styles/ directory" -ForegroundColor Cyan
    Write-Host "   Use --styles or --style-config for organized processing" -ForegroundColor Cyan
    exit 1
}

# If no arguments provided, default to --styles
if ($args.Count -eq 0) {
    Write-Host "No arguments provided, defaulting to --styles mode" -ForegroundColor Cyan
    $args = @("--styles")
}

# Note: Environment variables are loaded from .env file by main.py using python-dotenv
# You can still override them here if needed:
# $env:GOOGLE_CLOUD_PROJECT = "your-project-id"
# $env:GOOGLE_CLOUD_LOCATION = "us-central1"

Write-Host "Starting Gemini Powerpoint Sage..." -ForegroundColor Cyan
if ($env:GOOGLE_CLOUD_PROJECT) {
    Write-Host "Project: $($env:GOOGLE_CLOUD_PROJECT)" -ForegroundColor Cyan
} else {
    Write-Host "Project: (will be loaded from .env file)" -ForegroundColor Cyan
}

# Forward all original arguments exactly as received

# Prefer python if available, fallback to python3
$pythonCmd = if (Get-Command python -ErrorAction SilentlyContinue) { 'python' } elseif (Get-Command python3 -ErrorAction SilentlyContinue) { 'python3' } else { $null }
if (-not $pythonCmd) {
    Write-Host "Python interpreter not found (python/python3)." -ForegroundColor Red
    exit 127
}

# Execute main.py with all arguments
& $pythonCmd 'main.py' @args
$exitCode = $LASTEXITCODE

if ($exitCode -eq 0) {
    Write-Host 'Success!' -ForegroundColor Green
} else {
    Write-Host "Failed with error code $exitCode" -ForegroundColor Red
}
exit $exitCode
