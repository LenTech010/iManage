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
    export $(grep -v '^#' .env | xargs)
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
for i in {1..30}; do
    if curl -s http://localhost:8000 > /dev/null 2>&1; then
        echo -e "${GREEN}✓ Backend is ready!${NC}"
        break
    fi
    if [ $i -eq 30 ]; then
        echo -e "${YELLOW}! Backend might still be starting. Check logs with: $DOCKER_COMPOSE_CMD logs backend${NC}"
    fi
    sleep 2
done

# Display status
echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  Services are up and running!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "${GREEN}Backend (Django):${NC}   http://localhost:8000"
echo -e "${GREEN}Frontend (Node.js):${NC} http://localhost:3000"
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
echo -e "${GREEN}========================================${NC}"
