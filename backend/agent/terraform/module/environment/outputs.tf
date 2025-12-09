output "service_config" {
  value = {
    CORS_ORIGINS = jsonencode(var.cors_origins)
  }
}

output "cluster_name" {
  description = "Name of the ECS cluster"
  value       = var.name
}

output "subdomain" {
  description = "Full domain name for this environment"
  value       = var.subdomain != "" && var.domain_name != "" ? "${var.subdomain}.${var.domain_name}" : ""
}

