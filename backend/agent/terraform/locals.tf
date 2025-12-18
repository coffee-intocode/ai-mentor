locals {
  bastion_ingress   = ["150.221.144.4/32"]
  domain_name       = "" # Set to your domain (e.g., "intersectionlabs.net") to enable custom domain, or "" to disable
  staging_subdomain = "stage.api"

  # Helper to check if custom domain is enabled
  custom_domain_enabled = local.domain_name != ""
}
