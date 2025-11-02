# PowerShell script to install all dependencies
Write-Host "Installing dependencies for Vietnamese TTS Voice Cloning..." -ForegroundColor Green

# Activate venv if it exists
if (Test-Path "venv\Scripts\Activate.ps1") {
    Write-Host "Activating virtual environment..." -ForegroundColor Yellow
    & .\venv\Scripts\Activate.ps1
}

# Install dependencies
Write-Host "Installing core dependencies..." -ForegroundColor Yellow
& .\venv\Scripts\pip.exe install -e .

# Ensure critical packages are installed
Write-Host "Installing critical dependencies..." -ForegroundColor Yellow
& .\venv\Scripts\pip.exe install --force-reinstall --no-cache-dir gruut==2.2.3
& .\venv\Scripts\pip.exe install bnnumerizer jieba

# Create bnnumerizer stub if needed
$bnnumerizerStub = @"
# Stub module for bnnumerizer
def numerize(text):
    return text
"@

$stubPath = ".\venv\Lib\site-packages\bnnumerizer.py"
if (-not (Test-Path $stubPath)) {
    Write-Host "Creating bnnumerizer stub..." -ForegroundColor Yellow
    $bnnumerizerStub | Out-File -FilePath $stubPath -Encoding utf8
}

Write-Host "Dependencies installed successfully!" -ForegroundColor Green
Write-Host "You can now run the application with: python app.py" -ForegroundColor Cyan

