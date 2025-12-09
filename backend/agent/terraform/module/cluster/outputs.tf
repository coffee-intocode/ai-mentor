output "cluster_arn" {
  value = aws_ecs_cluster.this.arn
}

output "distribution_domain" {
  value = aws_cloudfront_distribution.this.domain_name
}

output "distribution_zone_id" {
  description = "CloudFront hosted zone ID for Route53 alias records"
  value       = aws_cloudfront_distribution.this.hosted_zone_id
}


output "listener_arn" {
  value = aws_lb_listener.http.arn
}
