variable "bastion_ingress" {
  default     = []
  description = "CIDR blocks for bastion ingress"
  type        = list(string)
}

variable "name" {
  description = "Name of the cloud environment"
  type        = string
}

variable "subdomain" {
  description = "Subdomain for this environment (e.g., 'dev', 'stage', 'app')"
  type        = string
  default     = ""
}

variable "domain_name" {
  description = "Base domain name"
  type        = string
  default     = ""
}

variable "route53_zone_id" {
  description = "Route53 hosted zone ID"
  type        = string
  default     = ""
}

variable "acm_certificate_arn" {
  description = "ACM certificate ARN for CloudFront"
  type        = string
  default     = ""
}

variable "cors_origins" {
  description = "CORS origins"
  type        = list(string)
  default     = ["http://localhost:3000", "http://localhost:5173"]
}
