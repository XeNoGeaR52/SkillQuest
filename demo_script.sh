#!/bin/bash

# SkillQuest API Demo Script
# This script demonstrates the complete user flow

set -e  # Exit on error

API_URL="http://localhost:8000"
echo "SkillQuest API Demo"
echo "==================="
echo ""

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Step 1: Register a new user
echo -e "${BLUE}1. Registering a new user...${NC}"
REGISTER_RESPONSE=$(curl -s -X POST "$API_URL/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "demo_user",
    "email": "demo@example.com",
    "password": "demo123456"
  }')
echo "$REGISTER_RESPONSE" | jq '.'
USER_ID=$(echo "$REGISTER_RESPONSE" | jq -r '.id')
echo -e "${GREEN}✓ User registered with ID: $USER_ID${NC}"
echo ""

# Step 2: Login
echo -e "${BLUE}2. Logging in...${NC}"
LOGIN_RESPONSE=$(curl -s -X POST "$API_URL/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=demo_user&password=demo123456")
echo "$LOGIN_RESPONSE" | jq '.'
ACCESS_TOKEN=$(echo "$LOGIN_RESPONSE" | jq -r '.access_token')
echo -e "${GREEN}✓ Login successful, got access token${NC}"
echo ""

# Step 3: Get current user profile
echo -e "${BLUE}3. Getting user profile...${NC}"
curl -s -X GET "$API_URL/auth/me" \
  -H "Authorization: Bearer $ACCESS_TOKEN" | jq '.'
echo ""

# Step 4: List available challenges
echo -e "${BLUE}4. Listing available challenges...${NC}"
CHALLENGES_RESPONSE=$(curl -s -X GET "$API_URL/challenges?limit=5")
echo "$CHALLENGES_RESPONSE" | jq '.'
CHALLENGE_ID=$(echo "$CHALLENGES_RESPONSE" | jq -r '.[0].id')
CHALLENGE_TITLE=$(echo "$CHALLENGES_RESPONSE" | jq -r '.[0].title')
CHALLENGE_XP=$(echo "$CHALLENGES_RESPONSE" | jq -r '.[0].xp')
echo -e "${GREEN}✓ Found challenge: '$CHALLENGE_TITLE' ($CHALLENGE_XP XP)${NC}"
echo ""

# Step 5: Start an attempt
echo -e "${BLUE}5. Starting challenge attempt...${NC}"
ATTEMPT_RESPONSE=$(curl -s -X POST "$API_URL/attempts" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"challenge_id\": \"$CHALLENGE_ID\"}")
echo "$ATTEMPT_RESPONSE" | jq '.'
ATTEMPT_ID=$(echo "$ATTEMPT_RESPONSE" | jq -r '.id')
echo -e "${GREEN}✓ Attempt started with ID: $ATTEMPT_ID${NC}"
echo ""

# Step 6: Submit the attempt
echo -e "${BLUE}6. Submitting attempt with a score of 95...${NC}"
SUBMIT_RESPONSE=$(curl -s -X POST "$API_URL/attempts/$ATTEMPT_ID/submit" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "score": 95,
    "solution": "def hello_world():\n    print(\"Hello, World!\")",
    "metadata": {"language": "python"}
  }')
echo "$SUBMIT_RESPONSE" | jq '.'
echo -e "${GREEN}✓ Attempt submitted! Background worker will process XP and badges${NC}"
echo ""

# Wait for background processing
echo -e "${BLUE}Waiting 3 seconds for background worker to process...${NC}"
sleep 3
echo ""

# Step 7: Check updated user progress
echo -e "${BLUE}7. Checking user progress...${NC}"
PROGRESS_RESPONSE=$(curl -s -X GET "$API_URL/leaderboard/users/$USER_ID/progress")
echo "$PROGRESS_RESPONSE" | jq '.'
TOTAL_XP=$(echo "$PROGRESS_RESPONSE" | jq -r '.total_xp')
LEVEL=$(echo "$PROGRESS_RESPONSE" | jq -r '.level')
BADGES=$(echo "$PROGRESS_RESPONSE" | jq -r '.total_badges')
echo -e "${GREEN}✓ User now has $TOTAL_XP XP, Level $LEVEL, and $BADGES badge(s)${NC}"
echo ""

# Step 8: Check badges
echo -e "${BLUE}8. Checking earned badges...${NC}"
curl -s -X GET "$API_URL/badges/me" \
  -H "Authorization: Bearer $ACCESS_TOKEN" | jq '.'
echo ""

# Step 9: View leaderboard
echo -e "${BLUE}9. Viewing top 10 leaderboard...${NC}"
curl -s -X GET "$API_URL/leaderboard?limit=10" | jq '.'
echo ""

# Step 10: List all badges available
echo -e "${BLUE}10. Listing all available badges...${NC}"
curl -s -X GET "$API_URL/badges" | jq '.'
echo ""

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Demo completed successfully!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "Next steps:"
echo "  - Try submitting more attempts to earn more XP and badges"
echo "  - Create your own challenges via POST /challenges"
echo "  - Explore the API docs at $API_URL/docs"
