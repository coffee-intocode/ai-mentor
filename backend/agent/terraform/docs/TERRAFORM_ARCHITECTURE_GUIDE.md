# Terraform Infrastructure Guide: FastAPI on AWS

## TL;DR (Quick Summary)

This Terraform code creates a complete AWS environment to run a FastAPI chatbot:

| Component    | What It Does                                              |
| ------------ | --------------------------------------------------------- |
| **Network**  | Private virtual network (VPC) with public/private subnets |
| **Database** | PostgreSQL on RDS (managed database)                      |
| **Cluster**  | ECS cluster with auto-scaling EC2 instances               |
| **Service**  | Your FastAPI app running in Docker containers             |
| **CDN**      | CloudFront for HTTPS and global distribution              |

**One command deploys everything:** `terraform apply`

---

## Table of Contents

1. [Introduction](#introduction)
2. [What is Terraform?](#what-is-terraform)
3. [Terraform Workflow](#terraform-workflow)
4. [Project File Structure](#project-file-structure)
5. [Project Overview](#project-overview)
6. [Core Concepts](#core-concepts)
7. [Architecture Breakdown](#architecture-breakdown)
8. [Module Deep Dive](#module-deep-dive)
9. [How It All Connects](#how-it-all-connects)
10. [Real-World Analogy](#real-world-analogy)

---

## Introduction

This guide explains how the Terraform infrastructure in this codebase deploys a FastAPI application to AWS. Think of it as a blueprint that automatically builds and connects all the cloud pieces needed to run your application in production.

## What is Terraform?

Imagine you're building a house. Instead of manually hammering every nail and placing every brick, you give a construction crew a detailed blueprint, and they build everything exactly as specified. Terraform is that blueprint for cloud infrastructure.

**Key Benefits:**

- **Reproducible**: Run the same code, get the same infrastructure every time
- **Version Controlled**: Track changes to your infrastructure like you track code changes
- **Declarative**: You describe _what_ you want, not _how_ to build it
- **Automated**: No clicking through AWS console dashboards

## Terraform Workflow

When you work with Terraform, you'll use three main commands:

```bash
terraform init    # 1. Download providers & modules
terraform plan    # 2. Preview what will be created/changed
terraform apply   # 3. Actually create the infrastructure
```

**What each step does:**

| Command | What Happens                                                                                                                | Analogy                                 |
| ------- | --------------------------------------------------------------------------------------------------------------------------- | --------------------------------------- |
| `init`  | Downloads AWS provider code and external modules into `.terraform/` folder. Creates `.terraform.lock.hcl` to lock versions. | Getting your tools and materials ready  |
| `plan`  | Compares your code to current state, shows what will change. Creates `terraform.tfplan` file.                               | Reviewing the blueprint before building |
| `apply` | Creates/updates/deletes AWS resources to match your code. Updates state file.                                               | Actually building the house             |

**State File**: Terraform keeps track of what it created in a "state file" (`terraform.tfstate`). This project stores it in S3 so your team can share it.

---

## Project File Structure

```
terraform/
├── providers.tf          # AWS provider configuration
├── backend.tf            # Where state file is stored (S3)
├── locals.tf             # Shared variables
├── main.tf               # Entry point - calls environment module
├── .terraform/           # Downloaded providers (git-ignored)
├── .terraform.lock.hcl   # Locked provider versions
├── terraform.tfplan      # Last plan output
│
└── module/
    ├── environment/      # Orchestrator - calls all other modules
    ├── network/          # VPC, subnets, security groups, bastion
    ├── database/         # RDS PostgreSQL
    ├── cluster/          # ECS cluster, ASG, load balancer, CDN
    └── service/          # Task definition, ECS service, secrets
```

---

## Project Overview

This project creates a complete production environment for a FastAPI chatbot application on AWS. Here's what gets built:

```
Internet → CloudFront (CDN) → Load Balancer → ECS Cluster → Docker Containers
                                                    ↓
                                                Database (RDS)
```

**What's Actually Running:**

- A **staging environment** with networking, database, container cluster, and the FastAPI service
- Everything isolated in its own private network (VPC)
- Auto-scaling instances that grow/shrink based on demand
- Secure secret management for API keys and database credentials

---

## Core Concepts

Before diving into modules, let's understand some key Terraform concepts:

### 1. Resources

The actual cloud infrastructure pieces. Like `aws_ecs_cluster` creates an ECS cluster.

```hcl
resource "aws_ecs_cluster" "this" {
  name = "staging"
}
```

### 2. Modules

Reusable packages of resources. Think of them as functions in programming - you define them once, use them many times with different inputs.

```hcl
module "network" {
  source = "../network"
  name   = "staging"
}
```

**Two types of modules in this project:**

- **Local modules** (`source = "../network"`) - Code in this repo's `module/` folder
- **External modules** (`source = "terraform-aws-modules/vpc/aws"`) - Downloaded from [Terraform Registry](https://registry.terraform.io/), community-maintained and battle-tested

### 3. Variables

Inputs to modules and resources. They make your code flexible and reusable.

```hcl
variable "name" {
  description = "Name of the environment"
  type        = string
}
```

### 4. Outputs

Values that modules expose to others. Like return values from a function.

```hcl
output "vpc_id" {
  value = module.vpc.vpc_id
}
```

### 5. Data Sources

Read existing information from AWS (not creating anything new).

```hcl
data "aws_region" "this" {}  # Gets current AWS region
```

### 6. The `for_each` Pattern

You'll see `for_each` used throughout this codebase. It creates multiple copies of a resource from a map or set:

```hcl
# This creates one launch template PER capacity provider
resource "aws_launch_template" "this" {
  for_each = { for name, config in var.capacity_providers : name => config }

  name          = "${var.name}-${each.key}"      # each.key = "spot"
  instance_type = each.value.instance_type       # each.value = { instance_type = "t3a.medium", ... }
}
```

**Why use it?** Instead of copy-pasting the same resource block multiple times, you define it once and Terraform creates as many as needed. If you later add another capacity provider, Terraform automatically creates another launch template.

**Accessing the results:** Use `resource_name[key]` syntax:

```hcl
aws_launch_template.this["spot"].id  # Gets the "spot" launch template's ID
```

---

## Architecture Breakdown

### Root Configuration Files

#### `providers.tf`

Tells Terraform which cloud provider (AWS) and version to use:

```hcl
terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}
```

**What it does:** Ensures everyone uses AWS provider version 5.x (the `~>` means "5.0 or newer, but not 6.0")

#### `backend.tf`

Stores Terraform's memory (state file) in S3:

```hcl
terraform {
  backend "s3" {
    bucket = "ai-mentor-terraform-state"
    key    = "terraform.tfstate"
    region = "us-east-2"
  }
}
```

**Why it matters:** The state file tracks what Terraform created. Storing it in S3 means your team can all work on the same infrastructure without conflicts.

#### `locals.tf`

Defines local variables:

```hcl
locals {
  bastion_ingress = ["150.221.144.4/32"]
}
```

**What it does:** Sets which IP address can SSH into the bastion server (your secure jump box for accessing private resources).

#### `main.tf`

The entry point - creates the staging environment:

```hcl
module "staging" {
  source = "./module/environment"

  bastion_ingress = local.bastion_ingress
  name            = "staging"
}
```

**What it does:** Kicks off everything by calling the environment module with the name "staging".

---

## Module Deep Dive

The infrastructure is built from 5 modular components that work together. Let's explore each:

### 1. Environment Module (`module/environment`)

**Role:** The orchestrator that brings all other modules together.

**What it creates:**

- Calls network module to build VPC
- Calls database module to create RDS
- Calls cluster module to set up ECS
- Calls service module to deploy your app

**Code breakdown:**

```hcl
module "network" {
  source = "../network"

  availability_zones = ["us-east-2a", "us-east-2b", "us-east-2c"]
  bastion_ingress    = var.bastion_ingress
  cidr               = "10.0.0.0/16"
  name               = var.name
}
```

This creates a network spread across 3 availability zones (think of these as different data centers in the same region) with IP range `10.0.0.0/16` (65,536 possible IP addresses).

```hcl
module "database" {
  source = "../database"

  security_groups = [module.network.database_security_group]
  subnets         = module.network.database_subnets
  name            = var.name
  vpc_name        = module.network.vpc_name

  depends_on = [module.network]
}
```

Notice the `depends_on`? It tells Terraform: "Don't create the database until the network exists." The database gets placed in special database subnets and uses security groups (firewalls) from the network module.

```hcl
module "cluster" {
  source = "../cluster"

  capacity_providers = {
    "spot" = {
      instance_type = "t3a.medium"
      market_type   = "spot"
    }
  }
}
```

This sets up the container cluster using **spot instances** (cheaper AWS servers that can be interrupted) of type `t3a.medium` (2 CPUs, 4GB RAM).

```hcl
module "service" {
  source = "../service"

  image_repository  = "ai-mentor"
  port              = 8080

  secrets = [
    "ANTHROPIC_API_KEY",
    "SUPABASE_DATABASE_URL",
    "ALEMBIC_DB_URL"
  ]
}
```

This deploys your FastAPI app as a container, exposing port 8080, and securely injects secrets from AWS Systems Manager Parameter Store.

---

### 2. Network Module (`module/network`)

**Role:** Creates the virtual network where everything lives.

**What it creates:**

- VPC (Virtual Private Cloud) - your isolated network
- Subnets - subdivisions of the VPC across availability zones
- NAT Gateway - allows private resources to access internet
- Security Groups - firewall rules
- Bastion Host - secure jump box for SSH access

**Key concepts:**

#### Subnets

The network is divided into different subnet types:

```hcl
locals {
  subnets = {
    "database"    = 6,  # /22 subnets (1024 IPs each)
    "elasticache" = 6,
    "intra"       = 5,  # /21 subnets (2048 IPs each)
    "private"     = 3,  # /19 subnets (8192 IPs each)
    "public"      = 5,
  }
}
```

The numbers indicate how many bits to add to the base CIDR for subnetting. Smaller numbers = more IP addresses.

**Subnet Types:**

- **Public**: Have direct internet access (for load balancers, bastion)
- **Private**: No direct internet, only through NAT gateway (for app servers)
- **Database**: Isolated for databases only
- **Elasticache**: Reserved for Redis/Memcached (though not used in this setup)
- **Intra**: Completely isolated, no internet at all

#### VPC Configuration

```hcl
module "vpc" {
  source  = "terraform-aws-modules/vpc/aws"
  version = "5.21.0"

  enable_nat_gateway     = true
  single_nat_gateway     = true
  one_nat_gateway_per_az = false
}
```

**NAT Gateway settings:**

- `single_nat_gateway = true` means only one NAT gateway for all private subnets (cheaper, but single point of failure)
- Alternative would be `one_nat_gateway_per_az = true` for high availability (more expensive)

#### Security Groups

Think of security groups as bouncers at a club - they control who can get in and out:

```hcl
module "security_group_private" {
  source = "terraform-aws-modules/security-group/aws"

  ingress_with_self = [{
    rule = "all-all"
  }]

  egress_with_cidr_blocks = [{
    rule = "all-all"
  }]
}
```

**What this means:**

- **Ingress (incoming)**: Resources in this security group can talk to each other freely
- **Egress (outgoing)**: Can send traffic anywhere

**Database access rules:**

```hcl
resource "aws_vpc_security_group_ingress_rule" "db_allow_private" {
  from_port                    = 5432
  to_port                      = 5432
  referenced_security_group_id = module.security_group_private.security_group_id
  security_group_id            = module.security_group_db.security_group_id
}
```

This creates a rule: "Allow traffic from the private security group to the database security group on port 5432 (PostgreSQL)."

#### Bastion Host

```hcl
module "bastion" {
  source = "terraform-aws-modules/ec2-instance/aws"

  associate_public_ip_address = true
  instance_type               = "t3a.micro"
  subnet_id                   = module.vpc.public_subnets[0]

  vpc_security_group_ids = [
    module.security_group_bastion.security_group_id,
    module.security_group_private.security_group_id,
  ]
}
```

**What's a bastion?** A small server in the public subnet that you SSH into, then from there you can access private resources (like the database or app servers). It's like a security checkpoint.

**Why two security groups?**

- Bastion group allows SSH from your IP
- Private group lets it talk to private resources

**SSH Key management:**

```hcl
resource "tls_private_key" "bastion" {
  algorithm = "RSA"
  rsa_bits  = 4096
}

module "bastion-private-key" {
  source = "terraform-aws-modules/ssm-parameter/aws"

  name        = "/staging/bastion/private-key"
  secure_type = true
  value       = tls_private_key.bastion.private_key_pem
}
```

Terraform generates an SSH key pair and stores the private key securely in AWS Systems Manager Parameter Store. You can retrieve it later to SSH in.

---

### 3. Database Module (`module/database`)

**Role:** Creates a managed PostgreSQL database.

**What it creates:**

- RDS PostgreSQL instance
- Random password
- Secure storage of credentials

**Code breakdown:**

```hcl
resource "random_string" "password" {
  length  = 32
  special = false
}

resource "aws_ssm_parameter" "password" {
  name  = "/staging/database/password"
  type  = "SecureString"
  value = random_string.password.result
}
```

**Security practice:** Never hardcode passwords! This generates a random 32-character password and stores it encrypted in AWS Systems Manager.

```hcl
module "this" {
  source = "terraform-aws-modules/rds/aws"

  engine                = "postgres"
  engine_version        = "17.2"
  instance_class        = "db.t4g.micro"
  allocated_storage     = 50
  max_allocated_storage = 100

  username              = replace(var.name, "-", "_")
  password              = random_string.password.result
  publicly_accessible   = false
  skip_final_snapshot   = true
}
```

**Key settings:**

- **Instance class** `db.t4g.micro`: Small, low-cost database (1 vCPU, 1GB RAM)
- **Storage**: Starts at 50GB, can auto-grow to 100GB
- **Username**: Environment name with underscores (`staging`)
- **Publicly accessible = false**: Only accessible from within VPC (secure!)
- **Skip final snapshot**: When destroying, don't create backup (good for dev/staging, bad for production)

---

### 4. Cluster Module (`module/cluster`)

**Role:** Creates the ECS cluster that runs Docker containers.

**What it creates:**

- ECS Cluster
- Auto Scaling Groups (ASG)
- EC2 Launch Templates
- Application Load Balancer (ALB)
- CloudFront Distribution (CDN)
- Capacity Providers

This is the most complex module. Let's break it down:

#### ECS Cluster

```hcl
resource "aws_ecs_cluster" "this" {
  name = "staging"

  setting {
    name  = "containerInsights"
    value = "enabled"
  }
}
```

**ECS (Elastic Container Service)** manages Docker containers. `containerInsights` gives you monitoring and metrics.

#### Launch Template

```hcl
resource "aws_launch_template" "this" {
  for_each = { for provider_name, provider in var.capacity_providers : provider_name => provider }

  image_id      = jsondecode(data.aws_ssm_parameter.ecs_optimized_ami.value)["image_id"]
  instance_type = each.value.instance_type

  user_data = base64encode(templatefile("${path.module}/user_data.tpl", {
    cluster_name = var.name
  }))
}
```

**Launch Template** is a blueprint for EC2 instances. Think of it like a cookie cutter.

**for_each loop:** Creates one template per capacity provider (in this case, just "spot").

**AMI (Amazon Machine Image):** The OS image for the instance. Here it uses the ECS-optimized Amazon Linux 2 image (has Docker pre-installed).

**user_data:** Script that runs when instance boots up:

```bash
#cloud-config
write_files:
  - path: /etc/ecs/ecs.config
    content: |
      ECS_CLUSTER=staging
      ECS_ENABLE_SPOT_INSTANCE_DRAINING=true
      ECS_ENABLE_TASK_IAM_ROLE=true
```

This configures the instance to join the ECS cluster named "staging" and enables graceful shutdown for spot instances.

#### Auto Scaling Group

```hcl
resource "aws_autoscaling_group" "this" {
  for_each = { for provider_name, provider in var.capacity_providers : provider_name => provider }

  desired_capacity = 1
  min_size         = 1
  max_size         = 5

  instance_refresh {
    strategy = "Rolling"
    preferences {
      min_healthy_percentage = 50
    }
  }
}
```

**ASG manages a fleet of EC2 instances:**

- Starts with 1 instance
- Can scale up to 5 instances
- Always keeps at least 1 running
- When updating (like changing instance type), replaces instances in a rolling fashion while keeping 50% healthy

**Scaling policy:**

```hcl
resource "aws_autoscaling_policy" "this" {
  policy_type = "TargetTrackingScaling"

  target_tracking_configuration {
    predefined_metric_specification {
      predefined_metric_type = "ASGAverageCPUUtilization"
    }
    target_value = 50
  }
}
```

**What this does:** Automatically adds instances if average CPU goes above 50%, removes them if it drops below.

#### Capacity Provider

```hcl
resource "aws_ecs_capacity_provider" "this" {
  for_each = { for provider_name, provider in var.capacity_providers : provider_name => provider }

  name = "staging-spot"

  auto_scaling_group_provider {
    auto_scaling_group_arn = aws_autoscaling_group.this[each.key].arn

    managed_scaling {
      status = "DISABLED"
    }
  }
}
```

**Capacity Provider** links ECS to the Auto Scaling Group. With `managed_scaling` disabled, ECS won't automatically scale - we're relying on the CPU-based policy instead.

#### Load Balancer

```hcl
resource "aws_lb" "this" {
  load_balancer_type = "application"
  internal           = true
  subnets            = var.subnets
  security_groups    = concat([aws_security_group.load_balancer.id], var.security_groups)
}

resource "aws_lb_listener" "http" {
  load_balancer_arn = aws_lb.this.arn
  port              = "80"
  protocol          = "HTTP"

  default_action {
    type = "fixed-response"
    fixed_response {
      content_type = "text/plain"
      message_body = "404 Not Found"
      status_code  = "404"
    }
  }
}
```

**Application Load Balancer (ALB):**

- Distributes traffic across container instances
- `internal = true` means it's only accessible from within VPC (not directly from internet)
- Listens on port 80 (HTTP)
- Default action returns 404 (gets overridden by service-specific rules later)

#### CloudFront Distribution

```hcl
resource "aws_cloudfront_vpc_origin" "this" {
  vpc_origin_endpoint_config {
    arn                    = aws_lb.this.arn
    origin_protocol_policy = "http-only"
  }
}

resource "aws_cloudfront_distribution" "this" {
  enabled = true

  origin {
    domain_name = aws_lb.this.dns_name
    vpc_origin_config {
      vpc_origin_id = aws_cloudfront_vpc_origin.this.id
    }
  }

  default_cache_behavior {
    viewer_protocol_policy = "redirect-to-https"
    allowed_methods        = ["GET", "HEAD", "OPTIONS", "PUT", "POST", "PATCH", "DELETE"]
    cached_methods         = ["GET", "HEAD"]
  }
}
```

**CloudFront** is AWS's CDN (Content Delivery Network):

- Sits in front of your load balancer
- Provides HTTPS even though internal load balancer is HTTP-only
- Caches GET/HEAD requests for faster response
- Distributed globally for low latency

**Traffic flow:**

```
User (HTTPS) → CloudFront → VPC Origin → Load Balancer (HTTP) → Containers
```

---

### 5. Service Module (`module/service`)

**Role:** Deploys your actual FastAPI application as containers.

**What it creates:**

- ECS Task Definition (container blueprint)
- ECS Service (runs and maintains containers)
- CloudWatch Log Group (for application logs)
- IAM Roles (permissions)
- Load Balancer Target Group (routes traffic to containers)
- SSM Parameters (for secrets)

#### Task Definition

```hcl
resource "aws_ecs_task_definition" "this" {
  family             = "staging-service"
  execution_role_arn = aws_iam_role.execution.arn
  task_role_arn      = aws_iam_role.task.arn

  container_definitions = jsonencode([{
    name   = "service"
    image  = "${var.image_registry}/${var.image_repository}:${var.image_tag}"
    cpu    = 256
    memory = 512

    portMappings = [{ containerPort = 8080 }]

    environment = [
      for item_name, item in var.config : {
        name  = upper(replace(item_name, "-", "_"))
        value = item
      }
    ]

    secrets = [
      for item in var.secrets : {
        name      = upper(replace(item, "-", "_"))
        valueFrom = module.parameter_secure[item].ssm_parameter_arn
      }
    ]
  }])
}
```

**Task Definition** describes how to run a container:

- **Image**: Pulls from ECR (Elastic Container Registry): `123456789.dkr.ecr.us-east-2.amazonaws.com/ai-mentor:staging`
- **Resources**: 256 CPU units (0.25 vCPU), 512MB RAM
- **Port**: Container listens on 8080
- **Environment variables**: Plain config values
- **Secrets**: Injected from SSM Parameter Store (encrypted)

**Two IAM roles:**

- **Execution role**: Permissions to pull image and read secrets (used by ECS itself)
- **Task role**: Permissions for your application code (what your app can access)

#### Secrets Management

```hcl
module "parameter_secure" {
  for_each = { for item in var.secrets : item => item }

  source = "terraform-aws-modules/ssm-parameter/aws"

  name                 = "/staging/service/${lower(replace(each.key, "_", "-"))}"
  secure_type          = true
  value                = "example"
  ignore_value_changes = true
}
```

**What this does:** Creates a placeholder SSM parameter for each secret. You manually update the actual values in AWS console or CLI. The `ignore_value_changes = true` prevents Terraform from resetting them.

Example: `ANTHROPIC_API_KEY` becomes parameter `/staging/service/anthropic-api-key` with value "example" (you change it to your real key).

#### ECS Service

```hcl
resource "aws_ecs_service" "this" {
  cluster         = var.cluster_id
  desired_count   = 1
  task_definition = aws_ecs_task_definition.this.arn

  capacity_provider_strategy {
    base              = 1
    capacity_provider = "staging-spot"
    weight            = 100
  }

  load_balancer {
    container_name   = "service"
    container_port   = 8080
    target_group_arn = aws_lb_target_group.service.arn
  }
}
```

**ECS Service** keeps your containers running:

- Maintains 1 container (desired_count)
- If it crashes, ECS restarts it
- Uses spot capacity provider
- Registers with load balancer

#### Load Balancer Integration

```hcl
resource "aws_lb_target_group" "service" {
  port     = 8080
  protocol = "HTTP"
  vpc_id   = var.vpc_id
}

resource "aws_lb_listener_rule" "service" {
  listener_arn = var.listener_arn

  action {
    target_group_arn = aws_lb_target_group.service.arn
    type             = "forward"
  }

  condition {
    path_pattern {
      values = ["/*"]
    }
  }
}
```

**Target Group**: Collection of container instances to send traffic to.

**Listener Rule**: "For any path (`/*`), forward traffic to this target group."

---

## How It All Connects

Let's trace a request through the entire system:

### 1. User Makes Request

```
User → https://xyz123.cloudfront.net/chat
```

### 2. CloudFront (CDN)

- Receives HTTPS request
- Checks cache (not cached for POST requests)
- Forwards to origin (Load Balancer)

### 3. Load Balancer

- Receives HTTP request on port 80
- Checks listener rules
- Matches path `/*` to service target group
- Forwards to healthy container instance

### 4. ECS Container

- Container receives request on port 8080
- FastAPI application processes it
- Needs to query database

### 5. Database Connection

- Container has `SUPABASE_DATABASE_URL` secret
- Security group allows port 5432 from private subnet
- Connects to RDS PostgreSQL instance

### 6. Response Journey

```
Container → Load Balancer → CloudFront → User
```

### Dependency Graph

```
main.tf
  └─ module.staging (environment)
       ├─ module.network
       │    ├─ VPC
       │    ├─ Subnets (public, private, database)
       │    ├─ NAT Gateway
       │    ├─ Security Groups
       │    └─ Bastion Host
       │
       ├─ module.database (depends on network)
       │    ├─ RDS PostgreSQL
       │    └─ Password in SSM
       │
       ├─ module.cluster (depends on network)
       │    ├─ ECS Cluster
       │    ├─ Auto Scaling Group
       │    ├─ Launch Template
       │    ├─ Load Balancer
       │    └─ CloudFront
       │
       └─ module.service (depends on cluster)
            ├─ Task Definition
            ├─ ECS Service
            ├─ Target Group
            ├─ Listener Rule
            └─ Secrets in SSM
```

---

## Real-World Analogy

Think of this infrastructure as a **restaurant**:

### Network Module = Building & Layout

- **VPC**: The entire restaurant building
- **Public Subnets**: Dining area (customers can enter)
- **Private Subnets**: Kitchen (staff only)
- **Database Subnets**: Storage room (restricted access)
- **NAT Gateway**: Service entrance (kitchen can receive deliveries)
- **Security Groups**: Doors with locks (control who goes where)
- **Bastion**: Manager's office (access point to restricted areas)

### Database Module = Storage System

- **RDS**: Industrial refrigerator/pantry
- **Security Groups**: Only kitchen staff can access

### Cluster Module = Kitchen Infrastructure

- **ECS Cluster**: The kitchen itself
- **Auto Scaling Group**: Hiring more cooks when busy, sending them home when slow
- **Launch Template**: Training manual for new cooks
- **Load Balancer**: Maître d' who assigns tables to waiters
- **CloudFront**: Delivery service that brings food to customers far away

### Service Module = The Cooking Process

- **Task Definition**: Recipe card
- **Container**: Individual cook following the recipe
- **ECS Service**: Kitchen manager ensuring recipes are always being made
- **Secrets**: Secret ingredients (locked in safe)
- **Logs**: Cook's notes and timing records

### Traffic Flow = Customer Order

1. **Customer** calls delivery service (CloudFront)
2. **Delivery service** contacts restaurant (Load Balancer)
3. **Maître d'** assigns order to available cook (Target Group)
4. **Cook** prepares meal using recipe (Container runs code)
5. **Cook** gets ingredients from storage (Database query)
6. **Meal** travels back through delivery → customer

---

## Key Takeaways

### 1. Modular Design

Each module handles one concern (network, database, cluster, service). This makes it:

- **Easier to understand**: Focus on one piece at a time
- **Reusable**: Use the same modules for dev, staging, production
- **Maintainable**: Change one module without breaking others

### 2. Security By Default

- Database not publicly accessible
- Secrets stored encrypted
- Resources isolated in private subnets
- Security groups restrict traffic

### 3. Cost Optimization

- Spot instances (cheaper)
- Single NAT gateway (instead of 3)
- Small instance sizes
- Auto-scaling (pay for what you use)

### 4. High Availability

- Multi-AZ deployment (spread across data centers)
- Auto Scaling Groups (replace failed instances)
- Load Balancer (distributes traffic)
- CloudFront (global CDN)

### 5. Infrastructure as Code Benefits

- **Version controlled**: See what changed and when
- **Reproducible**: Rebuild everything from scratch
- **Documented**: Code is documentation
- **Collaborative**: Team members work on same infrastructure

---

## Next Steps

### To Deploy This Infrastructure:

1. **Install Terraform**:

   ```bash
   brew install terraform  # macOS
   ```

2. **Configure AWS credentials**:

   ```bash
   aws configure
   ```

3. **Initialize Terraform**:

   ```bash
   cd backend/agent/terraform
   terraform init
   ```

4. **Preview changes**:

   ```bash
   terraform plan
   ```

5. **Deploy**:

   ```bash
   terraform apply
   ```

6. **Update secrets** (after deploy):

   ```bash
   aws ssm put-parameter \
     --name "/staging/service/anthropic-api-key" \
     --value "your-actual-key" \
     --type "SecureString" \
     --overwrite
   ```

7. **Access bastion** (to connect to private resources):

   ```bash
   # Get private key
   aws ssm get-parameter \
     --name "/staging/bastion/private-key" \
     --with-decryption \
     --query "Parameter.Value" \
     --output text > bastion_key.pem

   chmod 400 bastion_key.pem

   # SSH to bastion
   ssh -i bastion_key.pem ec2-user@<bastion-public-ip>
   ```

### To Customize:

- **Change instance types**: Modify `capacity_providers` in `environment/main.tf`
- **Add more environments**: Duplicate the `module "staging"` block with different names
- **Adjust scaling**: Change `max_size` in cluster ASG or `desired_count` in service
- **Add more services**: Duplicate `module "service"` with different ports/paths

### Tips for Learning

| Question                                    | Answer                                                                       |
| ------------------------------------------- | ---------------------------------------------------------------------------- |
| "I changed code but nothing happened"       | Run `terraform plan` then `terraform apply`                                  |
| "How do I see what's deployed?"             | Run `terraform state list`                                                   |
| "How do I destroy everything?"              | Run `terraform destroy` (careful!)                                           |
| "Why does plan show changes I didn't make?" | Someone else applied changes, or AWS drifted. Run `terraform apply` to sync. |
| "What if apply fails halfway?"              | Run `terraform apply` again - it's idempotent (safe to re-run)               |

---

## Conclusion

You now understand how this Terraform code creates a complete, production-ready infrastructure for a FastAPI application on AWS. It provisions networking, databases, container clusters, load balancing, and CDN - all automatically, repeatably, and securely.

The modular design means you can reuse these building blocks for other projects, customize them for different needs, and maintain them as your application grows.

Happy terraforming! 🚀
