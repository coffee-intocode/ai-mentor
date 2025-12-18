module "network" {
  source = "../network"

  availability_zones = ["us-east-2a", "us-east-2b", "us-east-2c"]
  bastion_ingress    = var.bastion_ingress
  cidr               = "10.0.0.0/16"
  name               = var.name
}

# Commented out - using Supabase instead of provisioning RDS
# module "database" {
#   source = "../database"

#   security_groups = [module.network.database_security_group]
#   subnets         = module.network.database_subnets
#   name            = var.name
#   vpc_name        = module.network.vpc_name

#   depends_on = [module.network]
# }

module "cluster" {
  source = "../cluster"

  security_groups = [module.network.private_security_group]
  subnets         = module.network.private_subnets
  name            = var.name
  vpc_id          = module.network.vpc_id

  # ✅ Add custom domain configuration
  custom_domain_name  = var.subdomain != "" && var.domain_name != "" ? "${var.subdomain}.${var.domain_name}" : ""
  acm_certificate_arn = var.acm_certificate_arn

  # Customization what instance type we're provisioning and where do you want to put the instances when ready to be scheduled (spot or on-demand)
  capacity_providers = {
    "spot" = {
      instance_type = "t3a.medium"
      market_type   = "spot"
    }
  }
}

module "service" {
  source = "../service"

  capacity_provider = "spot"
  cluster_id        = module.cluster.cluster_arn
  cluster_name      = var.name
  image_registry    = "${data.aws_caller_identity.this.account_id}.dkr.ecr.${data.aws_region.this.name}.amazonaws.com"
  image_repository  = "ai-mentor"
  image_tag         = var.name
  listener_arn      = module.cluster.listener_arn
  name              = "service"
  paths             = ["/*"]
  port              = 8080
  vpc_id            = module.network.vpc_id

  # This is where we add env variables for the service
  config = {
    CORS_ORIGINS = jsonencode(var.cors_origins)
    # GOOGLE_REDIRECT_URL = "https://${module.cluster.distribution_domain}/auth/google/callback"
    # GOOSE_DRIVER        = "postgres"

  }

  secrets = [
    "ANTHROPIC_API_KEY",
    "SUPABASE_DATABASE_URL",
    "ALEMBIC_DB_URL"
  ]
}


# Create Route53 record for this environment's subdomain (only if custom domain is configured)
resource "aws_route53_record" "environment" {
  count = var.route53_zone_id != "" ? 1 : 0

  zone_id = var.route53_zone_id
  name    = "${var.subdomain}.${var.domain_name}"
  type    = "A"

  alias {
    name                   = module.cluster.distribution_domain
    zone_id                = module.cluster.distribution_zone_id
    evaluate_target_health = false
  }
}