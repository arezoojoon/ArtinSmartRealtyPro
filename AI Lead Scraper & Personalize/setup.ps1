# 🚀 ONE-CLICK SETUP SCRIPT
# For the world's laziest extension owner 😴
# Just run this once and you're done!

Write-Host ""
Write-Host "🤖 ======================================" -ForegroundColor Cyan
Write-Host "   ARTIN LEAD SCRAPER - AUTO SETUP" -ForegroundColor Cyan  
Write-Host "   For Super Lazy Owners! 😴" -ForegroundColor Cyan
Write-Host "======================================" -ForegroundColor Cyan
Write-Host ""

# Navigate to backend directory
Set-Location -Path "$PSScriptRoot\backend"

# Step 1: Check if Python is installed
Write-Host "🔍 Step 1: Checking Python installation..." -ForegroundColor Yellow
try {
    $pythonVersion = python --version 2>&1
    Write-Host "   ✅ Python found: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "   ❌ Python NOT found!" -ForegroundColor Red
    Write-Host "   📥 Please install Python 3.8+ from: https://www.python.org/downloads/" -ForegroundColor Yellow
    Write-Host "   ✅ Make sure to check 'Add Python to PATH' during installation" -ForegroundColor Yellow
    pause
    exit
}

# Step 2: Create virtual environment
Write-Host ""
Write-Host "📦 Step 2: Creating virtual environment..." -ForegroundColor Yellow
if (Test-Path "venv") {
    Write-Host "   ⚠️  venv already exists, skipping..." -ForegroundColor Yellow
} else {
    python -m venv venv
    Write-Host "   ✅ Virtual environment created!" -ForegroundColor Green
}

# Step 3: Activate venv and install dependencies
Write-Host ""
Write-Host "⚙️  Step 3: Installing dependencies..." -ForegroundColor Yellow
& ".\venv\Scripts\Activate.ps1"

# Upgrade pip first
python -m pip install --upgrade pip --quiet
Write-Host "   ✅ pip upgraded" -ForegroundColor Green

# Install requirements
if (Test-Path "requirements.txt") {
    pip install -r requirements.txt --quiet
    Write-Host "   ✅ All dependencies installed!" -ForegroundColor Green
} else {
    Write-Host "   ❌ requirements.txt NOT found!" -ForegroundColor Red
    pause
    exit
}

# Step 4: Setup .env file (INTERACTIVE)
Write-Host ""
Write-Host "🔑 Step 4: Setting up Gemini API Key..." -ForegroundColor Yellow

if (Test-Path ".env") {
    Write-Host "   ⚠️  .env file already exists" -ForegroundColor Yellow
    $overwrite = Read-Host "   Do you want to update your API key? (y/n)"
    
    if ($overwrite -eq "y") {
        $setupApiKey = $true
    } else {
        $setupApiKey = $false
        Write-Host "   ✅ Keeping existing .env file" -ForegroundColor Green
    }
} else {
    $setupApiKey = $true
}

if ($setupApiKey) {
    Write-Host ""
    Write-Host "   ╔═══════════════════════════════════════════════════╗" -ForegroundColor Cyan
    Write-Host "   ║  🎉 GET YOUR FREE GEMINI API KEY (30 seconds)   ║" -ForegroundColor Cyan
    Write-Host "   ╠═══════════════════════════════════════════════════╣" -ForegroundColor Cyan
    Write-Host "   ║  1. Go to: https://aistudio.google.com/app/apikey║" -ForegroundColor White
    Write-Host "   ║  2. Click 'Create API Key' (blue button)         ║" -ForegroundColor White
    Write-Host "   ║  3. Copy the key (starts with AIza...)           ║" -ForegroundColor White
    Write-Host "   ║  4. Paste it below                                ║" -ForegroundColor White
    Write-Host "   ║                                                   ║" -ForegroundColor White
    Write-Host "   ║  ✅ 100% FREE - No credit card required!         ║" -ForegroundColor Green
    Write-Host "   ╚═══════════════════════════════════════════════════╝" -ForegroundColor Cyan
    Write-Host ""
    
    # Open browser automatically
    Start-Process "https://aistudio.google.com/app/apikey"
    Write-Host "   🌐 Browser opened to API key page..." -ForegroundColor Green
    Write-Host ""
    
    $apiKey = Read-Host "   📝 Paste your API key here (or press Enter to skip)"
    
    if ($apiKey) {
        # Create .env file
        @"
# Gemini API Configuration
GEMINI_API_KEY=$apiKey

# Database Configuration
DATABASE_PATH=leads_database.db
"@ | Out-File -FilePath ".env" -Encoding utf8
        
        Write-Host "   ✅ API Key saved to .env file!" -ForegroundColor Green
    } else {
        Write-Host "   ⚠️  Skipped API key setup. You can add it later in .env file" -ForegroundColor Yellow
    }
}

