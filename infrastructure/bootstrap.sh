#!/bin/bash

# Fitlog Terraform Bootstrap Script
# Creates S3 bucket and DynamoDB table for Terraform state management
# Run this before deploying main infrastructure

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
BOOTSTRAP_DIR="bootstrap"
AWS_PROFILE="${AWS_PROFILE:-personal}"  # Default to personal profile
AWS_REGION="${AWS_REGION:-us-east-1}"    # Default to us-east-1
EXPECTED_ACCOUNT_ID="${EXPECTED_ACCOUNT_ID:-}"  # Set this for validation
AUTO_APPROVE=false  # Default to interactive mode

echo -e "${BLUE}🚀 Fitlog Terraform Bootstrap${NC}"
echo -e "${BLUE}================================${NC}"
echo ""

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to validate AWS configuration
validate_aws_config() {
    echo -e "${BLUE}🔍 Validating AWS configuration...${NC}"
    
    # Check if AWS CLI is installed
    if ! command_exists aws; then
        echo -e "${RED}❌ AWS CLI is not installed${NC}"
        echo "Please install AWS CLI: https://docs.aws.amazon.com/cli/latest/userguide/install-cliv2.html"
        exit 1
    fi
    
    # Check if Terraform is installed
    if ! command_exists terraform; then
        echo -e "${RED}❌ Terraform is not installed${NC}"
        echo "Please install Terraform: https://www.terraform.io/downloads.html"
        exit 1
    fi
    
    # Check if profile exists
    if ! aws configure list --profile "$AWS_PROFILE" &>/dev/null; then
        echo -e "${RED}❌ AWS profile '$AWS_PROFILE' not found${NC}"
        echo "Please configure your AWS profile:"
        echo "  aws configure --profile $AWS_PROFILE"
        echo ""
        echo "Or see AWS-PROFILES.md for detailed setup instructions"
        exit 1
    fi
    
    # Get current account ID
    echo "Using AWS profile: $AWS_PROFILE"
    CURRENT_ACCOUNT_ID=$(aws sts get-caller-identity --profile "$AWS_PROFILE" --query Account --output text 2>/dev/null || echo "")
    
    if [ -z "$CURRENT_ACCOUNT_ID" ]; then
        echo -e "${RED}❌ Failed to get AWS account ID${NC}"
        echo "Please check your AWS credentials and permissions"
        exit 1
    fi
    
    echo "Current AWS Account ID: $CURRENT_ACCOUNT_ID"
    
    # Validate account ID if provided
    if [ -n "$EXPECTED_ACCOUNT_ID" ]; then
        if [ "$CURRENT_ACCOUNT_ID" != "$EXPECTED_ACCOUNT_ID" ]; then
            echo -e "${RED}❌ ACCOUNT VALIDATION FAILED!${NC}"
            echo "Expected account ID: $EXPECTED_ACCOUNT_ID"
            echo "Current account ID:  $CURRENT_ACCOUNT_ID"
            echo ""
            echo "This suggests you're using the wrong AWS profile."
            echo "Please check your configuration and try again."
            exit 1
        else
            echo -e "${GREEN}✅ Account validation passed${NC}"
        fi
    else
        echo -e "${YELLOW}⚠️  No account ID validation configured${NC}"
        echo "Consider setting EXPECTED_ACCOUNT_ID for additional safety"
        echo "Current account: $CURRENT_ACCOUNT_ID"
        echo ""
        
        if [ "$AUTO_APPROVE" = true ]; then
            echo "Auto-approve enabled, proceeding with account: $CURRENT_ACCOUNT_ID"
        else
            read -p "Continue with this account? (y/N): " -n 1 -r
            echo
            if [[ ! $REPLY =~ ^[Yy]$ ]]; then
                echo "Aborted by user"
                exit 1
            fi
        fi
    fi
    
    echo ""
}

# Function to run Terraform bootstrap
run_bootstrap() {
    echo -e "${BLUE}📦 Running Terraform bootstrap...${NC}"
    
    # Change to bootstrap directory
    cd "$BOOTSTRAP_DIR"
    
    # Initialize Terraform
    echo "Initializing Terraform..."
    terraform init
    
    # Plan with variables
    echo ""
    echo "Planning bootstrap infrastructure..."
    terraform plan \
        -var="aws_profile=$AWS_PROFILE" \
        -var="aws_region=$AWS_REGION" \
        ${EXPECTED_ACCOUNT_ID:+-var="expected_account_id=$EXPECTED_ACCOUNT_ID"} \
        -out=bootstrap.tfplan
    
    echo ""
    echo -e "${YELLOW}⚠️  About to create AWS resources:${NC}"
    echo "  - S3 bucket for Terraform state storage"
    echo "  - DynamoDB table for state locking"
    echo "  - Associated IAM policies and encryption"
    echo ""
    
    if [ "$AUTO_APPROVE" = true ]; then
        echo "Auto-approve enabled, proceeding with bootstrap..."
    else
        read -p "Continue with bootstrap? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            echo "Bootstrap cancelled by user"
            rm -f bootstrap.tfplan
            exit 1
        fi
    fi
    
    # Apply the plan
    echo ""
    echo "Applying bootstrap infrastructure..."
    terraform apply bootstrap.tfplan
    
    # Clean up plan file
    rm -f bootstrap.tfplan
    
    echo ""
    echo -e "${GREEN}✅ Bootstrap completed successfully!${NC}"
}

