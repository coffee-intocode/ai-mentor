# Create hosted zone ONCE at root level (only if custom domain is enabled)
module "dns" {
  count  = local.custom_domain_enabled ? 1 : 0
  source = "./module/dns"

  domain_name = local.domain_name

  tags = {
    ManagedBy = "terraform"
    Purpose   = "Main hosted zone"
  }
}

# Create wildcard certificate ONCE at root level (only if custom domain is enabled)
module "acm" {
  count  = local.custom_domain_enabled ? 1 : 0
  source = "./module/acm"

  providers = {
    aws.us_east_1 = aws.us_east_1
  }

  domain_name = local.domain_name
  subject_alternative_names = [
    "*.${local.domain_name}",                          # Covers api, app, www, etc.
    "${local.staging_subdomain}.${local.domain_name}", # stage.api.intersectionlabs.net
    # Add more explicit subdomains as needed:
    # "dev.api.${local.domain_name}",
    # "prod.api.${local.domain_name}",
  ]

  zone_id = module.dns[0].zone_id

  tags = {
    ManagedBy = "terraform"
  }
}

# Staging environment with subdomain
module "staging" {
  source = "./module/environment"

  bastion_ingress     = local.bastion_ingress
  name                = "staging"
  subdomain           = local.custom_domain_enabled ? local.staging_subdomain : ""
  domain_name         = local.domain_name
  route53_zone_id     = local.custom_domain_enabled ? module.dns[0].zone_id : ""
  acm_certificate_arn = local.custom_domain_enabled ? module.acm[0].certificate_arn : ""
  cors_origins        = var.staging_cors_origins
}

# Dev environment with subdomain
# module "dev" {
#   source = "./module/environment"

#   bastion_ingress     = local.bastion_ingress
#   name                = "dev"
#   subdomain           = "dev"  # Creates dev.yourdomain.com
#   domain_name         = "yourdomain.com"
#   route53_zone_id     = module.dns.zone_id
#   acm_certificate_arn = module.acm.certificate_arn
# }

# Production environment with subdomain
# module "prod" {
#   source = "./module/environment"

#   bastion_ingress     = local.bastion_ingress
#   name                = "production"
#   subdomain           = "app"  # Creates app.yourdomain.com
#   domain_name         = "yourdomain.com"
#   route53_zone_id     = module.dns.zone_id
#   acm_certificate_arn = module.acm.certificate_arn
# }
