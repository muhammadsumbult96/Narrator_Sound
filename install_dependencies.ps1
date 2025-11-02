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

# Ensure critical packages are installed (force reinstall from source to avoid missing files)
Write-Host "Installing critical dependencies..." -ForegroundColor Yellow
Write-Host "Installing gruut (this may take a minute)..." -ForegroundColor Cyan
& .\venv\Scripts\pip.exe install --force-reinstall --no-cache-dir gruut==2.2.3

Write-Host "Installing jieba (this may take a minute)..." -ForegroundColor Cyan
& .\venv\Scripts\pip.exe install --force-reinstall --no-cache-dir jieba

Write-Host "Installing bnnumerizer..." -ForegroundColor Cyan
& .\venv\Scripts\pip.exe install bnnumerizer

Write-Host "Installing compatible transformers version..." -ForegroundColor Cyan
& .\venv\Scripts\pip.exe install "transformers>=4.33.0,<4.40.0"

Write-Host "Installing compatible PyTorch version (required for TTS compatibility)..." -ForegroundColor Cyan
& .\venv\Scripts\pip.exe install "torch>=2.0.0,<2.6.0" "torchaudio>=2.0.0,<2.6.0"

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

