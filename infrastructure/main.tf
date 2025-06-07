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

  # S3 backend for state storage (configured after bootstrap)
  backend "s3" {
    # These values will be provided via terraform init -backend-config
    # or via backend.hcl file
    # bucket         = "fitlog-terraform-state-bucket-123456789012"
    # key            = "fitlog/terraform.tfstate"
    # region         = "us-east-1"
    # dynamodb_table = "fitlog-terraform-state-lock"
    # encrypt        = true
    # profile        = "personal"
  }
}

# Configure AWS Provider
provider "aws" {
  region  = var.aws_region
  profile = var.aws_profile  # Use specific AWS profile for personal account

  default_tags {
    tags = {
      Project     = "fitlog"
      Environment = var.environment
      ManagedBy   = "terraform"
      AccountType = "personal"
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

variable "aws_profile" {
  description = "AWS profile to use (should be personal account)"
  type        = string
  default     = "personal"  # Change this to your personal profile name
}

variable "expected_account_id" {
  description = "Expected AWS account ID (personal account) for validation"
  type        = string
  default     = ""  # Set this to your personal AWS account ID
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

# Account validation - ensure we're using the correct AWS account
locals {
  account_id = data.aws_caller_identity.current.account_id
  name_prefix = "${var.project_name}-${var.environment}"

  # Account validation
  is_correct_account = var.expected_account_id == "" ? true : local.account_id == var.expected_account_id

  common_tags = {
    Project     = var.project_name
    Environment = var.environment
    ManagedBy   = "terraform"
    AccountType = "personal"
  }
}

# Validation check - fail if wrong account
resource "null_resource" "account_validation" {
  count = local.is_correct_account ? 0 : 1

  provisioner "local-exec" {
    command = <<-EOT
      echo "❌ ACCOUNT VALIDATION FAILED!"
      echo "Expected account ID: ${var.expected_account_id}"
      echo "Current account ID:  ${local.account_id}"
      echo "Please check your AWS profile configuration."
      exit 1
    EOT
  }
}

# S3 bucket for DuckDB storage
module "s3" {
  source = "./modules/s3"

  bucket_name = "${local.name_prefix}-data"
  environment = var.environment
  tags        = local.common_tags

  depends_on = [null_resource.account_validation]
}

# IAM roles and policies
module "iam" {
  source = "./modules/iam"

  name_prefix = local.name_prefix
  s3_bucket_arn = module.s3.bucket_arn
  tags        = local.common_tags

  depends_on = [null_resource.account_validation]
}

# Lambda function
module "lambda" {
  source = "./modules/lambda"

  function_name     = "${local.name_prefix}-api"
  s3_bucket        = module.s3.bucket_name
  lambda_role_arn  = module.iam.lambda_role_arn
  environment      = var.environment
  tags            = local.common_tags

  depends_on = [null_resource.account_validation]
}

# API Gateway
module "api_gateway" {
  source = "./modules/api-gateway"

  api_name          = "${local.name_prefix}-api"
  lambda_function_arn = module.lambda.function_arn
  lambda_function_name = module.lambda.function_name
  environment       = var.environment
  tags             = local.common_tags

  depends_on = [null_resource.account_validation]
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

output "account_id" {
  description = "AWS Account ID being used"
  value       = local.account_id
}
