#!/bin/bash

# ============================================
# ArtinSmartRealty V2 Deployment Script
# ============================================
# Usage: ./deploy.sh [dev|prod|stop|logs|status]

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Determine docker compose command (v2 vs legacy)
if command -v docker &> /dev/null && docker compose version &> /dev/null; then
    DOCKER_COMPOSE="docker compose"
elif command -v docker-compose &> /dev/null; then
    DOCKER_COMPOSE="docker-compose"
else
    echo -e "${RED}Error: Docker Compose not found!${NC}"
    echo ""
    echo "Please install Docker and Docker Compose:"
    echo ""
    echo "# Install Docker"
    echo "curl -fsSL https://get.docker.com | sh"
    echo ""
    echo "# Docker Compose is included with Docker Engine 20.10+"
    echo "# Verify with: docker compose version"
    exit 1
fi

echo -e "${BLUE}Using: $DOCKER_COMPOSE${NC}"

echo -e "${GREEN}"
echo "╔══════════════════════════════════════════╗"
echo "║     ArtinSmartRealty V2 Deployment       ║"
echo "║     Multi-tenant Real Estate SaaS        ║"
echo "╚══════════════════════════════════════════╝"
echo -e "${NC}"

# Check environment argument
ENV=${1:-help}

# Help function
show_help() {
    echo "Usage: ./deploy.sh [command]"
    echo ""
    echo "Commands:"
    echo "  dev     Start development mode (database only)"
    echo "  prod    Start production deployment"
    echo "  stop    Stop all services"
    echo "  logs    View logs (follow mode)"
    echo "  status  Show service status"
    echo ""
    echo "Example:"
    echo "  ./deploy.sh prod    # Deploy to production"
    echo "  ./deploy.sh dev     # Start DB for local dev"
}

# Check for required files
check_requirements() {
    if [ ! -f "docker-compose.yml" ]; then
        echo -e "${RED}Error: docker-compose.yml not found!${NC}"
        exit 1
    fi

    if [ ! -f ".env" ]; then
        echo -e "${YELLOW}Warning: .env file not found. Creating from template...${NC}"
        if [ -f ".env.example" ]; then
            cp .env.example .env
            echo -e "${GREEN}Created .env from template.${NC}"
            echo -e "${YELLOW}Please edit .env with your actual values before deploying.${NC}"
            echo ""
            echo "Required configuration:"
            echo "  - DB_PASSWORD"
            echo "  - GEMINI_API_KEY"
            echo "  - JWT_SECRET"
            echo "  - PASSWORD_SALT"
            echo "  - SUPER_ADMIN_PASSWORD (change from default!)"
            exit 1
        else
            echo -e "${RED}Error: .env.example not found!${NC}"
            exit 1
        fi
    fi
}

