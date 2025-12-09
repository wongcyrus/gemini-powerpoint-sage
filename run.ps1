<#
PowerShell helper script to run the Gemini Powerpoint Sage
Equivalent to run.sh for Windows environments.
Usage:
    ./run.ps1 --pptx <path_to_pptx> [--pdf <path_to_pdf>] [other flags]
    ./run.ps1 --folder <path_to_folder> [other flags]
    ./run.ps1 --config <config_file.yaml>
    ./run.ps1 --refine <progress_file.json>
If --pdf is omitted, a PDF with the same basename in the PPTX folder is auto-detected.
Examples:
    ./run.ps1 --pptx ../data/deck.pptx
    ./run.ps1 --pptx ../data/deck.pptx --pdf ../data/deck.pdf
    ./run.ps1 --folder ../data --language zh-CN
    ./run.ps1 --config config.gundam.yaml
    ./run.ps1 --refine progress.json
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

if ($args.Count -lt 2) {
    Write-Host "Usage: ./run.ps1 --pptx <path_to_pptx> [--pdf <path_to_pdf>] [other flags]" -ForegroundColor Yellow
    Write-Host "   or: ./run.ps1 --folder <path_to_folder> [--language <locale>]" -ForegroundColor Yellow
    Write-Host "   or: ./run.ps1 --config <config_file.yaml>" -ForegroundColor Yellow
    Write-Host "   or: ./run.ps1 --refine <progress_file.json>" -ForegroundColor Yellow
    Write-Host "" -ForegroundColor Yellow
    Write-Host "Examples:" -ForegroundColor Yellow
    Write-Host "  ./run.ps1 --pptx ../data/deck.pptx" -ForegroundColor Yellow
    Write-Host "  ./run.ps1 --folder ../data --language zh-CN" -ForegroundColor Yellow
    Write-Host "  ./run.ps1 --config config.gundam.yaml" -ForegroundColor Yellow
    Write-Host "  ./run.ps1 --refine progress.json" -ForegroundColor Yellow
    exit 1
}

# Flexible argument parsing supporting optional --pdf and passthrough of other flags
$argMap = @{}
for ($i = 0; $i -lt $args.Count; ) {
    $key = $args[$i]
    if ($key -notmatch '^--') { $i++; continue }
    # Boolean flags (no value)
    if ($key -in @('--skip-visuals','--retry-errors')) {
        $argMap[$key] = $true
        $i++
        continue
    }
    # Expect a value for other flags
    $valIndex = $i + 1
    if ($valIndex -ge $args.Count) { break }
    $value = $args[$valIndex]
    if ($value -match '^--') { $value = $true } # Handle missing value gracefully
    $argMap[$key] = $value
    $i += 2
}

$pptx = $argMap['--pptx']
$folder = $argMap['--folder']
$config = $argMap['--config']
$refine = $argMap['--refine']

# Validate that at least one mode is provided
if (-not $pptx -and -not $folder -and -not $config -and -not $refine) {
    Write-Host "Error: One of --pptx, --folder, --config, or --refine must be provided." -ForegroundColor Red
    exit 1
}

# Check for conflicting modes
$modeCount = 0
if ($pptx) { $modeCount++ }
if ($folder) { $modeCount++ }
if ($config) { $modeCount++ }
if ($refine) { $modeCount++ }

if ($modeCount -gt 1) {
    Write-Host "Error: Cannot use multiple modes (--pptx, --folder, --config, --refine) at the same time." -ForegroundColor Red
    exit 1
}

$pdf = $argMap['--pdf']

# Display mode-specific messages
if ($config) {
    Write-Host "Using configuration file: $config" -ForegroundColor Cyan
} elseif ($refine) {
    Write-Host "Refining progress file: $refine" -ForegroundColor Cyan
} elseif ($folder) {
    Write-Host "Processing all PPTX files in folder: $folder" -ForegroundColor Cyan
} elseif ($pptx -and -not $pdf) {
    Write-Host "No --pdf supplied; main.py will auto-detect a matching PDF." -ForegroundColor Yellow
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
