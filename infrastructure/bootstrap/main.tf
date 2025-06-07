# Bootstrap Terraform Configuration
# Creates S3 bucket and DynamoDB table for Terraform state management
# This runs with local state, then main infrastructure uses remote state

terraform {
  required_version = ">= 1.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
  
  # NOTE: This bootstrap config uses LOCAL state
  # The main infrastructure will use the S3 backend we create here
}

provider "aws" {
  region  = var.aws_region
  profile = var.aws_profile  # Use specific AWS profile for personal account
  
  default_tags {
    tags = {
      Project     = "fitlog"
      Environment = "bootstrap"
      ManagedBy   = "terraform-bootstrap"
      Purpose     = "terraform-state-management"
    }
  }
}

# Variables
variable "aws_region" {
  description = "AWS region"
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

variable "state_bucket_name" {
  description = "Name for the Terraform state S3 bucket"
  type        = string
  default     = "fitlog-terraform-state-bucket"
}

variable "dynamodb_table_name" {
  description = "Name for the DynamoDB table for state locking"
  type        = string
  default     = "fitlog-terraform-state-lock"
}

# Data sources
data "aws_caller_identity" "current" {}

# Account validation - ensure we're using the correct AWS account
locals {
  account_id = data.aws_caller_identity.current.account_id
  # Make bucket name globally unique by including account ID
  state_bucket_name = "${var.state_bucket_name}-${local.account_id}"
  
  # Account validation
  is_correct_account = var.expected_account_id == "" ? true : local.account_id == var.expected_account_id
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

# S3 bucket for Terraform state
resource "aws_s3_bucket" "terraform_state" {
  bucket = local.state_bucket_name

  # Prevent accidental deletion
  lifecycle {
    prevent_destroy = true
  }

  tags = {
    Name        = local.state_bucket_name
    Purpose     = "terraform-state-storage"
    Environment = "bootstrap"
    AccountType = "personal"
  }
  
  depends_on = [null_resource.account_validation]
}

# S3 bucket versioning (essential for state files)
resource "aws_s3_bucket_versioning" "terraform_state" {
  bucket = aws_s3_bucket.terraform_state.id
  versioning_configuration {
    status = "Enabled"
  }
}

# S3 bucket server-side encryption
resource "aws_s3_bucket_server_side_encryption_configuration" "terraform_state" {
  bucket = aws_s3_bucket.terraform_state.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
    bucket_key_enabled = true
  }
}

# S3 bucket public access block (security)
resource "aws_s3_bucket_public_access_block" "terraform_state" {
  bucket = aws_s3_bucket.terraform_state.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# DynamoDB table for state locking
resource "aws_dynamodb_table" "terraform_state_lock" {
  name           = var.dynamodb_table_name
  billing_mode   = "PAY_PER_REQUEST"  # More cost-effective for personal use
  hash_key       = "LockID"

  attribute {
    name = "LockID"
    type = "S"
  }

  # Enable point-in-time recovery
  point_in_time_recovery {
    enabled = true
  }

  # Enable deletion protection in production
  deletion_protection_enabled = false  # Set to true for production

  tags = {
    Name        = var.dynamodb_table_name
    Purpose     = "terraform-state-locking"
    Environment = "bootstrap"
    AccountType = "personal"
  }
  
  depends_on = [null_resource.account_validation]
}

# Outputs for use in main configuration
output "state_bucket_name" {
  description = "Name of the S3 bucket for Terraform state"
  value       = aws_s3_bucket.terraform_state.bucket
}

output "state_bucket_arn" {
  description = "ARN of the S3 bucket for Terraform state"
  value       = aws_s3_bucket.terraform_state.arn
}

output "dynamodb_table_name" {
  description = "Name of the DynamoDB table for state locking"
  value       = aws_dynamodb_table.terraform_state_lock.name
}

output "dynamodb_table_arn" {
  description = "ARN of the DynamoDB table for state locking"
  value       = aws_dynamodb_table.terraform_state_lock.arn
}

output "account_id" {
  description = "AWS Account ID being used"
  value       = local.account_id
}

# Configuration for main Terraform backend
output "backend_configuration" {
  description = "Backend configuration to use in main Terraform"
  value = {
    bucket         = aws_s3_bucket.terraform_state.bucket
    key            = "fitlog/terraform.tfstate"
    region         = var.aws_region
    dynamodb_table = aws_dynamodb_table.terraform_state_lock.name
    encrypt        = true
    profile        = var.aws_profile
  }
} 