# 🚀 QUICK START - Daily Use Script
# Run this every time you want to use the extension
# For the world's laziest owner 😴

Write-Host ""
Write-Host "🤖 ========================================" -ForegroundColor Cyan
Write-Host "   ARTIN LEAD SCRAPER - QUICK START" -ForegroundColor Cyan
Write-Host "   Starting your money-making machine..." -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Kill any existing backend processes
Write-Host "🧹 Cleaning up old processes..." -ForegroundColor Yellow
Get-Process python -ErrorAction SilentlyContinue | Where-Object { $_.Path -like "*venv*" } | Stop-Process -Force 2>$null
Write-Host "   ✅ Old processes cleaned" -ForegroundColor Green

# Navigate to backend
Set-Location -Path "$PSScriptRoot\backend"

# Check if setup was run
if (!(Test-Path "venv")) {
    Write-Host ""
    Write-Host "❌ ERROR: Setup not complete!" -ForegroundColor Red
    Write-Host "   Please run SETUP.ps1 first (one-time setup)" -ForegroundColor Yellow
    Write-Host ""
    pause
    exit
}

if (!(Test-Path ".env")) {
    Write-Host ""
    Write-Host "⚠️  WARNING: No .env file found!" -ForegroundColor Yellow
    Write-Host "   Backend will start but won't generate messages without API key" -ForegroundColor Yellow
    Write-Host "   Run SETUP.ps1 to configure API key" -ForegroundColor Yellow
    Write-Host ""
}

# Start backend in new window (minimized)
Write-Host "🚀 Starting backend server..." -ForegroundColor Yellow
Write-Host "   (Opening in new minimized window)" -ForegroundColor Gray

$process = Start-Process powershell -ArgumentList `
    "-NoExit", `
    "-Command", `
    "cd '$PSScriptRoot\backend'; .\venv\Scripts\Activate.ps1; Write-Host '🌐 Backend Running - DO NOT CLOSE THIS WINDOW!' -ForegroundColor Green; python main.py" `
    -WindowStyle Minimized -PassThru

Write-Host "   ✅ Backend started (Process ID: $($process.Id))" -ForegroundColor Green

# Wait for backend to be ready
Write-Host ""
Write-Host "⏳ Waiting for backend to start (5 seconds)..." -ForegroundColor Yellow
Start-Sleep -Seconds 5

# Test backend health
Write-Host "🧪 Testing backend connection..." -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "http://localhost:8000/api/health" -Method Get -TimeoutSec 5
    Write-Host "   ✅ Backend is READY!" -ForegroundColor Green
    Write-Host ""
    Write-Host "   📊 Status: $($response.status)" -ForegroundColor Cyan
    Write-Host "   🤖 AI Model: $($response.model)" -ForegroundColor Cyan
    Write-Host "   💾 Total Leads: $($response.database.total_leads)" -ForegroundColor Cyan
    Write-Host "   📬 Messages Sent: $($response.database.messages_sent)" -ForegroundColor Cyan
    $backendRunning = $true
} catch {
    Write-Host "   ⚠️  Backend not responding!" -ForegroundColor Yellow
    Write-Host "   Error: $_" -ForegroundColor Red
    Write-Host ""
    Write-Host "   🔧 Troubleshooting:" -ForegroundColor Yellow
    Write-Host "      1. Check if API key is set in .env" -ForegroundColor White
    Write-Host "      2. Look for errors in the backend window" -ForegroundColor White
    Write-Host "      3. Try running SETUP.ps1 again" -ForegroundColor White
    $backendRunning = $false
}

Write-Host ""
Write-Host "═══════════════════════════════════════" -ForegroundColor Green
Write-Host "   ✅ READY TO USE!" -ForegroundColor Green
Write-Host "═══════════════════════════════════════" -ForegroundColor Green
Write-Host ""

if ($backendRunning) {
    Write-Host "🎯 HOW TO USE:" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "   📱 MANUAL MODE (LinkedIn Profiles):" -ForegroundColor Yellow
    Write-Host "      1. Open any LinkedIn profile" -ForegroundColor White
    Write-Host "      2. Click the purple '🤖 Generate Icebreaker' button" -ForegroundColor White
    Write-Host "      3. Get personalized message + auto-save to CRM" -ForegroundColor White
    Write-Host ""
    Write-Host "   🤖 AUTOMATION MODE (Bulk Campaigns):" -ForegroundColor Yellow
    Write-Host "      1. Click extension icon → '🤖 Automation Dashboard'" -ForegroundColor White
    Write-Host "      2. Send 10 LinkedIn messages daily (automated)" -ForegroundColor White
    Write-Host "      3. Prepare Email campaigns (bulk CSV)" -ForegroundColor White
    Write-Host "      4. Prepare WhatsApp campaigns (pre-filled links)" -ForegroundColor White
    Write-Host ""
    Write-Host "   💾 CRM MANAGER:" -ForegroundColor Yellow
    Write-Host "      • Click extension icon → 'CRM Manager'" -ForegroundColor White
    Write-Host "      • View all leads, export to Excel, manage database" -ForegroundColor White
} else {
    Write-Host "⚠️  BACKEND NOT READY" -ForegroundColor Yellow
    Write-Host "   Please fix the backend errors before using" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "🔗 Quick Links:" -ForegroundColor Cyan
Write-Host "   • Backend Status: http://localhost:8000/api/health" -ForegroundColor White
Write-Host "   • API Docs: http://localhost:8000/docs" -ForegroundColor White
Write-Host "   • Chrome Extensions: chrome://extensions/" -ForegroundColor White
Write-Host ""
Write-Host "🛑 To Stop Backend:" -ForegroundColor Cyan
Write-Host "   • Close the minimized PowerShell window" -ForegroundColor White
Write-Host "   • Or press Ctrl+C in that window" -ForegroundColor White
Write-Host ""
Write-Host "💡 Pro Tips:" -ForegroundColor Yellow
Write-Host "   • Best scraping time: 9-11 AM (less LinkedIn traffic)" -ForegroundColor White
Write-Host "   • Safe limit: 100 profiles per day" -ForegroundColor White
Write-Host "   • Backup CRM weekly: Export to Excel" -ForegroundColor White
Write-Host ""
Write-Host "🎉 Happy Lead Generating! Now go make money! 💰" -ForegroundColor Green
Write-Host ""

# Return to root directory
Set-Location -Path $PSScriptRoot

pause
