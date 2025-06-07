# Fitlog Cloud Infrastructure
# Terraform configuration for AWS serverless deployment

terraform {
  required_version = ">= 1.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
  
  # TODO: Configure backend for state storage
  # backend "s3" {
  #   bucket = "fitlog-terraform-state"
  #   key    = "terraform.tfstate"
  #   region = "us-east-1"
  # }
}

# Configure AWS Provider
provider "aws" {
  region = var.aws_region
  
  default_tags {
    tags = {
      Project     = "fitlog"
      Environment = var.environment
      ManagedBy   = "terraform"
    }
  }
}

# Data sources
data "aws_caller_identity" "current" {}
data "aws_region" "current" {}

# Variables
variable "aws_region" {
  description = "AWS region for resources"
  type        = string
  default     = "us-east-1"
}

variable "environment" {
  description = "Environment name (dev, prod)"
  type        = string
  default     = "dev"
}

variable "project_name" {
  description = "Project name for resource naming"
  type        = string
  default     = "fitlog"
}

# Local values
locals {
  name_prefix = "${var.project_name}-${var.environment}"
  
  common_tags = {
    Project     = var.project_name
    Environment = var.environment
    ManagedBy   = "terraform"
  }
}

# S3 bucket for DuckDB storage
module "s3" {
  source = "./modules/s3"
  
  bucket_name = "${local.name_prefix}-data"
  environment = var.environment
  tags        = local.common_tags
}

# IAM roles and policies
module "iam" {
  source = "./modules/iam"
  
  name_prefix = local.name_prefix
  s3_bucket_arn = module.s3.bucket_arn
  tags        = local.common_tags
}

# Lambda function
module "lambda" {
  source = "./modules/lambda"
  
  function_name     = "${local.name_prefix}-api"
  s3_bucket        = module.s3.bucket_name
  lambda_role_arn  = module.iam.lambda_role_arn
  environment      = var.environment
  tags            = local.common_tags
}

# API Gateway
module "api_gateway" {
  source = "./modules/api-gateway"
  
  api_name          = "${local.name_prefix}-api"
  lambda_function_arn = module.lambda.function_arn
  lambda_function_name = module.lambda.function_name
  environment       = var.environment
  tags             = local.common_tags
}

# Outputs
output "api_endpoint" {
  description = "API Gateway endpoint URL"
  value       = module.api_gateway.api_endpoint
}

output "s3_bucket_name" {
  description = "S3 bucket name for data storage"
  value       = module.s3.bucket_name
}

output "lambda_function_name" {
  description = "Lambda function name"
  value       = module.lambda.function_name
} 