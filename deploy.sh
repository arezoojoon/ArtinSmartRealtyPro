#!/bin/bash

# ArtinSmartRealty V2 Deployment Script
# Usage: ./deploy.sh [dev|prod]

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}🏠 ArtinSmartRealty V2 Deployment Script${NC}"
echo "=========================================="

# Check environment
ENV=${1:-dev}
echo -e "Environment: ${YELLOW}$ENV${NC}"

# Check for required files
if [ ! -f "docker-compose.yml" ]; then
    echo -e "${RED}Error: docker-compose.yml not found!${NC}"
    exit 1
fi

# Check for .env file
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}Warning: .env file not found. Creating template...${NC}"
    cat > .env << EOF
# ArtinSmartRealty Environment Configuration
DB_PASSWORD=your_secure_password_here
GEMINI_API_KEY=your_gemini_api_key_here
DEBUG=false
EOF
    echo -e "${GREEN}Created .env template. Please edit it with your values.${NC}"
    exit 1
fi

# Load environment variables
export $(cat .env | grep -v '^#' | xargs)

# Function to wait for service
wait_for_service() {
    local service=$1
    local max_attempts=30
    local attempt=1
    
    echo -e "Waiting for ${service} to be ready..."
    while [ $attempt -le $max_attempts ]; do
        if docker-compose ps $service | grep -q "healthy\|Up"; then
            echo -e "${GREEN}$service is ready!${NC}"
            return 0
        fi
        echo "Attempt $attempt/$max_attempts..."
        sleep 2
        ((attempt++))
    done
    
    echo -e "${RED}$service failed to start!${NC}"
    return 1
}

# Deploy based on environment
if [ "$ENV" == "prod" ]; then
    echo -e "${GREEN}Starting production deployment...${NC}"
    
    # Build and start services
    docker-compose -f docker-compose.yml build --no-cache
    docker-compose -f docker-compose.yml up -d
    
    # Wait for services
    wait_for_service "db"
    wait_for_service "backend"
    wait_for_service "frontend"
    
    echo ""
    echo -e "${GREEN}✅ Production deployment complete!${NC}"
    echo "=========================================="
    echo -e "Frontend: ${YELLOW}http://localhost:80${NC}"
    echo -e "Backend API: ${YELLOW}http://localhost:80/api${NC}"
    echo -e "Health Check: ${YELLOW}http://localhost:80/health${NC}"
    
else
    echo -e "${GREEN}Starting development deployment...${NC}"
    
    # Start only db for local development
    docker-compose up -d db
    
    wait_for_service "db"
    
    echo ""
    echo -e "${GREEN}✅ Development database is ready!${NC}"
    echo "=========================================="
    echo -e "Database: ${YELLOW}postgresql://postgres:postgres@localhost:5432/artinrealty${NC}"
    echo ""
    echo -e "To start backend: ${YELLOW}cd backend && pip install -r requirements.txt && uvicorn main:app --reload${NC}"
    echo -e "To start frontend: ${YELLOW}cd frontend && npm install && npm run dev${NC}"
fi

# Show logs
echo ""
echo -e "To view logs: ${YELLOW}docker-compose logs -f${NC}"
echo -e "To stop services: ${YELLOW}docker-compose down${NC}"
