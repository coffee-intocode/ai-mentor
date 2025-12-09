resource "aws_route53_zone" "main" {
  name    = var.domain_name
  comment = "Managed by Terraform for ${var.domain_name}"

  lifecycle {
    prevent_destroy = true
  }

  tags = merge(
    var.tags,
    {
      Name = var.domain_name
    }
  )
}
