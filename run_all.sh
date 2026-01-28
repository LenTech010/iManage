#!/bin/bash
# SPDX-FileCopyrightText: 2025-present Tobias Kunze
# SPDX-License-Identifier: Apache-2.0

set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  iManage Docker Setup Script${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo -e "${YELLOW}Error: Docker is not installed. Please install Docker first.${NC}"
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo -e "${YELLOW}Error: Docker Compose is not installed. Please install Docker Compose first.${NC}"
    exit 1
fi

# Use docker-compose or docker compose based on availability
DOCKER_COMPOSE_CMD="docker-compose"
if ! command -v docker-compose &> /dev/null; then
    DOCKER_COMPOSE_CMD="docker compose"
fi

# Load environment variables from .env file if it exists
if [ -f .env ]; then
    echo -e "${GREEN}✓ Loading environment variables from .env file${NC}"
    # Safely load .env file
    set -a
    source .env 2>/dev/null || true
    set +a
else
    echo -e "${YELLOW}! No .env file found. Using default values.${NC}"
    echo -e "${YELLOW}  You can create a .env file to customize settings.${NC}"
fi

# Stop and remove existing containers
echo ""
echo -e "${BLUE}Stopping existing containers...${NC}"
$DOCKER_COMPOSE_CMD down 2>/dev/null || true

# Build Docker images
echo ""
echo -e "${BLUE}Building Docker images...${NC}"
$DOCKER_COMPOSE_CMD build

# Start services
echo ""
echo -e "${BLUE}Starting services...${NC}"
$DOCKER_COMPOSE_CMD up -d

# Wait for services to be ready
echo ""
echo -e "${BLUE}Waiting for services to start...${NC}"
sleep 5

# Check if backend is responding
echo -e "${BLUE}Checking backend health...${NC}"
BACKEND_READY=false
for i in {1..30}; do
    if curl -s http://localhost:3000 > /dev/null 2>&1; then
        echo -e "${GREEN}✓ Backend is ready!${NC}"
        BACKEND_READY=true
        break
    fi
    sleep 2
done

if [ "$BACKEND_READY" = false ]; then
    echo -e "${YELLOW}========================================${NC}"
    echo -e "${YELLOW}  WARNING: Backend did not start${NC}"
    echo -e "${YELLOW}========================================${NC}"
    echo ""
    echo -e "${YELLOW}The backend service did not respond within 60 seconds.${NC}"
    echo -e "${YELLOW}This may be normal if it's still starting up.${NC}"
    echo ""
    echo -e "${BLUE}Check logs with:${NC} $DOCKER_COMPOSE_CMD logs backend"
    echo ""
    echo -e "${YELLOW}Press Ctrl+C to stop, or wait for services to continue starting...${NC}"
    echo ""
fi

# Display status
echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  Services are up and running!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "${GREEN}Website (Django):${NC}    http://localhost:3000"
echo -e "${GREEN}Database (PostgreSQL):${NC} localhost:5432"
echo ""
echo -e "${BLUE}Default superuser credentials:${NC}"
echo -e "  Username: ${DJANGO_SUPERUSER_USERNAME:-admin}"
echo -e "  Password: ${DJANGO_SUPERUSER_PASSWORD:-admin}"
echo -e "  Email:    ${DJANGO_SUPERUSER_EMAIL:-admin@localhost}"
echo ""
echo -e "${BLUE}Useful commands:${NC}"
echo -e "  View logs:           $DOCKER_COMPOSE_CMD logs -f"
echo -e "  Stop services:       $DOCKER_COMPOSE_CMD down"
echo -e "  Restart services:    $DOCKER_COMPOSE_CMD restart"
echo -e "  View backend logs:   $DOCKER_COMPOSE_CMD logs -f backend"
echo -e "  View frontend logs:  $DOCKER_COMPOSE_CMD logs -f frontend"
echo -e "  Enter backend shell: $DOCKER_COMPOSE_CMD exec backend bash"
echo ""
echo -e "${YELLOW}========================================${NC}"
echo -e "${YELLOW}  📝 IMPORTANT: Development Tip${NC}"
echo -e "${YELLOW}========================================${NC}"
echo -e "${YELLOW}After making UI/UX changes to Vue files:${NC}"
echo -e "  ${GREEN}✓ DO NOT run ./run_all.sh again!${NC}"
echo -e "  ${GREEN}✓ Just save your files${NC}"
echo -e "  ${GREEN}✓ Refresh your browser (Ctrl+Shift+R)${NC}"
echo ""
echo -e "${YELLOW}Only rebuild when you change:${NC}"
echo -e "  - package.json (npm dependencies)"
echo -e "  - pyproject.toml (Python dependencies)"
echo -e "  - Dockerfiles or docker-compose.yml"
echo ""
echo -e "${BLUE}For more info, see:${NC} DEVELOPMENT_WORKFLOW.md"
echo ""
echo -e "${GREEN}========================================${NC}"
