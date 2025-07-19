# Variables for S3 module

variable "bucket_name" {
  description = "Name of the S3 bucket for DuckDB storage"
  type        = string
}

variable "environment" {
  description = "Environment name (dev, prod)"
  type        = string
}

variable "tags" {
  description = "Tags to apply to resources"
  type        = map(string)
  default     = {}
}
