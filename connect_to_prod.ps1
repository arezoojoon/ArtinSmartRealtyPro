#!/usr/bin/env pwsh
# Direct SSH connection script

$password = 'u0;74KWyoEydh5g.Q9)s'
$server = '72.62.93.116'

Write-Host "Connecting to $server..." -ForegroundColor Cyan

# Create expect-like script using PowerShell
$commands = @'
cd /opt/ArtinSmartRealty
echo "=== Container Status ==="
docker-compose ps
echo ""
echo "=== Checking Errors ==="
docker-compose logs --tail=100 backend router | grep -i error
echo ""
echo "=== Backend Health ==="
curl -s http://localhost:8000/health
echo ""
echo "=== Router Health ==="
curl -s http://localhost:8001/health
echo ""
echo "=== Database Check ==="
docker-compose exec -T db psql -U postgres -d artinrealty_db -c "SELECT COUNT(*) FROM tenants;"
'@

# Save commands to file
$commands | Out-File -FilePath "temp_ssh_commands.sh" -Encoding ASCII

Write-Host @"

برای اتصال به سرور، این دستورات را در PowerShell اجرا کنید:

`$password = 'u0;74KWyoEydh5g.Q9)s'
`$server = '72.62.93.116'

# نصب plink (اگر نصب نیست)
# choco install putty

# یا استفاده از PuTTY
plink -ssh root@`$server -pw `$password "cd /opt/ArtinSmartRealty && docker-compose ps"

# یا اتصال دستی
ssh root@`$server
# Password: u0;74KWyoEydh5g.Q9)s

"@