# Validate production environment
validate_production_env() {
    echo -e "${BLUE}Validating production configuration...${NC}"
    
    # Load env vars
    source .env
    
    # Check for default/empty values
    local errors=0
    
    if [ "$DB_PASSWORD" == "change_me_to_a_secure_password" ] || [ -z "$DB_PASSWORD" ]; then
        echo -e "${RED}  ✗ DB_PASSWORD is not set or using default${NC}"
        errors=$((errors + 1))
    else
        echo -e "${GREEN}  ✓ DB_PASSWORD is set${NC}"
    fi
    
    if [ -z "$GEMINI_API_KEY" ] || [ "$GEMINI_API_KEY" == "your_gemini_api_key_here" ]; then
        echo -e "${RED}  ✗ GEMINI_API_KEY is not set${NC}"
        errors=$((errors + 1))
    else
        echo -e "${GREEN}  ✓ GEMINI_API_KEY is set${NC}"
    fi
    
    if [ -z "$JWT_SECRET" ] || [ ${#JWT_SECRET} -lt 32 ]; then
        echo -e "${RED}  ✗ JWT_SECRET is missing or too short (need 32+ chars)${NC}"
        errors=$((errors + 1))
    else
        echo -e "${GREEN}  ✓ JWT_SECRET is set${NC}"
    fi
    
    if [ "$SUPER_ADMIN_PASSWORD" == "SuperAdmin123!" ]; then
        echo -e "${YELLOW}  ⚠ SUPER_ADMIN_PASSWORD is using default (not recommended for production)${NC}"
    else
        echo -e "${GREEN}  ✓ SUPER_ADMIN_PASSWORD is changed${NC}"
    fi
    
    if [ $errors -gt 0 ]; then
        echo ""
        echo -e "${RED}Found $errors configuration error(s). Please fix before deploying.${NC}"
        exit 1
    fi
    
    echo ""
}

# Wait for service to be healthy
wait_for_service() {
    local service=$1
    local max_attempts=30
    local attempt=1
    
    echo -n "  Waiting for $service"
    while [ $attempt -le $max_attempts ]; do
        if $DOCKER_COMPOSE ps $service 2>/dev/null | grep -q "healthy\|Up"; then
            echo -e " ${GREEN}✓${NC}"
            return 0
        fi
        echo -n "."
        sleep 2
        ((attempt++))
    done
    
    echo -e " ${RED}✗ (timeout)${NC}"
    return 1
}

# Development deployment
deploy_dev() {
    echo -e "${GREEN}Starting development environment...${NC}"
    echo ""
    
    # Start only database
    $DOCKER_COMPOSE up -d db
    
    wait_for_service "db"
    
    echo ""
    echo -e "${GREEN}✅ Development database is ready!${NC}"
    echo ""
    echo "Database connection:"
    echo -e "  ${YELLOW}postgresql://postgres:\${DB_PASSWORD}@localhost:5432/artinrealty${NC}"
    echo ""
    echo "Start backend:"
    echo -e "  ${YELLOW}cd backend && pip install -r requirements.txt && uvicorn main:app --reload${NC}"
    echo ""
    echo "Start frontend:"
    echo -e "  ${YELLOW}cd frontend && npm install && npm run dev${NC}"
}

# Production deployment
deploy_prod() {
    validate_production_env
    
    echo -e "${GREEN}Starting production deployment...${NC}"
    echo ""
    
    # Build and start all services
    echo "Building containers..."
    $DOCKER_COMPOSE build --no-cache
    
    echo ""
    echo "Starting services..."
    $DOCKER_COMPOSE up -d
    
    echo ""
    echo "Waiting for services to be ready..."
    wait_for_service "db"
    wait_for_service "backend"
    wait_for_service "frontend"
    
    echo ""
    echo -e "${GREEN}╔══════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║     ✅ Production deployment complete!   ║${NC}"
    echo -e "${GREEN}╚══════════════════════════════════════════╝${NC}"
    echo ""
    echo "Access the application:"
    echo -e "  Dashboard:    ${YELLOW}http://localhost${NC}"
    echo -e "  API Docs:     ${YELLOW}http://localhost/docs${NC}"
    echo -e "  Health Check: ${YELLOW}http://localhost/health${NC}"
    echo ""
    echo "Super Admin login:"
    echo -e "  Email:    ${YELLOW}\${SUPER_ADMIN_EMAIL}${NC}"
    echo -e "  Password: ${YELLOW}(from .env)${NC}"
    echo ""
    echo "Useful commands:"
    echo -e "  View logs:    ${YELLOW}./deploy.sh logs${NC}"
    echo -e "  Stop services: ${YELLOW}./deploy.sh stop${NC}"
}

# Stop services
stop_services() {
    echo -e "${YELLOW}Stopping all services...${NC}"
    $DOCKER_COMPOSE down
    echo -e "${GREEN}✅ All services stopped.${NC}"
}

# Show logs
show_logs() {
    $DOCKER_COMPOSE logs -f
}

# Show status
show_status() {
    echo -e "${BLUE}Service Status:${NC}"
    $DOCKER_COMPOSE ps
}

# Main logic
case $ENV in
    dev)
        check_requirements
        deploy_dev
        ;;
    prod)
        check_requirements
        deploy_prod
        ;;
    stop)
        stop_services
        ;;
    logs)
        show_logs
        ;;
    status)
        show_status
        ;;
    help|*)
        show_help
        ;;
esac
