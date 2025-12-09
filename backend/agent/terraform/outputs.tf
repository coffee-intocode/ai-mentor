# Output active environments for use in CI/CD and Makefile
output "active_environments" {
  description = "List of active environment names for build/deploy automation"
  value = compact([
    try(module.staging.cluster_name, ""),
    # Uncomment as environments are enabled:
    # try(module.dev.cluster_name, ""),
    # try(module.prod.cluster_name, ""),
  ])
}

