#!/usr/bin/env pwsh
# Deploy brain.py fix to production server

$serverHost = "72.62.93.116"
$serverUser = "root"
$serverPassword = "u0;74KWyoEydh5g.Q9)s"
$localFile = "i:\ArtinRealtySmartPro\ArtinSmartRealty\backend\brain.py"
$remoteFile = "/opt/ArtinSmartRealty/backend/brain.py"

Write-Host "🚀 Deploying brain.py fix to production..." -ForegroundColor Green

# 1. Upload the fixed file using scp
Write-Host "`n📤 Step 1: Uploading brain.py..." -ForegroundColor Yellow
$scpProcess = Start-Process -FilePath "scp" -ArgumentList @(
    "-o", "StrictHostKeyChecking=no",
    "$localFile",
    "${serverUser}@${serverHost}:${remoteFile}"
) -NoNewWindow -Wait -PassThru

if ($scpProcess.ExitCode -eq 0) {
    Write-Host "✅ File uploaded successfully!" -ForegroundColor Green
} else {
    Write-Host "❌ Upload failed! Exit code: $($scpProcess.ExitCode)" -ForegroundColor Red
    exit 1
}

# 2. Rebuild backend container
Write-Host "`n🔨 Step 2: Rebuilding backend container..." -ForegroundColor Yellow
$rebuildCmd = @"
cd /opt/ArtinSmartRealty && \
echo '📋 Stopping backend...' && \
docker-compose stop backend && \
echo '🔨 Rebuilding backend...' && \
docker-compose build --no-cache backend && \
echo '🚀 Starting backend...' && \
docker-compose up -d backend && \
sleep 5 && \
echo '📊 Checking status...' && \
docker-compose ps backend && \
echo '📝 Recent logs:' && \
docker-compose logs --tail=30 backend | grep -E '✅|❌|❓|Bot started|GEMINI'
"@

$sshProcess = Start-Process -FilePath "ssh" -ArgumentList @(
    "-o", "StrictHostKeyChecking=no",
    "${serverUser}@${serverHost}",
    "$rebuildCmd"
) -NoNewWindow -Wait -PassThru

if ($sshProcess.ExitCode -eq 0) {
    Write-Host "`n✅ Deployment completed successfully!" -ForegroundColor Green
} else {
    Write-Host "`n⚠️ Deployment may have issues. Check logs." -ForegroundColor Yellow
}

Write-Host "`n🧪 Test the bot now:" -ForegroundColor Cyan
Write-Host "   1. Open Telegram: @TaranteenBot" -ForegroundColor White
Write-Host "   2. Send: /start" -ForegroundColor White
Write-Host "   3. Choose: 🇮🇷 فارسی" -ForegroundColor White
Write-Host "   4. When asked for name, type: ببین من چطوری میتونم اقامت بگیرم؟" -ForegroundColor White
Write-Host "   5. Bot should answer the question then ask for name again ✅" -ForegroundColor White

Write-Host "`n📊 To view live logs, run:" -ForegroundColor Cyan
Write-Host "   ssh root@$serverHost 'cd /opt/ArtinSmartRealty && docker-compose logs -f backend'" -ForegroundColor Gray
