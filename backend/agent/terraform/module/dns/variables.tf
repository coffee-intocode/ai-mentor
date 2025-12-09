variable "domain_name" {
  description = "Base domain name for the Route53 hosted zone"
  type        = string
}

variable "tags" {
  description = "Tags to apply to the Route53 hosted zone"
  type        = map(string)
  default     = {}
}
