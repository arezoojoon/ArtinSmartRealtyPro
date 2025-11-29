# Quick Debug Commands

## Check if backend is ready
```bash
# Wait for backend to be healthy
sleep 30

# Check service status
docker-compose ps

# Check backend health
docker-compose logs backend | tail -50

# Look for startup errors
docker-compose logs backend | grep -i error

# Check if app is listening
docker-compose exec backend netstat -tlnp | grep 8000
```

## Test webhook after backend is up
```bash
# Test via localhost (inside container)
docker-compose exec backend curl "http://localhost:8000/webhook/whatsapp?hub.mode=subscribe&hub.verify_token=ArtinSmartRealty2024SecureWebhookToken9876543210&hub.challenge=SUCCESS123"

# Test via nginx (external)
curl "https://realty.artinsmartagent.com/webhook/whatsapp?hub.mode=subscribe&hub.verify_token=ArtinSmartRealty2024SecureWebhookToken9876543210&hub.challenge=SUCCESS123"
```

## Common Issues

### 502 Bad Gateway
- Backend not started yet (wait 30-60s)
- Backend crashed on startup (check logs)
- Port 8000 not listening

### Check token is loaded
```bash
docker-compose exec backend python -c "import os; print(f\"TOKEN: '{os.getenv('WHATSAPP_VERIFY_TOKEN')}'\")"
```

### Force rebuild if needed
```bash
docker-compose down
docker-compose up -d --build backend
sleep 30
docker-compose ps | grep backend
```
