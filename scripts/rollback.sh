#!/bin/bash
set -e

# SaltBitter Deployment Rollback Script
# Rolls back to a previous deployment version

echo "========================================="
echo "  SaltBitter Rollback Script"
echo "========================================="
echo ""

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Configuration
AWS_REGION="${AWS_REGION:-us-east-1}"
ECS_CLUSTER="${ECS_CLUSTER:-saltbitter-cluster}"
BACKEND_SERVICE="${BACKEND_SERVICE:-saltbitter-backend}"
FRONTEND_SERVICE="${FRONTEND_SERVICE:-saltbitter-frontend}"

# Parse arguments
ENVIRONMENT="${1:-staging}"
ROLLBACK_TO_VERSION="${2}"

if [ -z "$ROLLBACK_TO_VERSION" ]; then
    echo -e "${RED}Error: Rollback version not specified${NC}"
    echo "Usage: $0 <environment> <version>"
    echo "Example: $0 staging v1.2.3"
    echo ""
    echo "To list available versions, run:"
    echo "  aws ecs describe-task-definition --task-definition saltbitter-backend --region $AWS_REGION"
    exit 1
fi

echo "Environment: $ENVIRONMENT"
echo "Rollback to: $ROLLBACK_TO_VERSION"
echo ""

# Confirm rollback
read -p "Are you sure you want to rollback $ENVIRONMENT to $ROLLBACK_TO_VERSION? (yes/no): " CONFIRM

if [ "$CONFIRM" != "yes" ]; then
    echo "Rollback cancelled."
    exit 0
fi

echo ""
echo -e "${YELLOW}Starting rollback process...${NC}"

# Step 1: Get current task definition
echo "Step 1: Getting current task definitions..."
CURRENT_BACKEND_TASK=$(aws ecs describe-services \
    --cluster "$ECS_CLUSTER" \
    --services "$BACKEND_SERVICE" \
    --region "$AWS_REGION" \
    --query 'services[0].taskDefinition' \
    --output text)

CURRENT_FRONTEND_TASK=$(aws ecs describe-services \
    --cluster "$ECS_CLUSTER" \
    --services "$FRONTEND_SERVICE" \
    --region "$AWS_REGION" \
    --query 'services[0].taskDefinition' \
    --output text)

echo "Current backend task: $CURRENT_BACKEND_TASK"
echo "Current frontend task: $CURRENT_FRONTEND_TASK"

# Step 2: Create snapshot of current state
echo ""
echo "Step 2: Creating snapshot of current state..."
mkdir -p .rollback-snapshots
SNAPSHOT_FILE=".rollback-snapshots/snapshot-$(date +%Y%m%d-%H%M%S).json"

cat > "$SNAPSHOT_FILE" <<EOF
{
  "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "environment": "$ENVIRONMENT",
  "before_rollback": {
    "backend_task": "$CURRENT_BACKEND_TASK",
    "frontend_task": "$CURRENT_FRONTEND_TASK"
  },
  "rollback_to_version": "$ROLLBACK_TO_VERSION"
}
EOF

echo "Snapshot saved to: $SNAPSHOT_FILE"

# Step 3: Update backend service
echo ""
echo -e "${YELLOW}Step 3: Rolling back backend service...${NC}"
aws ecs update-service \
    --cluster "$ECS_CLUSTER" \
    --service "$BACKEND_SERVICE" \
    --task-definition "saltbitter-backend:$ROLLBACK_TO_VERSION" \
    --region "$AWS_REGION" \
    --force-new-deployment

echo "Backend service update initiated"

# Step 4: Update frontend service
echo ""
echo -e "${YELLOW}Step 4: Rolling back frontend service...${NC}"
aws ecs update-service \
    --cluster "$ECS_CLUSTER" \
    --service "$FRONTEND_SERVICE" \
    --task-definition "saltbitter-frontend:$ROLLBACK_TO_VERSION" \
    --region "$AWS_REGION" \
    --force-new-deployment

echo "Frontend service update initiated"

# Step 5: Wait for services to stabilize
echo ""
echo -e "${YELLOW}Step 5: Waiting for services to stabilize...${NC}"
echo "This may take a few minutes..."

aws ecs wait services-stable \
    --cluster "$ECS_CLUSTER" \
    --services "$BACKEND_SERVICE" "$FRONTEND_SERVICE" \
    --region "$AWS_REGION"

# Step 6: Run smoke tests
echo ""
echo -e "${YELLOW}Step 6: Running smoke tests...${NC}"

# Test backend health
BACKEND_URL="https://api-$ENVIRONMENT.saltbitter.com/health"
BACKEND_HEALTH=$(curl -s -o /dev/null -w "%{http_code}" "$BACKEND_URL")

if [ "$BACKEND_HEALTH" = "200" ]; then
    echo -e "${GREEN}✓ Backend health check passed${NC}"
else
    echo -e "${RED}✗ Backend health check failed (HTTP $BACKEND_HEALTH)${NC}"
fi

# Test frontend
FRONTEND_URL="https://$ENVIRONMENT.saltbitter.com"
FRONTEND_HEALTH=$(curl -s -o /dev/null -w "%{http_code}" "$FRONTEND_URL")

if [ "$FRONTEND_HEALTH" = "200" ]; then
    echo -e "${GREEN}✓ Frontend health check passed${NC}"
else
    echo -e "${RED}✗ Frontend health check failed (HTTP $FRONTEND_HEALTH)${NC}"
fi

# Step 7: Update snapshot with results
echo ""
echo "Step 7: Updating snapshot with results..."

# Get new task definitions
NEW_BACKEND_TASK=$(aws ecs describe-services \
    --cluster "$ECS_CLUSTER" \
    --services "$BACKEND_SERVICE" \
    --region "$AWS_REGION" \
    --query 'services[0].taskDefinition' \
    --output text)

NEW_FRONTEND_TASK=$(aws ecs describe-services \
    --cluster "$ECS_CLUSTER" \
    --services "$FRONTEND_SERVICE" \
    --region "$AWS_REGION" \
    --query 'services[0].taskDefinition' \
    --output text)

cat > "$SNAPSHOT_FILE" <<EOF
{
  "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "environment": "$ENVIRONMENT",
  "before_rollback": {
    "backend_task": "$CURRENT_BACKEND_TASK",
    "frontend_task": "$CURRENT_FRONTEND_TASK"
  },
  "rollback_to_version": "$ROLLBACK_TO_VERSION",
  "after_rollback": {
    "backend_task": "$NEW_BACKEND_TASK",
    "frontend_task": "$NEW_FRONTEND_TASK"
  },
  "smoke_tests": {
    "backend_health": "$BACKEND_HEALTH",
    "frontend_health": "$FRONTEND_HEALTH"
  },
  "completed_at": "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
}
EOF

echo ""
echo "========================================="
echo -e "${GREEN}✓ Rollback completed successfully!${NC}"
echo "========================================="
echo ""
echo "Summary:"
echo "  Environment: $ENVIRONMENT"
echo "  Rolled back to: $ROLLBACK_TO_VERSION"
echo "  Backend: $NEW_BACKEND_TASK"
echo "  Frontend: $NEW_FRONTEND_TASK"
echo "  Snapshot: $SNAPSHOT_FILE"
echo ""
echo "To rollback this rollback, run:"
echo "  $0 $ENVIRONMENT <previous-version>"
