terraform {
  backend "s3" {
    bucket = "ai-mentor-terraform-state"
    key    = "terraform.tfstate"
    region = "us-east-2"
  }
}