output "function_arn" {
  description = "ARN of the Lambda function"
  value       = aws_lambda_function.fitlog_api.arn
}

output "function_name" {
  description = "Name of the Lambda function"
  value       = aws_lambda_function.fitlog_api.function_name
}

output "function_invoke_arn" {
  description = "Invoke ARN of the Lambda function (for API Gateway)"
  value       = aws_lambda_function.fitlog_api.invoke_arn
}

output "function_url" {
  description = "Lambda function URL for direct HTTP access"
  value       = aws_lambda_function_url.fitlog_api.function_url
}

output "log_group_name" {
  description = "CloudWatch Log Group name"
  value       = aws_cloudwatch_log_group.lambda_logs.name
}

output "log_group_arn" {
  description = "CloudWatch Log Group ARN"
  value       = aws_cloudwatch_log_group.lambda_logs.arn
} 