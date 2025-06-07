variable "function_name" {
  description = "Name of the Lambda function"
  type        = string
}

variable "lambda_role_arn" {
  description = "ARN of the IAM role for Lambda execution"
  type        = string
}

variable "s3_bucket" {
  description = "Name of the S3 bucket for DuckDB storage"
  type        = string
}

variable "environment" {
  description = "Environment name (dev, prod)"
  type        = string
}

variable "lambda_zip_path" {
  description = "Path to the Lambda deployment zip file"
  type        = string
  default     = "./lambda_function.zip"
}

variable "create_placeholder_zip" {
  description = "Whether to create a placeholder zip file if none exists"
  type        = bool
  default     = true
}

variable "tags" {
  description = "Tags to apply to Lambda resources"
  type        = map(string)
  default     = {}
}