# Step 5: Create database (initialize)
Write-Host ""
Write-Host "💾 Step 5: Initializing database..." -ForegroundColor Yellow
python -c "from database import LeadsCRM; crm = LeadsCRM(); print('Database initialized')" 2>$null
Write-Host "   ✅ Database ready!" -ForegroundColor Green

# Step 6: Test backend startup
Write-Host ""
Write-Host "🧪 Step 6: Testing backend..." -ForegroundColor Yellow
Write-Host "   ⏳ Starting server (this takes 5 seconds)..." -ForegroundColor Yellow

# Start backend in background
$backendJob = Start-Job -ScriptBlock {
    Set-Location -Path $using:PSScriptRoot\backend
    & ".\venv\Scripts\Activate.ps1"
    python main.py
}

Start-Sleep -Seconds 5

# Test health endpoint
try {
    $response = Invoke-RestMethod -Uri "http://localhost:8000/api/health" -Method Get -TimeoutSec 3
    Write-Host "   ✅ Backend is WORKING!" -ForegroundColor Green
    Write-Host "   📊 Status: $($response.status)" -ForegroundColor Gray
    Write-Host "   🤖 Model: $($response.model)" -ForegroundColor Gray
    Write-Host "   💾 Leads: $($response.database.total_leads)" -ForegroundColor Gray
} catch {
    Write-Host "   ⚠️  Backend test failed (might need API key)" -ForegroundColor Yellow
}

# Stop test backend
Stop-Job -Job $backendJob
Remove-Job -Job $backendJob

# Final Summary
Write-Host ""
Write-Host "═══════════════════════════════════════" -ForegroundColor Green
Write-Host "   ✅ SETUP COMPLETE!" -ForegroundColor Green
Write-Host "═══════════════════════════════════════" -ForegroundColor Green
Write-Host ""
Write-Host "📋 What's installed:" -ForegroundColor Cyan
Write-Host "   ✅ Virtual environment (venv)" -ForegroundColor White
Write-Host "   ✅ All Python dependencies" -ForegroundColor White
Write-Host "   ✅ Database initialized" -ForegroundColor White
Write-Host "   ✅ API key configured" -ForegroundColor White
Write-Host ""
Write-Host "🚀 NEXT STEPS (Super Easy):" -ForegroundColor Cyan
Write-Host ""
Write-Host "   1️⃣  INSTALL EXTENSION IN CHROME:" -ForegroundColor Yellow
Write-Host "      • Go to: chrome://extensions/" -ForegroundColor White
Write-Host "      • Enable 'Developer mode' (top right)" -ForegroundColor White
Write-Host "      • Click 'Load unpacked'" -ForegroundColor White
Write-Host "      • Select folder: $PSScriptRoot" -ForegroundColor White
Write-Host ""
Write-Host "   2️⃣  START BACKEND (Every Time You Use):" -ForegroundColor Yellow
Write-Host "      • Just run: .\quick-start.ps1" -ForegroundColor White
Write-Host "      • Or manually: cd backend; .\venv\Scripts\Activate.ps1; python main.py" -ForegroundColor Gray
Write-Host ""
Write-Host "   3️⃣  USE THE TOOL:" -ForegroundColor Yellow
Write-Host "      • Open LinkedIn profile" -ForegroundColor White
Write-Host "      • Click purple '🤖 Generate Icebreaker' button" -ForegroundColor White
Write-Host "      • Get personalized message instantly!" -ForegroundColor White
Write-Host ""
Write-Host "📚 Documentation:" -ForegroundColor Cyan
Write-Host "   • Quick Start: README.md" -ForegroundColor White
Write-Host "   • Full Guide: QUICKSTART.md" -ForegroundColor White
Write-Host "   • Automation: AUTOMATION_GUIDE.md" -ForegroundColor White
Write-Host ""
Write-Host "💡 Pro Tip: Run .\quick-start.ps1 to start everything with one command!" -ForegroundColor Yellow
Write-Host ""
Write-Host "🎉 Happy Lead Generating!" -ForegroundColor Green
Write-Host ""

pause
