output "api_endpoint" {
  description = "API Gateway endpoint URL"
  value       = "${aws_api_gateway_rest_api.fitlog_api.execution_arn}/${var.environment}"
}

output "api_gateway_url" {
  description = "API Gateway invoke URL" 
  value       = "https://${aws_api_gateway_rest_api.fitlog_api.id}.execute-api.${data.aws_region.current.name}.amazonaws.com/${var.environment}"
}

output "api_gateway_id" {
  description = "API Gateway ID"
  value       = aws_api_gateway_rest_api.fitlog_api.id
}

output "api_gateway_arn" {
  description = "API Gateway ARN"
  value       = aws_api_gateway_rest_api.fitlog_api.arn
}

# Data source for current region
data "aws_region" "current" {} 