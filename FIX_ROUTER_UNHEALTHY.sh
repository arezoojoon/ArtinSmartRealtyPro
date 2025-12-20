#!/bin/bash
# FIX ROUTER UNHEALTHY - Add curl to router container

echo "=== FIXING ROUTER UNHEALTHY STATUS ==="
echo ""

cd /opt/ArtinSmartRealty

# Check current router status
echo "Current router status:"
docker-compose ps router
echo ""

# Check router logs for errors
echo "Router errors:"
docker-compose logs --tail=100 router | grep -i "error\|exception\|failed"
echo ""

# The fix is already in code (Dockerfile.router_v3 has curl)
# Just need to restart
echo "Restarting router..."
docker-compose restart router
echo ""

sleep 10

echo "New router status:"
docker-compose ps router
echo ""

echo "Router health:"
curl -s http://localhost:8001/health | python3 -m json.tool
echo ""

echo "If still unhealthy, check:"
echo "  docker-compose logs router"
