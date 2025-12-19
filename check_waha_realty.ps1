# Script to check Waha status on Realty server
Write-Host "=== Checking Waha on Realty Server ===" -ForegroundColor Cyan

# Using Plink (PuTTY command-line) for non-interactive SSH
$server = "root@72.60.196.192"
$commands = @"
cd /opt/ArtinSmartRealty
echo "--- Container Status ---"
docker-compose ps waha
echo ""
echo "--- Extract API Key ---"
docker-compose logs waha 2>&1 | grep "WAHA_API_KEY=" | tail -1
echo ""
echo "--- Check Session ---"
API_KEY=`$(docker-compose logs waha 2>&1 | grep "WAHA_API_KEY=" | tail -1 | sed 's/.*WAHA_API_KEY=//')
if [ ! -z "`$API_KEY" ]; then
    echo "Found API Key: `$API_KEY"
    curl -s -H "X-Api-Key: `$API_KEY" http://localhost:3001/api/sessions/default | python3 -m json.tool 2>/dev/null || curl -s -H "X-Api-Key: `$API_KEY" http://localhost:3001/api/sessions/default
else
    echo "No API Key found in logs"
fi
"@

# Execute commands via SSH
Write-Host "Connecting to server..." -ForegroundColor Yellow
echo $commands | ssh -o StrictHostKeyChecking=no $server bash

Write-Host "`n=== Check Complete ===" -ForegroundColor Green
