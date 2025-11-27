#!/bin/bash
# SSL Setup for ArtinSmartRealty with Docker Nginx
# This script helps setup SSL/HTTPS using certbot with Docker

DOMAIN="${1:-realty.artinsmartagent.com}"
EMAIL="${2:-hr.damroodi@gmail.com}"

echo "======================================"
echo "SSL Setup for ArtinSmartRealty"
echo "======================================"
echo "Domain: ${DOMAIN}"
echo "Email: ${EMAIL}"
echo ""

# Create directories for certbot
echo "1. Creating certbot directories..."
mkdir -p certbot/conf
mkdir -p certbot/www

# Stop nginx container to free port 80
echo ""
echo "2. Stopping nginx container temporarily..."
docker compose stop nginx

# Run certbot in standalone mode
echo ""
echo "3. Obtaining SSL certificate..."
docker run -it --rm \
  -v "$(pwd)/certbot/conf:/etc/letsencrypt" \
  -v "$(pwd)/certbot/www:/var/www/certbot" \
  -p 80:80 \
  certbot/certbot certonly \
  --standalone \
  --email "${EMAIL}" \
  --agree-tos \
  --no-eff-email \
  -d "${DOMAIN}"

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ SSL certificate obtained successfully!"
    
    # Update nginx.conf for SSL
    echo ""
    echo "4. Updating nginx configuration..."
    
    cat > nginx-ssl.conf << 'EOF'
events {
    worker_connections 1024;
}

http {
    include mime.types;
    default_type application/octet-stream;
    sendfile on;
    keepalive_timeout 65;

    # Rate limiting
    limit_req_zone $binary_remote_addr zone=api_limit:10m rate=10r/s;

    # Upstream definitions
    upstream backend {
        server backend:8000;
    }

    upstream frontend {
        server frontend:80;
    }

    # HTTP Server (Redirect to HTTPS)
    server {
        listen 80;
        server_name DOMAIN_PLACEHOLDER;

        # Certbot challenge
        location /.well-known/acme-challenge/ {
            root /var/www/certbot;
        }

        # Redirect all HTTP to HTTPS
        location / {
            return 301 https://$server_name$request_uri;
        }
    }

    # HTTPS Server
    server {
        listen 443 ssl http2;
        server_name DOMAIN_PLACEHOLDER;

        ssl_certificate /etc/letsencrypt/live/DOMAIN_PLACEHOLDER/fullchain.pem;
        ssl_certificate_key /etc/letsencrypt/live/DOMAIN_PLACEHOLDER/privkey.pem;

        # SSL configuration
        ssl_protocols TLSv1.2 TLSv1.3;
        ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256;
        ssl_prefer_server_ciphers off;

        # API routes
        location /api {
            limit_req zone=api_limit burst=20 nodelay;
            proxy_pass http://backend;
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection 'upgrade';
            proxy_set_header Host $host;
            proxy_cache_bypass $http_upgrade;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }

        # Webhook routes
        location /webhook {
            proxy_pass http://backend;
            proxy_http_version 1.1;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }

        # Health check
        location /health {
            proxy_pass http://backend;
        }

        # Frontend routes
        location / {
            proxy_pass http://frontend;
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection 'upgrade';
            proxy_set_header Host $host;
            proxy_cache_bypass $http_upgrade;
        }
    }
}
EOF

    # Replace placeholder with actual domain
    sed -i "s/DOMAIN_PLACEHOLDER/${DOMAIN}/g" nginx-ssl.conf
    
    echo ""
    echo "5. SSL configuration created: nginx-ssl.conf"
    echo ""
    echo "To enable SSL:"
    echo "  1. Backup current nginx.conf: cp nginx.conf nginx.conf.backup"
    echo "  2. Use new config: cp nginx-ssl.conf nginx.conf"
    echo "  3. Update docker-compose.yml to mount certbot volumes"
    echo "  4. Restart: docker compose up -d"
    
else
    echo ""
    echo "❌ Failed to obtain SSL certificate"
    echo ""
    echo "Troubleshooting:"
    echo "1. Make sure domain points to this server"
    echo "2. Check DNS: dig ${DOMAIN}"
    echo "3. Ensure port 80 is open"
fi

# Restart nginx
echo ""
echo "6. Restarting nginx..."
docker compose start nginx

echo ""
echo "======================================"
echo "Done!"
echo "======================================"
