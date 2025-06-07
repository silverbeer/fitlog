variable "name_prefix" {
  description = "Prefix for naming IAM resources"
  type        = string
}

variable "s3_bucket_arn" {
  description = "ARN of the S3 bucket for DuckDB data storage"
  type        = string
}

variable "tags" {
  description = "Tags to apply to IAM resources"
  type        = map(string)
  default     = {}
} 