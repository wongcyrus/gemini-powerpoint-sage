<#
PowerShell helper script to run the Gemini Powerpoint Sage
Equivalent to run.sh for Windows environments.
Usage:
    ./run.ps1 --pptx <path_to_pptx> [--pdf <path_to_pdf>] [other flags]
If --pdf is omitted, a PDF with the same basename in the PPTX folder is auto-detected.
Example:
    ./run.ps1 --pptx ../data/deck.pptx
    ./run.ps1 --pptx ../data/deck.pptx --pdf ../data/deck.pdf
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
    Write-Host "Usage: ./run.ps1 --pptx <path_to_pptx> [--pdf <path_to_pdf>]" -ForegroundColor Yellow
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
if (-not $pptx) {
    Write-Host "--pptx is required." -ForegroundColor Red
    exit 1
}
$pdf = $argMap['--pdf']

if (-not $pdf) {
    Write-Host "No --pdf supplied; main.py will auto-detect a matching PDF." -ForegroundColor Yellow
}

# Set Google Cloud environment variables (defaults only if not already set)
if (-not $env:GOOGLE_CLOUD_PROJECT) { $env:GOOGLE_CLOUD_PROJECT = 'langbridge-presenter' }
if (-not $env:GOOGLE_CLOUD_LOCATION) { $env:GOOGLE_CLOUD_LOCATION = 'global' }
if (-not $env:GOOGLE_GENAI_USE_VERTEXAI) { $env:GOOGLE_GENAI_USE_VERTEXAI = 'True' }

Write-Host "Starting Gemini Powerpoint Sage..." -ForegroundColor Cyan
Write-Host "Project: $($env:GOOGLE_CLOUD_PROJECT)" -ForegroundColor Cyan

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
