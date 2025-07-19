#!/bin/bash

# Fitlog Infrastructure Deployment Script
# Handles secure deployment with environment variables

set -e

echo "🚀 Fitlog Infrastructure Deployment"
echo "=================================="

# Check for required environment variables
if [[ -z "$TF_VAR_api_key" ]]; then
    echo ""
    echo "❌ TF_VAR_api_key environment variable is required!"
    echo ""
    echo "💡 Generate a secure API key and set it:"
    echo "   export TF_VAR_api_key=\"fitlog_\$(openssl rand -base64 32 | tr -d '/+=')\" "
    echo ""
    echo "   Or use the one from your previous setup:"
    echo "   export TF_VAR_api_key=\"fitlog_z-e8yE_lWLIZAkRcKy6AVW5ZaJJ3qmaGS5eFVZjtnHw\""
    echo ""
    exit 1
fi

# Check if terraform.tfvars exists
if [[ ! -f "terraform.tfvars" ]]; then
    echo "📋 Creating terraform.tfvars from example..."
    cp terraform.tfvars.example terraform.tfvars
    echo "✅ Please review and update terraform.tfvars if needed"
fi

# Initialize Terraform if needed
if [[ ! -d ".terraform" ]]; then
    echo "🔧 Initializing Terraform..."
    terraform init -backend-config=backend.hcl
fi

# Plan deployment
echo "📋 Planning deployment..."
terraform plan

# Confirm deployment
echo ""
read -p "🚀 Deploy changes? (y/N): " -n 1 -r
echo ""

if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "🚀 Applying changes..."
    terraform apply -auto-approve

    echo ""
    echo "✅ Deployment complete!"
    echo ""
    echo "🔗 API Endpoint: $(terraform output -raw api_endpoint)"
    echo "📦 Lambda Function: $(terraform output -raw lambda_function_name)"
    echo "🪣 S3 Bucket: $(terraform output -raw s3_bucket_name)"
    echo ""
    echo "🔑 Your API key is: $TF_VAR_api_key"
    echo "   Keep this secret and use it for API requests!"
    echo ""
else
    echo "❌ Deployment cancelled"
    exit 1
fi
