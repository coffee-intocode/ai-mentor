# Dynamic Environment Detection

The build and deployment system now automatically detects which environments are active in Terraform.

## How It Works

1. **Terraform Outputs** - `terraform/outputs.tf` exports a list of active environments
2. **Shell Scripts** - `build.sh` and `deploy.sh` query Terraform outputs to determine the environment
3. **Makefile Wrapper** - Simple Makefile targets invoke the shell scripts
4. **Automatic Configuration** - ECS cluster names, service names, and image tags are automatically set

## Usage

### Building Images

**Build Only (Local):**

```bash
make build-image        # Auto-detects from Terraform (currently: staging)
make build-image ENV=dev
```

**Build and Push to ECR:**

```bash
make build-image-push           # Build + push both tags (SHA + environment)
make build-image-push ENV=dev
```

**Or call the script directly:**

```bash
./build.sh              # Build only, auto-detect
./build.sh staging      # Build only, explicit environment
PUSH=true ./build.sh    # Build + push, auto-detect
PUSH=true ./build.sh staging  # Build + push, explicit
```

### Deploying to ECS

**Automatic (Default):**

```bash
make deploy             # Auto-detects from Terraform
```

**Manual Override:**

```bash
make deploy ENV=staging
make deploy ENV=dev
make deploy ENV=prod
```

**Or call the script directly:**

```bash
./deploy.sh             # Auto-detect
./deploy.sh staging     # Explicit environment
```

### Check Available Environments

```bash
make show-env
```

Output:

```
Available environments:
staging

Usage:
  make build-image          - Auto-detect from Terraform
  make build-image ENV=dev  - Build for specific environment
```

## How Configuration Is Generated

The scripts automatically set:

**For Building (`build.sh`):**

- Docker image tags: `ai-mentor:abc123def` (git SHA) and `ai-mentor:staging` (environment)
- ECR domain: `{account}.dkr.ecr.{region}.amazonaws.com`
- Platform: `linux/amd64`

**For Deploying (`deploy.sh`):**

- ECS Cluster Name: `{environment}` (e.g., `staging`)
- ECS Service Name: `{environment}-service` (e.g., `staging-service`)
- Task Definition: `{environment}-service`

## Adding New Environments

When you uncomment a new environment in `terraform/main.tf`:

1. Uncomment the module (e.g., `module "dev"`)
2. Uncomment the output in `terraform/outputs.tf`:
   ```terraform
   output "active_environments" {
     value = compact([
       try(module.staging.cluster_name, ""),
       try(module.dev.cluster_name, ""),      # ← Uncomment this
     ])
   }
   ```
3. Apply Terraform: `terraform apply`
4. The Makefile will automatically detect the new environment

## Fallback Behavior

If Terraform is not initialized or outputs fail:

- Falls back to `staging` environment
- This ensures backward compatibility
