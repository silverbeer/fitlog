# IAM Module for Fitlog
# Creates IAM roles and policies for Lambda execution

# Lambda execution role
resource "aws_iam_role" "lambda_role" {
  name = "${var.name_prefix}-lambda-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })

  tags = var.tags
}

# Lambda basic execution policy attachment
resource "aws_iam_role_policy_attachment" "lambda_basic_execution" {
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
  role       = aws_iam_role.lambda_role.name
}

# Custom policy for S3 access (DuckDB on S3)
resource "aws_iam_policy" "lambda_s3_policy" {
  name        = "${var.name_prefix}-lambda-s3-policy"
  description = "IAM policy for Lambda to access S3 bucket for DuckDB"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:DeleteObject",
          "s3:ListBucket"
        ]
        Resource = [
          var.s3_bucket_arn,
          "${var.s3_bucket_arn}/*"
        ]
      }
    ]
  })

  tags = var.tags
}

# Attach S3 policy to Lambda role
resource "aws_iam_role_policy_attachment" "lambda_s3_policy" {
  policy_arn = aws_iam_policy.lambda_s3_policy.arn
  role       = aws_iam_role.lambda_role.name
}

# CloudWatch Logs policy for enhanced logging
resource "aws_iam_policy" "lambda_logs_policy" {
  name        = "${var.name_prefix}-lambda-logs-policy"
  description = "IAM policy for Lambda CloudWatch Logs"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "arn:aws:logs:*:*:*"
      }
    ]
  })

  tags = var.tags
}

# Attach CloudWatch Logs policy to Lambda role
resource "aws_iam_role_policy_attachment" "lambda_logs_policy" {
  policy_arn = aws_iam_policy.lambda_logs_policy.arn
  role       = aws_iam_role.lambda_role.name
}
