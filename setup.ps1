# Email Attachment Processor - Quick Setup Script
# Run this script to set up your environment

Write-Host "=" -NoNewline -ForegroundColor Cyan
Write-Host ("=" * 79) -ForegroundColor Cyan
Write-Host "Email Attachment Processor - Setup Script" -ForegroundColor Cyan  
Write-Host ("=" * 80) -ForegroundColor Cyan
Write-Host ""

# Check Python version
Write-Host "[1/5] Checking Python version..." -ForegroundColor Yellow
$pythonVersion = python --version 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "  ✓ $pythonVersion" -ForegroundColor Green
} else {
    Write-Host "  ✗ Python not found. Please install Python 3.8+." -ForegroundColor Red
    exit 1
}

# Install Python packages
Write-Host ""
Write-Host "[2/5] Installing Python packages..." -ForegroundColor Yellow
Write-Host "  This may take a few minutes..." -ForegroundColor Gray
pip install -r requirements.txt --quiet
if ($LASTEXITCODE -eq 0) {
    Write-Host "  ✓ Python packages installed" -ForegroundColor Green
} else {
    Write-Host "  ✗ Failed to install packages. Check requirements.txt" -ForegroundColor Red
    exit 1
}

# Check for Tesseract
Write-Host ""
Write-Host "[3/5] Checking for Tesseract OCR..." -ForegroundColor Yellow
$tesseractFound = $false
try {
    $tesseractVersion = tesseract --version 2>&1 | Select-Object -First 1
    Write-Host "  ✓ $tesseractVersion" -ForegroundColor Green
    $tesseractFound = $true
} catch {
    Write-Host "  ✗ Tesseract not found in PATH" -ForegroundColor Red
    Write-Host "  Download from: https://github.com/UB-Mannheim/tesseract/wiki" -ForegroundColor Yellow
}

# Check for API key
Write-Host ""
Write-Host "[4/5] Checking for Google Gemini API key..." -ForegroundColor Yellow
if ($env:GOOGLE_API_KEY) {
    $maskedKey = $env:GOOGLE_API_KEY.Substring(0, [Math]::Min(8, $env:GOOGLE_API_KEY.Length)) + "..."
    Write-Host "  ✓ GOOGLE_API_KEY set ($maskedKey)" -ForegroundColor Green
} else {
    Write-Host "  ✗ GOOGLE_API_KEY not set" -ForegroundColor Red
    Write-Host "  Get a free key from: https://makersuite.google.com/app/apikey" -ForegroundColor Yellow
    Write-Host "  Then run: `$env:GOOGLE_API_KEY = 'your-key-here'" -ForegroundColor Yellow
}

# Run dependency check
Write-Host ""
Write-Host "[5/5] Running full dependency check..." -ForegroundColor Yellow
python tests\check_dependencies.py

Write-Host ""
Write-Host ("=" * 80) -ForegroundColor Cyan
Write-Host "Setup complete!" -ForegroundColor Green
Write-Host ("=" * 80) -ForegroundColor Cyan
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "  1. If Tesseract or API key missing, install them (see messages above)" -ForegroundColor White
Write-Host "  2. Test with: python src\main.py --input `"<path>`" --test-mode --dry-run" -ForegroundColor White
Write-Host "  3. See README.md for full documentation" -ForegroundColor White
Write-Host ""
