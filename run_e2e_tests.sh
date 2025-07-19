#!/bin/bash

# fitlog E2E Test Runner
# Usage: ./run_e2e_tests.sh [local|prod|custom-url]

set -e

# Activate virtual environment
source .venv/bin/activate

# Determine API URL
case "${1:-prod}" in
    "local")
        API_URL="http://localhost:8000"
        echo "🏠 Testing against LOCAL API: $API_URL"
        ;;
    "prod")
        API_URL="https://2054k0hh9j.execute-api.us-east-1.amazonaws.com/dev"
        echo "🚀 Testing against PRODUCTION API: $API_URL"
        ;;
    *)
        API_URL="$1"
        echo "🔗 Testing against CUSTOM API: $API_URL"
        ;;
esac

# Get API key from Terraform variables or environment
if [[ -z "$API_KEY" ]]; then
    if [[ -f "infrastructure/terraform.tfvars" ]]; then
        API_KEY=$(grep '^api_key' infrastructure/terraform.tfvars | cut -d'"' -f2)
        echo "📋 Using API key from terraform.tfvars"
    else
        echo "❌ API_KEY environment variable not set and terraform.tfvars not found"
        echo "💡 Set API_KEY environment variable or ensure terraform.tfvars contains api_key"
        exit 1
    fi
fi

# Check API health first
echo "🔍 Checking API health..."
if curl -s --max-time 10 "$API_URL/" > /dev/null 2>&1; then
    echo "✅ API is responding"
else
    echo "❌ API is not responding at $API_URL"
    exit 1
fi

# Run E2E tests
echo "🧪 Running E2E tests..."
API_BASE_URL="$API_URL" API_KEY="$API_KEY" uv run pytest tests/e2e/ -v -m e2e --tb=short

echo "✅ E2E tests completed!"
