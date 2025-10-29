#!/bin/bash

# SkillQuest Demo Setup Script
# Automatically starts docker-compose, runs migrations, and seeds the database

set -e  # Exit on error

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}SkillQuest Demo Setup${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Step 1: Stop any existing containers
echo -e "${YELLOW}1. Stopping any existing containers...${NC}"
docker-compose down 2>/dev/null || true
echo -e "${GREEN}✓ Cleaned up existing containers${NC}"
echo ""

# Step 2: Start docker-compose services
echo -e "${YELLOW}2. Starting docker-compose services...${NC}"
docker-compose up -d --build
echo -e "${GREEN}✓ Docker services started${NC}"
echo ""

# Step 3: Wait for database to be ready
echo -e "${YELLOW}3. Waiting for database to be ready...${NC}"
MAX_RETRIES=30
RETRY_COUNT=0

while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    if docker-compose exec -T db pg_isready -U skillquest -d skillquest > /dev/null 2>&1; then
        echo -e "${GREEN}✓ Database is ready${NC}"
        break
    fi
    RETRY_COUNT=$((RETRY_COUNT + 1))
    echo -n "."
    sleep 1
done

if [ $RETRY_COUNT -eq $MAX_RETRIES ]; then
    echo -e "${RED}✗ Database failed to start after ${MAX_RETRIES} seconds${NC}"
    exit 1
fi
echo ""

# Step 4: Wait for web service to be ready
echo -e "${YELLOW}4. Waiting for web service to be ready...${NC}"
RETRY_COUNT=0

while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
        echo -e "${GREEN}✓ Web service is ready${NC}"
        break
    fi
    RETRY_COUNT=$((RETRY_COUNT + 1))
    echo -n "."
    sleep 1
done

if [ $RETRY_COUNT -eq $MAX_RETRIES ]; then
    echo -e "${YELLOW}⚠ Web service not responding, continuing anyway...${NC}"
fi
echo ""

# Step 5: Run database migrations
echo -e "${YELLOW}5. Running database migrations...${NC}"
docker-compose exec -T web alembic upgrade head
echo -e "${GREEN}✓ Migrations completed${NC}"
echo ""

# Step 6: Seed the database with sample data
echo -e "${YELLOW}6. Seeding database with sample data...${NC}"
docker-compose exec -T web python -m scripts.seed_data
echo -e "${GREEN}✓ Database seeded${NC}"
echo ""

# Display summary
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Setup completed successfully!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "${BLUE}Services running:${NC}"
echo "  • Web API: http://localhost:8000"
echo "  • API Docs: http://localhost:8000/docs"
echo "  • PostgreSQL: localhost:5432"
echo "  • Redis: localhost:6379"
echo ""
echo -e "${BLUE}Sample user credentials:${NC}"
echo "  • Username: alice   | Password: password123"
echo "  • Username: bob     | Password: password123"
echo "  • Username: charlie | Password: password123"
echo ""
echo -e "${BLUE}Next steps:${NC}"
echo "  • View logs: docker-compose logs -f"
echo "  • Stop services: docker-compose down"
echo "  • Run API demo: ./demo_script.sh"
echo "  • Access API docs: http://localhost:8000/docs"
echo ""
