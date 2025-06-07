# API Gateway Module for Fitlog
# Creates REST API Gateway with Lambda integration

# REST API Gateway
resource "aws_api_gateway_rest_api" "fitlog_api" {
  name        = var.api_name
  description = "Fitlog serverless API for exercise tracking"

  endpoint_configuration {
    types = ["REGIONAL"]
  }

  tags = var.tags
}

# API Gateway Deployment
resource "aws_api_gateway_deployment" "fitlog_api" {
  depends_on = [
    aws_api_gateway_integration.lambda_proxy,
    aws_api_gateway_method.proxy_method,
    aws_api_gateway_method.root_method,
  ]

  rest_api_id = aws_api_gateway_rest_api.fitlog_api.id

  lifecycle {
    create_before_destroy = true
  }
}

# Root resource (/)
resource "aws_api_gateway_method" "root_method" {
  rest_api_id   = aws_api_gateway_rest_api.fitlog_api.id
  resource_id   = aws_api_gateway_rest_api.fitlog_api.root_resource_id
  http_method   = "ANY"
  authorization = "NONE"
}

resource "aws_api_gateway_integration" "root_integration" {
  rest_api_id = aws_api_gateway_rest_api.fitlog_api.id
  resource_id = aws_api_gateway_rest_api.fitlog_api.root_resource_id
  http_method = aws_api_gateway_method.root_method.http_method

  integration_http_method = "POST"
  type                   = "AWS_PROXY"
  uri                    = "arn:aws:apigateway:${data.aws_region.current.name}:lambda:path/2015-03-31/functions/${var.lambda_function_arn}/invocations"
}

# Proxy resource ({proxy+})
resource "aws_api_gateway_resource" "proxy_resource" {
  rest_api_id = aws_api_gateway_rest_api.fitlog_api.id
  parent_id   = aws_api_gateway_rest_api.fitlog_api.root_resource_id
  path_part   = "{proxy+}"
}

resource "aws_api_gateway_method" "proxy_method" {
  rest_api_id   = aws_api_gateway_rest_api.fitlog_api.id
  resource_id   = aws_api_gateway_resource.proxy_resource.id
  http_method   = "ANY"
  authorization = "NONE"
}

resource "aws_api_gateway_integration" "lambda_proxy" {
  rest_api_id = aws_api_gateway_rest_api.fitlog_api.id
  resource_id = aws_api_gateway_resource.proxy_resource.id
  http_method = aws_api_gateway_method.proxy_method.http_method

  integration_http_method = "POST"
  type                   = "AWS_PROXY"
  uri                    = "arn:aws:apigateway:${data.aws_region.current.name}:lambda:path/2015-03-31/functions/${var.lambda_function_arn}/invocations"
}

# Lambda permission for API Gateway
resource "aws_lambda_permission" "api_gateway" {
  statement_id  = "AllowExecutionFromAPIGateway"
  action        = "lambda:InvokeFunction"
  function_name = var.lambda_function_name
  principal     = "apigateway.amazonaws.com"

  # Allow execution from any stage and method
  source_arn = "${aws_api_gateway_rest_api.fitlog_api.execution_arn}/*/*"
}

# Stage configuration
resource "aws_api_gateway_stage" "fitlog_stage" {
  deployment_id = aws_api_gateway_deployment.fitlog_api.id
  rest_api_id   = aws_api_gateway_rest_api.fitlog_api.id
  stage_name    = var.environment

  tags = var.tags
}
