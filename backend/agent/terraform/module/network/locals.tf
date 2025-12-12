locals {
  subnets = {
    # "database"    = 6,  # Commented out - using Supabase instead of RDS
    # "elasticache" = 6,  # Commented out - not using Elasticache currently
    "intra"       = 5,
    "private"     = 3,
    "public"      = 5,
  }
}