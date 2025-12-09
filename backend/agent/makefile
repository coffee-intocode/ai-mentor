# AI Mentor Backend Makefile
# 
# Local Development Commands:
#   make build              - Install dependencies
#   make start              - Start the FastAPI app with hot reload
#   make dev                - Quick start (skip dependency check)
#   make migrate            - Run database migrations locally
#   make migrate-status     - Check migration status
#   make migrate-create     - Create new migration
#
# Docker Commands (Auto-detect environment from Terraform):
#   make build-image        - Build Docker image (auto-detects from Terraform)
#   make build-image ENV=dev - Build for specific environment
#   make build-image-push   - Build AND push to AWS ECR (both SHA and ENV tags)
#   make deploy             - Deploy to ECS (auto-detects from Terraform)
#   make deploy ENV=prod    - Deploy to specific environment
#   make show-env           - Show available environments
#   make build-image-migrate - Run migrations in Docker (requires ALEMBIC_DB_URL)
#   make up/down            - Docker Compose up/down
#
# Environment Detection:
#   By default, commands auto-detect the active environment from Terraform outputs.
#   Override with ENV=<environment> (e.g., ENV=staging, ENV=dev, ENV=prod)

MIGRATION_DIR := alembic
AWS_ACCOUNT_ID := 565551666976
AWS_DEFAULT_REGION := us-east-2
AWS_ECR_DOMAIN := $(AWS_ACCOUNT_ID).dkr.ecr.$(AWS_DEFAULT_REGION).amazonaws.com
GIT_SHA := $(shell git rev-parse HEAD)
BUILD_IMAGE := $(AWS_ECR_DOMAIN)/ai-mentor
BUILD_TAG := $(if $(BUILD_TAG),$(BUILD_TAG),latest)
DOCKERIZE_HOST := $(shell echo $(ALEMBIC_DB_URL) | cut -d "@" -f 2 | cut -d ":" -f 1)
DOCKERIZE_URL := tcp://$(if $(DOCKERIZE_HOST),$(DOCKERIZE_HOST):5432,localhost:5432)

.DEFAULT_GOAL := build

# Show current deployment environment
.PHONY: show-env
show-env:
	@cd terraform 2>/dev/null && \
		echo "Available environments:" && \
		terraform output -json active_environments 2>/dev/null | grep -o '"[^"]*"' | tr -d '"' || \
		echo "Terraform not initialized - default: staging"
	@echo ""
	@echo "Usage:"
	@echo "  make build-image          - Auto-detect from Terraform"
	@echo "  make build-image ENV=dev  - Build for specific environment"

build:
	uv sync
	uv pip install -e .

build-image:
	@if [ -n "$(ENV)" ]; then \
		./build.sh $(ENV); \
	else \
		./build.sh; \
	fi

build-image-push:
	@if [ -n "$(ENV)" ]; then \
		PUSH=true ./build.sh $(ENV); \
	else \
		PUSH=true ./build.sh; \
	fi

# Legacy targets (kept for backward compatibility)
build-image-login:
	aws ecr get-login-password --region $(AWS_DEFAULT_REGION) | docker login \
		--username AWS \
		--password-stdin \
		$(AWS_ECR_DOMAIN)

build-image-pull: build-image-login
	docker image pull $(BUILD_IMAGE):$(GIT_SHA)

build-image-migrate:
	@echo "Running migrations in Docker container..."
	@echo "Note: ALEMBIC_DB_URL must be set in your environment"
	@if [ -z "$(ALEMBIC_DB_URL)" ]; then \
		echo "ERROR: ALEMBIC_DB_URL is not set"; \
		exit 1; \
	fi
	docker container run \
		--entrypoint "dockerize" \
		--network "host" \
		--rm \
		$(BUILD_IMAGE):$(GIT_SHA) \
		-timeout 30s \
		-wait \
		$(DOCKERIZE_URL)
	docker container run \
		--entrypoint "alembic" \
		--env "ALEMBIC_DB_URL=$(ALEMBIC_DB_URL)" \
		--network "host" \
		--rm \
		$(BUILD_IMAGE):$(GIT_SHA) \
		current
	docker container run \
		--entrypoint "alembic" \
		--env "ALEMBIC_DB_URL=$(ALEMBIC_DB_URL)" \
		--network "host" \
		--rm \
		$(BUILD_IMAGE):$(GIT_SHA) \
		upgrade head

build-image-promote:
	docker image tag $(BUILD_IMAGE):$(GIT_SHA) $(BUILD_IMAGE):$(BUILD_TAG)
	docker image push $(BUILD_IMAGE):$(BUILD_TAG)

down:
	docker compose down --remove-orphans --volumes

up: down
	docker compose up --detach

deploy:
	@if [ -n "$(ENV)" ]; then \
		./deploy.sh $(ENV); \
	else \
		./deploy.sh; \
	fi

migrate:
	uv run alembic upgrade head

migrate-status:
	uv run alembic current

migrate-history:
	uv run alembic history

migrate-downgrade:
	uv run alembic downgrade -1

migrate-create:
	@read -p "Enter migration message: " msg; \
	uv run alembic revision --autogenerate -m "$$msg"

start: build
	uv run uvicorn chatbot.app:app --reload --host 0.0.0.0 --port 8080

dev:
	uv run uvicorn chatbot.app:app --reload --host 0.0.0.0 --port 8080
