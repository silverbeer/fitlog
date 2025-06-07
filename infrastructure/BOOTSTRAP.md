# 🏗️ Terraform Bootstrap Guide

This guide explains how to set up Terraform state management for the fitlog cloud infrastructure.

## 🎯 **Why Bootstrap?**

Terraform needs somewhere to store its state file. For production use, we want:
- **S3 storage**: Durable, versioned, encrypted
- **DynamoDB locking**: Prevents concurrent modifications
- **Team collaboration**: Shared state accessible to all developers

But there's a "chicken and egg" problem: we need Terraform to create these resources, but Terraform needs them to store state!

## 🚀 **Bootstrap Solution**

We solve this with a **two-stage approach**:

1. **Bootstrap stage**: Creates S3 + DynamoDB with local state
2. **Main stage**: Uses the S3 + DynamoDB for remote state

## 📋 **Prerequisites**

- **AWS CLI** configured with appropriate permissions
- **Terraform >= 1.0** installed
- **AWS Profile**: Personal account profile configured (see `AWS-PROFILES.md`)
- **Permissions**: AWS credentials with permissions to create:
  - S3 buckets
  - DynamoDB tables
  - IAM roles (for main infrastructure)

### **Multi-Account Setup**
If you have multiple AWS accounts (work/personal), see the comprehensive guide:
```bash
# View detailed multi-account setup
cat AWS-PROFILES.md
```

### **Required AWS Permissions**

Your AWS user/role needs these permissions:
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:CreateBucket",
        "s3:GetBucketVersioning",
        "s3:PutBucketVersioning",
        "s3:PutBucketEncryption",
        "s3:PutBucketPublicAccessBlock",
        "s3:GetBucketLocation",
        "dynamodb:CreateTable",
        "dynamodb:DescribeTable",
        "dynamodb:GetItem",
        "dynamodb:PutItem",
        "dynamodb:DeleteItem"
      ],
      "Resource": "*"
    }
  ]
}
```

## 🏃‍♀️ **Quick Start**

### **Step 1: Configure AWS Profile**
```bash
# Set up your personal AWS profile (prevents accidental work account usage)
aws configure --profile personal

# Get your account ID (you'll need this)
aws sts get-caller-identity --profile personal --query Account --output text
```

### **Step 2: Run Bootstrap Script (Recommended)**

```bash
# From the infrastructure directory
export AWS_PROFILE=personal
export EXPECTED_ACCOUNT_ID=123456789012  # Your actual account ID
./bootstrap.sh
```

**Alternative: Command line options**
```bash
# Specify profile and validation directly
./bootstrap.sh --profile personal --account-id 123456789012

# See all available options
./bootstrap.sh --help
```

The script will:
1. **Validate AWS account and profile** (prevents wrong account deployment)
2. Check AWS CLI and Terraform installation
3. Initialize bootstrap Terraform
4. Create S3 bucket and DynamoDB table
5. Generate `backend.hcl` and `terraform.tfvars` configuration files

### **Option 2: Manual Steps**

```bash
# 1. Bootstrap the state infrastructure
cd infrastructure/bootstrap
terraform init
terraform plan
terraform apply

# 2. Get the outputs
terraform output

# 3. Configure main infrastructure backend
cd ..
terraform init -backend-config=backend.hcl
```

## 📦 **What Gets Created**

### **S3 Bucket for State Storage**
- **Name**: `fitlog-terraform-state-bucket-{account-id}`
- **Versioning**: Enabled (essential for state recovery)
- **Encryption**: AES256 server-side encryption
- **Public Access**: Blocked (security)
- **Lifecycle**: Prevent destruction

### **DynamoDB Table for State Locking**
- **Name**: `fitlog-terraform-state-lock`
- **Billing**: Pay-per-request (cost-effective for personal use)
- **Key**: `LockID` (required by Terraform)
- **Features**: Point-in-time recovery enabled

## 💰 **Cost Considerations**

### **S3 Costs**
- **Storage**: ~$0.023/GB/month (minimal for state files)
- **Requests**: ~$0.0004 per 1000 requests
- **Versioning**: Old versions accumulate (set lifecycle rules if needed)

### **DynamoDB Costs**
- **Pay-per-request**: ~$1.25 per million requests
- **Storage**: ~$0.25/GB/month
- **For personal use**: Expect < $1/month total

## 🔒 **Security Features**

- ✅ **S3 bucket encryption** at rest
- ✅ **Public access blocked** on state bucket
- ✅ **DynamoDB encryption** at rest
- ✅ **State file versioning** for recovery
- ✅ **Deletion protection** on state resources

## 🛠️ **Troubleshooting**

### **Permission Errors**
```bash
# Check AWS configuration
aws sts get-caller-identity
aws iam get-user  # or get-role
```

### **Bucket Name Conflicts**
The script uses your AWS account ID to make bucket names unique. If you still get conflicts, edit the `state_bucket_name` variable in `bootstrap/main.tf`.

### **State Lock Issues**
```bash
# If DynamoDB table gets stuck
aws dynamodb delete-item \
  --table-name fitlog-terraform-state-lock \
  --key '{"LockID":{"S":"path/to/lock"}}'
```

### **Starting Over**
```bash
# Delete everything and start fresh
cd bootstrap
terraform destroy
cd ..
rm -f backend.hcl
```

## 📝 **Files Created**

- `bootstrap/terraform.tfstate` - Bootstrap state (local)
- `backend.hcl` - Backend configuration for main infrastructure
- S3 bucket with your state files
- DynamoDB table for locking

## 🔄 **After Bootstrap**

Once bootstrap is complete:

1. **Main infrastructure** uses remote state in S3
2. **State is locked** during operations
3. **Team members** can collaborate safely
4. **State is versioned** and recoverable

### **Normal Workflow**
```bash
# Main infrastructure operations
cd infrastructure
terraform plan
terraform apply
terraform destroy  # when needed
```

## 🚨 **Important Notes**

- **Don't delete** the bootstrap resources while main infrastructure exists
- **Backup** the bootstrap state file (`bootstrap/terraform.tfstate`)
- **Consider** enabling MFA delete on the state bucket for production
- **Monitor** AWS costs, especially if you have many state operations

---

*This bootstrap process follows AWS and Terraform best practices for secure, collaborative infrastructure management.*
