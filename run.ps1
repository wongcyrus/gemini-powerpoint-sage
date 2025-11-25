<#
PowerShell helper script to run the Gemini Powerpoint Sage
Equivalent to run.sh for Windows environments.
Usage:
  ./run.ps1 --pptx <path_to_pptx> --pdf <path_to_pdf>
Example:
  ./run.ps1 --pptx ../data/deck.pptx --pdf ../data/deck.pdf
#>

# Ensure we are running from the script's directory
Set-Location -Path $PSScriptRoot

# Parse arguments expecting flag/value pairs: --pptx path --pdf path
if ($args.Count -lt 4) {
    Write-Host "Usage: ./run.ps1 --pptx <path_to_pptx> --pdf <path_to_pdf>" -ForegroundColor Yellow
    exit 1
}

$argMap = @{}
for ($i = 0; $i -lt $args.Count; $i += 2) {
    $key = $args[$i]
    $valIndex = $i + 1
    if ($valIndex -ge $args.Count) { break }
    $value = $args[$valIndex]
    $argMap[$key] = $value
}

$pptx = $argMap['--pptx']
$pdf  = $argMap['--pdf']

if (-not $pptx -or -not $pdf) {
    Write-Host "Missing required arguments." -ForegroundColor Red
    Write-Host "Usage: ./run.ps1 --pptx <path_to_pptx> --pdf <path_to_pdf>" -ForegroundColor Yellow
    exit 1
}

# Set Google Cloud environment variables
# Change GOOGLE_CLOUD_PROJECT to your alternate project ID to avoid rate limits
$env:GOOGLE_CLOUD_PROJECT = 'langbridge-presenter'  # Change this to your other project
$env:GOOGLE_CLOUD_LOCATION = 'global'
$env:GOOGLE_GENAI_USE_VERTEXAI = 'True'

Write-Host "Starting Gemini Powerpoint Sage..." -ForegroundColor Cyan
Write-Host "Project: $($env:GOOGLE_CLOUD_PROJECT)" -ForegroundColor Cyan

# Build the argument list to forward exactly as received
$forwardArgs = @('--pptx', $pptx, '--pdf', $pdf)

# Prefer python if available, fallback to python3
$pythonCmd = if (Get-Command python -ErrorAction SilentlyContinue) { 'python' } elseif (Get-Command python3 -ErrorAction SilentlyContinue) { 'python3' } else { $null }
if (-not $pythonCmd) {
    Write-Host "Python interpreter not found (python/python3)." -ForegroundColor Red
    exit 127
}

# Execute main.py
& $pythonCmd 'main.py' @forwardArgs
$exitCode = $LASTEXITCODE

if ($exitCode -eq 0) {
    Write-Host 'Success!' -ForegroundColor Green
} else {
    Write-Host "Failed with error code $exitCode" -ForegroundColor Red
}
exit $exitCode
