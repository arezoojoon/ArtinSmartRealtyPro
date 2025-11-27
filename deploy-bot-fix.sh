#!/bin/bash
# Deploy bot engagement fixes to server

cd /opt/ArtinSmartRealty

# Pull latest changes
git pull origin copilot/build-multi-tenant-saas-architecture

# Rebuild backend to load new code
docker compose up -d --build backend

# Show logs
echo "Waiting 5 seconds for container to start..."
sleep 5
docker compose logs backend --tail 30
