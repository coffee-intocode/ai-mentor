terraform {
  backend "s3" {
    bucket = "terraform-state-intersection"
    key    = "terraform.tfstate"
    region = "us-east-2"
  }
}