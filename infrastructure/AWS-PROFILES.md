# 🔐 AWS Multi-Account Setup Guide

This guide helps you configure AWS profiles to ensure fitlog only uses your personal AWS account, never your work account.

## 🎯 **Why AWS Profiles?**

With multiple AWS accounts (work + personal), you need:
- **Isolation**: Prevent accidental deployments to wrong account
- **Security**: Clear separation of credentials and permissions  
- **Convenience**: Easy switching between accounts
- **Safety**: Built-in validation to catch mistakes

## 📋 **Step 1: Check Your Current AWS Configuration**

```bash
# Check current AWS configuration
aws sts get-caller-identity

# List configured profiles
aws configure list-profiles

# Check specific profile
aws sts get-caller-identity --profile personal
```

## 🔧 **Step 2: Configure AWS Profiles**

### **Option A: AWS CLI Configuration (Recommended)**

```bash
# Configure your personal profile
aws configure --profile personal
# AWS Access Key ID: [your personal access key]
# AWS Secret Access Key: [your personal secret key]  
# Default region name: us-east-1
# Default output format: json

# Configure your work profile (if needed)
aws configure --profile work
# AWS Access Key ID: [your work access key]
# AWS Secret Access Key: [your work secret key]
# Default region name: us-east-1  
# Default output format: json
```

### **Option B: Manual Configuration**

Edit `~/.aws/credentials`:
```ini
[personal]
aws_access_key_id = YOUR_PERSONAL_ACCESS_KEY
aws_secret_access_key = YOUR_PERSONAL_SECRET_KEY

[work]
aws_access_key_id = YOUR_WORK_ACCESS_KEY
aws_secret_access_key = YOUR_WORK_SECRET_KEY
```

Edit `~/.aws/config`:
```ini
[profile personal]
region = us-east-1
output = json

[profile work]
region = us-east-1
output = json
```

## 🎯 **Step 3: Get Your Personal Account ID**

```bash
# Get your personal AWS account ID
aws sts get-caller-identity --profile personal --query Account --output text
```

**Copy this account ID** - you'll need it for the next step.

## 🔒 **Step 4: Configure Fitlog for Personal Account**

### **Update Terraform Variables**

Edit `infrastructure/terraform.tfvars`:
```hcl
# AWS Configuration
aws_profile = "personal"  # Your personal profile name
aws_region  = "us-east-1"  # Your preferred region

# IMPORTANT: Replace with your actual personal account ID
expected_account_id = "123456789012"  # Your personal AWS account ID

# Environment
environment = "dev"  # or "prod"
```

### **Or Set Environment Variables**

```bash
# Add to your shell profile (~/.zshrc, ~/.bashrc, etc.)
export AWS_PROFILE=personal
export TF_VAR_aws_profile=personal
export TF_VAR_expected_account_id=123456789012  # Your account ID
```

## 🧪 **Step 5: Test Account Isolation**

### **Test Personal Account Access**
```bash
# Should show your personal account
aws sts get-caller-identity --profile personal

# Test with fitlog
cd infrastructure/bootstrap
terraform plan -var="aws_profile=personal" -var="expected_account_id=123456789012"
```

### **Test Work Account Rejection** (Optional)
```bash
# This should FAIL validation (if you have work profile configured)
terraform plan -var="aws_profile=work" -var="expected_account_id=123456789012"
# Expected: Account validation error
```

## 🚀 **Step 6: Bootstrap with Personal Account**

```bash
# Set profile for this session
export AWS_PROFILE=personal

# Run bootstrap (will use personal account)
cd infrastructure
./bootstrap.sh
```

## 🛡️ **Security Best Practices**

### **1. Use IAM Roles (Recommended)**

Instead of long-term access keys, use IAM roles with temporary credentials:

```ini
# ~/.aws/config
[profile personal]
region = us-east-1
role_arn = arn:aws:iam::123456789012:role/PersonalAdminRole
source_profile = personal-user

[profile personal-user]
region = us-east-1
```

### **2. Enable MFA**

```ini
# ~/.aws/config  
[profile personal]
region = us-east-1
mfa_serial = arn:aws:iam::123456789012:mfa/your-username
```

### **3. Least Privilege Access**

Create specific IAM policies for fitlog:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:*",
        "lambda:*",
        "apigateway:*",
        "iam:PassRole",
        "iam:CreateRole",
        "iam:AttachRolePolicy",
        "dynamodb:*",
        "logs:*"
      ],
      "Resource": [
        "arn:aws:s3:::fitlog-*",
        "arn:aws:lambda:*:*:function:fitlog-*",
        "arn:aws:iam::*:role/fitlog-*"
      ]
    }
  ]
}
```

## 🚨 **Common Issues & Solutions**

### **Wrong Account Error**
```
❌ ACCOUNT VALIDATION FAILED!
Expected account ID: 123456789012
Current account ID:  999999999999
```

**Solution**: Check your AWS profile
```bash
echo $AWS_PROFILE
aws sts get-caller-identity
```

### **Profile Not Found**
```
The config profile (personal) could not be found
```

**Solution**: Configure the profile
```bash
aws configure --profile personal
```

### **Permission Denied**
```
AccessDenied: User is not authorized to perform...
```

**Solution**: Check IAM permissions
```bash
aws iam get-user --profile personal
aws iam list-attached-user-policies --user-name your-username --profile personal
```

### **MFA Required**
```
Access denied (MFA required)
```

**Solution**: Get temporary credentials
```bash
aws sts get-session-token --serial-number arn:aws:iam::123456789012:mfa/username --token-code 123456
```

## 📝 **Profile Configuration Template**

Save this as `~/.aws/config`:
```ini
[profile personal]
region = us-east-1
output = json
# Uncomment if using MFA
# mfa_serial = arn:aws:iam::ACCOUNT-ID:mfa/USERNAME

[profile work]
region = us-east-1  
output = json
# Work account configuration
```

## 🔄 **Daily Workflow**

```bash
# Always verify which account you're using
aws sts get-caller-identity --profile personal

# Set profile for session
export AWS_PROFILE=personal

# Or specify in commands
terraform plan -var="aws_profile=personal"
```

## 🎯 **Validation Commands**

```bash
# Verify fitlog configuration
cd infrastructure
terraform plan | grep "Account ID"

# Check current profile
echo "Current profile: $AWS_PROFILE"
aws sts get-caller-identity --query Account --output text
```

---

**🔐 Remember**: Always double-check your AWS profile before running terraform commands. The account validation will catch most mistakes, but it's better to be explicit! 