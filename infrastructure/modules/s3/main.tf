# S3 module for fitlog DuckDB storage

# S3 bucket for DuckDB data storage
resource "aws_s3_bucket" "fitlog_data" {
  bucket = var.bucket_name

  tags = merge(var.tags, {
    Name = var.bucket_name
    Purpose = "DuckDB data storage"
  })
}

# S3 bucket versioning
resource "aws_s3_bucket_versioning" "fitlog_data" {
  bucket = aws_s3_bucket.fitlog_data.id
  versioning_configuration {
    status = "Enabled"
  }
}

# S3 bucket server-side encryption
resource "aws_s3_bucket_server_side_encryption_configuration" "fitlog_data" {
  bucket = aws_s3_bucket.fitlog_data.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

# S3 bucket public access block (security)
resource "aws_s3_bucket_public_access_block" "fitlog_data" {
  bucket = aws_s3_bucket.fitlog_data.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# S3 bucket lifecycle configuration for cost optimization
resource "aws_s3_bucket_lifecycle_configuration" "fitlog_data" {
  bucket = aws_s3_bucket.fitlog_data.id

  rule {
    id     = "fitlog_lifecycle"
    status = "Enabled"

    # Apply to all objects (empty filter means all objects)
    filter {}

    # Transition older data to cheaper storage classes
    transition {
      days          = 30
      storage_class = "STANDARD_IA"
    }

    transition {
      days          = 90
      storage_class = "GLACIER"
    }

    # Keep data for 7 years (personal fitness tracking)
    expiration {
      days = 2555  # ~7 years
    }

    # Clean up incomplete multipart uploads
    abort_incomplete_multipart_upload {
      days_after_initiation = 7
    }
  }
}

# Create initial folder structure for DuckDB partitioning
resource "aws_s3_object" "runs_folder" {
  bucket = aws_s3_bucket.fitlog_data.id
  key    = "runs/"
  content_type = "application/x-directory"
}

resource "aws_s3_object" "pushups_folder" {
  bucket = aws_s3_bucket.fitlog_data.id
  key    = "pushups/"
  content_type = "application/x-directory"
}

resource "aws_s3_object" "metadata_folder" {
  bucket = aws_s3_bucket.fitlog_data.id
  key    = "metadata/"
  content_type = "application/x-directory"
}
