output "lambda_role_arn" {
  description = "ARN of the Lambda execution role"
  value       = aws_iam_role.lambda_role.arn
}

output "lambda_role_name" {
  description = "Name of the Lambda execution role"
  value       = aws_iam_role.lambda_role.name
}

output "lambda_s3_policy_arn" {
  description = "ARN of the Lambda S3 access policy"
  value       = aws_iam_policy.lambda_s3_policy.arn
}

output "lambda_logs_policy_arn" {
  description = "ARN of the Lambda CloudWatch Logs policy"
  value       = aws_iam_policy.lambda_logs_policy.arn
}
