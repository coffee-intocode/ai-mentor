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

# Set AWS configuration
AWS_ACCOUNT_ID="${AWS_ACCOUNT_ID:-565551666976}"
AWS_DEFAULT_REGION="${AWS_DEFAULT_REGION:-us-east-2}"
AWS_ECR_DOMAIN="${AWS_ECR_DOMAIN:-${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_DEFAULT_REGION}.amazonaws.com}"
BUILD_IMAGE="${AWS_ECR_DOMAIN}/ai-mentor"
GIT_SHA=$(git rev-parse HEAD)

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Build Configuration${NC}"
echo -e "${BLUE}========================================${NC}"
echo "Environment:    ${DEPLOY_ENV}"
echo "AWS Account:    ${AWS_ACCOUNT_ID}"
echo "AWS Region:     ${AWS_DEFAULT_REGION}"
echo "ECR Domain:     ${AWS_ECR_DOMAIN}"
echo "Image:          ${BUILD_IMAGE}"
echo "Git SHA:        ${GIT_SHA}"
echo "Tags:           ${BUILD_IMAGE}:${GIT_SHA}"
echo "                ${BUILD_IMAGE}:${DEPLOY_ENV}"
echo -e "${BLUE}========================================${NC}"

# Check if we need to push and login to ECR first
if [ "${PUSH:-false}" = "true" ]; then
  echo -e "\n${BLUE}Logging in to AWS ECR...${NC}"
  aws ecr get-login-password --region "${AWS_DEFAULT_REGION}" | docker login \
    --username AWS \
    --password-stdin \
    "${AWS_ECR_DOMAIN}"
fi

# Build multi-stage Docker image
echo -e "\n${GREEN}Building build stage...${NC}"
docker buildx build \
  --platform "linux/amd64" \
  --tag "${BUILD_IMAGE}:${GIT_SHA}-build" \
  --target "build" \
  .

# Build final image (with optional push)
if [ "${PUSH:-false}" = "true" ]; then
  echo -e "\n${GREEN}Building and pushing final image to ECR...${NC}"
else
  echo -e "\n${GREEN}Building final image...${NC}"
fi

docker buildx build \
  --cache-from "${BUILD_IMAGE}:${GIT_SHA}-build" \
  --platform "linux/amd64" \
  --tag "${BUILD_IMAGE}:${GIT_SHA}" \
  --tag "${BUILD_IMAGE}:${DEPLOY_ENV}" \
  $([ "${PUSH:-false}" = "true" ] && echo "--push") \
  .

# Success message
if [ "${PUSH:-false}" = "true" ]; then
  echo -e "\n${GREEN}✓ Build and push complete!${NC}"
  echo -e "Pushed to ECR:"
  echo -e "  - ${BUILD_IMAGE}:${GIT_SHA}"
  echo -e "  - ${BUILD_IMAGE}:${DEPLOY_ENV}"
else
  echo -e "\n${GREEN}✓ Build complete!${NC}"
  echo -e "Tagged locally as:"
  echo -e "  - ${BUILD_IMAGE}:${GIT_SHA}"
  echo -e "  - ${BUILD_IMAGE}:${DEPLOY_ENV}"
fi

