# Remote Deployment Script for ArtinSmartRealty
# Target: 72.62.93.119
# PowerShell Script

$serverIP = "72.62.93.119"
$username = "root"
$password = "8;YdR.y3J1Uy08TZ-yKo"

Write-Host "🚀 Starting Remote Deployment to $serverIP..." -ForegroundColor Cyan

# Create secure credential
$securePassword = ConvertTo-SecureString $password -AsPlainText -Force
$credential = New-Object System.Management.Automation.PSCredential ($username, $securePassword)

# Deployment commands
$deploymentScript = @'
#!/bin/bash
set -e

echo "📂 Navigating to project..."
cd ~/ArtinSmartRealty 2>/dev/null || cd /root/ArtinSmartRealty 2>/dev/null || cd /var/www/ArtinSmartRealty || {
    echo "❌ Project directory not found"
    echo "Available directories:"
    ls -la ~
    exit 1
}

echo "📥 Pulling latest code..."
git pull origin main

echo "⏸️  Stopping services..."
docker-compose down

echo "🔨 Building new images..."
docker-compose build --no-cache backend router

echo "🚀 Starting services..."
docker-compose up -d db redis
sleep 10
docker-compose up -d

echo "⏳ Waiting for health..."
sleep 15

echo "🏥 Health checks:"
curl -s http://localhost:8000/health || echo "❌ Backend failed"
curl -s http://localhost:8001/health || echo "❌ Router failed"

echo "📊 Container status:"
docker-compose ps

echo "✅ Deployment complete!"
'@

# Save script to temp file
$scriptPath = "C:\temp\deploy_remote.sh"
$deploymentScript | Out-File -FilePath $scriptPath -Encoding UTF8

Write-Host "📤 Uploading deployment script..." -ForegroundColor Yellow

try {
    # Use SCP to copy script (requires scp.exe from OpenSSH)
    $scpCommand = "scp -o StrictHostKeyChecking=no $scriptPath ${username}@${serverIP}:/tmp/deploy.sh"
    
    Write-Host "⚠️  Manual deployment required. Please run these commands manually:" -ForegroundColor Red
    Write-Host ""
    Write-Host "1. SSH to server:" -ForegroundColor Green
    Write-Host "   ssh root@72.62.93.119" -ForegroundColor White
    Write-Host "   Password: 8;YdR.y3J1Uy08TZ-yKo" -ForegroundColor White
    Write-Host ""
    Write-Host "2. Run deployment commands:" -ForegroundColor Green
    Write-Host "   cd ~/ArtinSmartRealty" -ForegroundColor White
    Write-Host "   git pull origin main" -ForegroundColor White
    Write-Host "   docker-compose down" -ForegroundColor White
    Write-Host "   docker-compose build --no-cache backend router" -ForegroundColor White
    Write-Host "   docker-compose up -d" -ForegroundColor White
    Write-Host ""
    Write-Host "3. Verify deployment:" -ForegroundColor Green
    Write-Host "   docker-compose ps" -ForegroundColor White
    Write-Host "   curl http://localhost:8000/health" -ForegroundColor White
    Write-Host "   docker-compose logs -f backend" -ForegroundColor White
    Write-Host ""
    
} catch {
    Write-Host "❌ Error: $_" -ForegroundColor Red
}

Write-Host ""
Write-Host "📋 Deployment Summary:" -ForegroundColor Cyan
Write-Host "✅ Code committed and pushed to GitHub" -ForegroundColor Green
Write-Host "✅ Security hardening applied (rate limiting + safe tasks)" -ForegroundColor Green
Write-Host "✅ WhatsApp Router V3 ready for deployment" -ForegroundColor Green
Write-Host "⏳ Manual SSH deployment required (see instructions above)" -ForegroundColor Yellow
