# Lambda Module for Fitlog
# Creates Lambda function for the FastAPI application

# Lambda function
resource "aws_lambda_function" "fitlog_api" {
  filename         = var.lambda_zip_path
  function_name    = var.function_name
  role            = var.lambda_role_arn
  handler         = "main.handler"
  runtime         = "python3.13"
  timeout         = 30
  memory_size     = 512

  # AWS Lambda Powertools layer for observability
  layers = [
    "arn:aws:lambda:us-east-1:017000801446:layer:AWSLambdaPowertoolsPythonV3-python313-x86_64:1"
  ]

  environment {
    variables = {
      ENVIRONMENT = var.environment
      S3_BUCKET   = var.s3_bucket
      DUCKDB_PATH = "s3://${var.s3_bucket}/fitlog.db"
      API_KEY     = var.api_key
    }
  }

  depends_on = [
    aws_cloudwatch_log_group.lambda_logs,
  ]

  tags = var.tags
}

# CloudWatch Log Group
resource "aws_cloudwatch_log_group" "lambda_logs" {
  name              = "/aws/lambda/${var.function_name}"
  retention_in_days = 30

  tags = var.tags
}

# Lambda function URL (for direct HTTP access)
resource "aws_lambda_function_url" "fitlog_api" {
  function_name      = aws_lambda_function.fitlog_api.function_name
  authorization_type = "NONE"

  cors {
    allow_credentials = false
    allow_headers     = ["date", "keep-alive"]
    allow_methods     = ["*"]
    allow_origins     = ["*"]
    expose_headers    = ["date", "keep-alive"]
    max_age          = 86400
  }
}

# Create a placeholder zip file if one doesn't exist
resource "null_resource" "lambda_zip" {
  count = var.create_placeholder_zip ? 1 : 0

  provisioner "local-exec" {
    command = <<EOF
mkdir -p ${dirname(var.lambda_zip_path)}
cat > ${dirname(var.lambda_zip_path)}/main.py << 'PYTHON'
import json

def handler(event, context):
    """Placeholder Lambda function"""
    return {
        'statusCode': 200,
        'headers': {
            'Content-Type': 'application/json',
        },
        'body': json.dumps({
            'message': 'Fitlog API placeholder - deploy your FastAPI code here',
            'event': event
        })
    }
PYTHON

cd ${dirname(var.lambda_zip_path)}
zip ${basename(var.lambda_zip_path)} main.py
EOF
  }

  triggers = {
    always_run = timestamp()
  }
}