# Function to generate backend configuration
generate_backend_config() {
    echo -e "${BLUE}📝 Generating backend configuration...${NC}"
    
    # Get outputs from bootstrap
    STATE_BUCKET=$(terraform output -raw state_bucket_name)
    DYNAMODB_TABLE=$(terraform output -raw dynamodb_table_name)
    ACCOUNT_ID=$(terraform output -raw account_id)
    
    # Create backend configuration file
    cat > ../backend.hcl <<EOF
# Terraform Backend Configuration
# Generated by bootstrap.sh on $(date)
# Account ID: $ACCOUNT_ID

bucket         = "$STATE_BUCKET"
key            = "fitlog/terraform.tfstate"
region         = "$AWS_REGION"
dynamodb_table = "$DYNAMODB_TABLE"
encrypt        = true
profile        = "$AWS_PROFILE"
EOF
    
    # Create terraform.tfvars if it doesn't exist
    if [ ! -f "../terraform.tfvars" ]; then
        cat > ../terraform.tfvars <<EOF
# Fitlog Terraform Variables
# Generated by bootstrap.sh on $(date)

# AWS Configuration
aws_profile = "$AWS_PROFILE"
aws_region  = "$AWS_REGION"

# IMPORTANT: Update this with your actual personal account ID for validation
expected_account_id = "$ACCOUNT_ID"

# Environment Configuration
environment = "dev"
project_name = "fitlog"
EOF
        echo -e "${GREEN}✅ Created terraform.tfvars${NC}"
    fi
    
    echo ""
    echo -e "${GREEN}✅ Backend configuration saved to backend.hcl${NC}"
    echo ""
    echo -e "${BLUE}📋 Next steps:${NC}"
    echo "1. Review and customize terraform.tfvars if needed"
    echo "2. Initialize main Terraform configuration:"
    echo "   cd .."
    echo "   terraform init -backend-config=backend.hcl"
    echo "3. Plan and apply main infrastructure:"
    echo "   terraform plan"
    echo "   terraform apply"
    echo ""
    echo -e "${YELLOW}💡 Backend Configuration:${NC}"
    cat ../backend.hcl
}

# Main execution
main() {
    # Show current directory and configuration
    echo "Working directory: $(pwd)"
    echo "AWS Profile: $AWS_PROFILE"
    echo "AWS Region: $AWS_REGION"
    echo "Expected Account ID: ${EXPECTED_ACCOUNT_ID:-<not set>}"
    echo ""
    
    # Validate prerequisites
    validate_aws_config
    
    # Check if bootstrap directory exists
    if [ ! -d "$BOOTSTRAP_DIR" ]; then
        echo -e "${RED}❌ Bootstrap directory not found: $BOOTSTRAP_DIR${NC}"
        echo "Please run this script from the infrastructure directory"
        exit 1
    fi
    
    # Run bootstrap
    run_bootstrap
    
    # Generate backend configuration
    generate_backend_config
    
    echo -e "${GREEN}🎉 Bootstrap process completed successfully!${NC}"
    echo ""
    echo -e "${BLUE}📚 For more information:${NC}"
    echo "- Review AWS-PROFILES.md for multi-account setup"
    echo "- Check BOOTSTRAP.md for detailed documentation"
    echo "- Customize terraform.tfvars for your environment"
}

# Help function
show_help() {
    echo "Fitlog Terraform Bootstrap Script"
    echo ""
    echo "Usage: $0 [options]"
    echo ""
    echo "Options:"
    echo "  -h, --help          Show this help message"
    echo "  -p, --profile       AWS profile to use (default: personal)"
    echo "  -r, --region        AWS region (default: us-east-1)"
    echo "  -a, --account-id    Expected account ID for validation"
    echo "  -y, --yes           Auto-approve bootstrap (non-interactive)"
    echo ""
    echo "Environment Variables:"
    echo "  AWS_PROFILE         AWS profile to use"
    echo "  AWS_REGION          AWS region"
    echo "  EXPECTED_ACCOUNT_ID AWS account ID for validation"
    echo ""
    echo "Examples:"
    echo "  $0                                    # Use defaults (interactive)"
    echo "  $0 -p personal -r us-west-2          # Custom profile and region"
    echo "  $0 -a 123456789012 --yes             # With account validation (non-interactive)"
    echo "  $0 --yes                             # Auto-approve bootstrap"
    echo "  AWS_PROFILE=personal $0               # Using environment variable"
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            show_help
            exit 0
            ;;
        -p|--profile)
            AWS_PROFILE="$2"
            shift 2
            ;;
        -r|--region)
            AWS_REGION="$2"
            shift 2
            ;;
        -a|--account-id)
            EXPECTED_ACCOUNT_ID="$2"
            shift 2
            ;;
        -y|--yes)
            AUTO_APPROVE=true
            shift
            ;;
        *)
            echo -e "${RED}❌ Unknown option: $1${NC}"
            echo "Use -h or --help for usage information"
            exit 1
            ;;
    esac
done

# Run main function
main 