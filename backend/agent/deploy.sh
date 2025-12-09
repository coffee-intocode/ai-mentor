#!/bin/bash
set -euo pipefail

# Color output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Get environment from argument or detect from Terraform
if [ -n "${1:-}" ]; then
  DEPLOY_ENV="$1"
  echo -e "${BLUE}Using specified environment: ${DEPLOY_ENV}${NC}"
else
  # Detect active environments from Terraform
  if [ -d "terraform" ]; then
    ACTIVE_ENVS=$(cd terraform 2>/dev/null && terraform output -json active_environments 2>/dev/null | grep -o '"[^"]*"' | tr -d '"' | head -1 || echo "")
    if [ -n "$ACTIVE_ENVS" ]; then
      DEPLOY_ENV="$ACTIVE_ENVS"
      echo -e "${GREEN}Auto-detected environment from Terraform: ${DEPLOY_ENV}${NC}"
    else
      DEPLOY_ENV="staging"
      echo -e "${YELLOW}Terraform outputs not available, using default: ${DEPLOY_ENV}${NC}"
    fi
  else
    DEPLOY_ENV="staging"
    echo -e "${YELLOW}Terraform directory not found, using default: ${DEPLOY_ENV}${NC}"
  fi
fi

# Set ECS configuration based on environment
ECS_CLUSTER_NAME="${DEPLOY_ENV}"
ECS_SERVICE_NAME="${DEPLOY_ENV}-service"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Deploy Configuration${NC}"
echo -e "${BLUE}========================================${NC}"
echo "Environment:    ${DEPLOY_ENV}"
echo "ECS Cluster:    ${ECS_CLUSTER_NAME}"
echo "ECS Service:    ${ECS_SERVICE_NAME}"
echo -e "${BLUE}========================================${NC}"

cat > overrides.txt <<EOF
{
  "containerOverrides": [
    {
      "name": "service",
      "command": ["alembic", "upgrade", "head"]
    }
  ]
}
EOF

TASK_ARN=$(aws ecs run-task \
	--cluster "${ECS_CLUSTER_NAME}" \
	--launch-type EC2 \
	--overrides file://overrides.txt \
	--task-definition "${ECS_SERVICE_NAME}" | jq -r '.tasks[0].taskArn')

echo "Running task: ${TASK_ARN}"

aws ecs wait tasks-stopped \
    --cluster "${ECS_CLUSTER_NAME}" \
    --tasks "${TASK_ARN}"

EXIT_CODE=$(aws ecs describe-tasks \
    --cluster "${ECS_CLUSTER_NAME}" \
    --tasks "${TASK_ARN}" | jq -r '.tasks[0].containers[0].exitCode')

if [ "$EXIT_CODE" -ne 0 ]; then
    echo "Task failed with exit code: $EXIT_CODE"
    exit 1
fi

echo "Task completed successfully with exit code: $EXIT_CODE"

rm -f overrides.txt exit_code.txt

echo "Updating ECS service to use the latest task definition..."

aws ecs update-service \
  --force-new-deployment \
  --cluster "${ECS_CLUSTER_NAME}" \
  --service "${ECS_SERVICE_NAME}" | jq

echo "Waiting for ECS service to stabilize..."

aws ecs wait services-stable \
  --cluster "${ECS_CLUSTER_NAME}" \
  --services "${ECS_SERVICE_NAME}"

echo "ECS service is stable."