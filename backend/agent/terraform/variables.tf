variable "staging_cors_origins" {
  description = "CORS origins for staging environment"
  type        = list(string)
  default = [
    "http://localhost:3000",
    "http://localhost:5173",
    "https://shawn-exp-frontend-config.d1helczvbtzd13.amplifyapp.com",
    "https://stage.intersectionlabs.net",
    "https://main.d5gwshxu5q3t4.amplifyapp.com"
  ]
}

