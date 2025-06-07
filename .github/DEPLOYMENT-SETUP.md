# 🚀 GitHub Actions Deployment Setup

This guide walks you through setting up automated deployments for your fitlog infrastructure and application code.

## 🎯 **Overview**

We have two GitHub Actions workflows:

| Workflow | Trigger | Purpose |
|----------|---------|---------|
| **`deploy.yml`** | Code changes (`api/`, `fitlog/`) | Deploy FastAPI to Lambda |
| **`infrastructure.yml`** | Infrastructure changes | Deploy Terraform changes |

## 🔐 **Step 1: Configure GitHub Secrets**

### **Required Secrets**

Go to your GitHub repository → **Settings** → **Secrets and variables** → **Actions** → **New repository secret**

| Secret Name | Value | Description |
|-------------|-------|-------------|
| `AWS_ACCESS_KEY_ID` | Your AWS access key | Personal AWS account access key |
| `AWS_SECRET_ACCESS_KEY` | Your AWS secret key | Personal AWS account secret key |
| `AWS_ACCOUNT_ID` | `332089435055` | Your personal AWS account ID |

### **Getting AWS Credentials**

#### **Option A: Use Existing Credentials**
If you already have AWS credentials for your personal account:

```bash
# Check your current credentials
cat ~/.aws/credentials

# Look for your personal profile section:
[personal]
aws_access_key_id = AKIA...
aws_secret_access_key = xxxxx...
```

#### **Option B: Create Deployment-Specific User (Recommended)**

1. **Create IAM User for GitHub Actions**:
   ```bash
   aws iam create-user --user-name github-actions-fitlog --profile personal
   ```

2. **Attach Required Policies**:
   ```bash
   # Lambda and API Gateway permissions
   aws iam attach-user-policy \
     --user-name github-actions-fitlog \
     --policy-arn arn:aws:iam::aws:policy/AWSLambdaFullAccess \
     --profile personal

   # API Gateway permissions
   aws iam attach-user-policy \
     --user-name github-actions-fitlog \
     --policy-arn arn:aws:iam::aws:policy/AmazonAPIGatewayAdministrator \
     --profile personal

   # S3 and DynamoDB for Terraform state
   aws iam attach-user-policy \
     --user-name github-actions-fitlog \
     --policy-arn arn:aws:iam::aws:policy/AmazonS3FullAccess \
     --profile personal

   aws iam attach-user-policy \
     --user-name github-actions-fitlog \
     --policy-arn arn:aws:iam::aws:policy/AmazonDynamoDBFullAccess \
     --profile personal
   ```

3. **Create Access Keys**:
   ```bash
   aws iam create-access-key --user-name github-actions-fitlog --profile personal
   ```

   Save the `AccessKeyId` and `SecretAccessKey` for GitHub secrets.

## 🏗️ **Step 2: Update pyproject.toml**

Your `pyproject.toml` already has the cloud dependencies configured:

```toml
[project.optional-dependencies]
cloud = [
    "fastapi>=0.104.0",
    "uvicorn[standard]>=0.24.0",
    "boto3>=1.34.0",
    "aioboto3>=12.0.0",
    "mangum>=0.17.0",  # Lambda ASGI adapter
]
```

✅ **No changes needed** - your dependencies are already configured!

## 📁 **Step 3: Create FastAPI Application Structure**

Create the FastAPI application that will replace the placeholder:

```bash
# Create API directory
mkdir -p api

# Create main FastAPI application
cat > api/main.py << 'EOF'
import os
from fastapi import FastAPI
from mangum import Mangum

# Import your fitlog modules
from fitlog.models import Run, Pushup
from fitlog.db import get_db_connection

app = FastAPI(
    title="Fitlog API",
    description="Personal exercise tracking API",
    version="2.0.0"
)

@app.get("/")
async def health_check():
    return {
        "message": "Fitlog API v2.0.0",
        "status": "healthy",
        "environment": os.getenv("ENVIRONMENT", "unknown"),
        "s3_bucket": os.getenv("S3_BUCKET", "unknown")
    }

@app.get("/runs")
async def get_runs():
    # TODO: Implement with DuckDB S3 connection
    return {"message": "Get runs endpoint - implement with DuckDB S3"}

@app.post("/runs")
async def create_run(run_data: dict):
    # TODO: Implement with DuckDB S3 connection
    return {"message": "Create run endpoint - implement with DuckDB S3", "data": run_data}

# Lambda handler
handler = Mangum(app)
EOF
```

## 🧪 **Step 4: Test Locally First**

Before pushing to GitHub, test the workflow components locally:

```bash
# Test FastAPI application
cd api
uvicorn main:app --reload

# Test packaging
mkdir -p test-deploy
cp -r ../fitlog test-deploy/
pip install fastapi uvicorn mangum duckdb boto3 --target test-deploy/
cd test-deploy && zip -r ../test-package.zip .
```

## 🚀 **Step 5: Trigger First Deployment**

### **Deploy Application Code**

1. **Commit and push your FastAPI code**:
   ```bash
   git add api/ .github/
   git commit -m "Add FastAPI application and GitHub Actions workflows"
   git push origin feature/v2-cloud-migration
   ```

2. **The GitHub Action will**:
   - ✅ Run tests and linting
   - ✅ Package your FastAPI app with dependencies
   - ✅ Deploy to AWS Lambda
   - ✅ Test the deployment

### **Deploy Infrastructure Changes**

1. **Commit infrastructure changes**:
   ```bash
   git add infrastructure/
   git commit -m "Update Terraform configuration"
   git push origin feature/v2-cloud-migration
   ```

2. **The GitHub Action will**:
   - ✅ Run `terraform plan`
   - ✅ Run security scans
   - ✅ Apply changes (only on main branch)

## 📊 **Step 6: Monitor Deployments**

### **GitHub Actions Dashboard**
- Go to **Actions** tab in your GitHub repository
- Monitor workflow runs and logs
- Check deployment status and errors

### **AWS CloudWatch Logs**
- Monitor Lambda function logs: `/aws/lambda/fitlog-dev-api`
- Check API Gateway access logs
- Monitor application errors and performance

## 🔄 **Daily Workflow**

Once set up, your deployment workflow becomes:

```bash
# 1. Make code changes
vim fitlog/api.py

# 2. Commit and push
git add .
git commit -m "Add new endpoint for activity status"
git push origin feature/v2-cloud-migration

# 3. GitHub Actions automatically:
#    - Tests your code
#    - Deploys to Lambda
#    - Reports success/failure

# 4. Test your changes
curl https://2054k0hh9j.execute-api.us-east-1.amazonaws.com/dev
```

## 🛡️ **Security Best Practices**

### **Environment Protection (Optional)**

Add deployment protection in GitHub:

1. Go to **Settings** → **Environments** → **New environment**
2. Name: `production`
3. Add protection rules:
   - ✅ Required reviewers
   - ✅ Wait timer
   - ✅ Branch restrictions

### **Least Privilege IAM**

Create a custom IAM policy instead of using AWS managed policies:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "lambda:UpdateFunctionCode",
        "lambda:GetFunction",
        "lambda:GetFunctionConfiguration",
        "apigateway:GET",
        "s3:GetObject",
        "s3:PutObject",
        "dynamodb:GetItem",
        "dynamodb:PutItem"
      ],
      "Resource": [
        "arn:aws:lambda:us-east-1:332089435055:function:fitlog-*",
        "arn:aws:apigateway:us-east-1::*",
        "arn:aws:s3:::fitlog-*/*",
        "arn:aws:dynamodb:us-east-1:332089435055:table/fitlog-*"
      ]
    }
  ]
}
```

## 🆘 **Troubleshooting**

### **Common Issues**

1. **AWS Credentials Error**:
   ```
   Error: InvalidAccessKeyId
   ```
   **Solution**: Check GitHub secrets are correctly set

2. **Terraform Backend Error**:
   ```
   Error: Failed to get existing workspaces
   ```
   **Solution**: Ensure S3 bucket and DynamoDB table exist from bootstrap

3. **Lambda Package Too Large**:
   ```
   Error: Unzipped size must be smaller than 262144000 bytes
   ```
   **Solution**: Optimize dependencies, use Lambda layers

### **Debug Commands**

```bash
# Check GitHub Actions logs
gh run list
gh run view [run-id]

# Test AWS credentials locally
aws sts get-caller-identity --profile personal

# Test Lambda function
aws lambda invoke --function-name fitlog-dev-api response.json
```

---

🎉 **Your automated deployment pipeline is ready!** Every code push will now trigger automated testing and deployment to AWS.

## 📚 **Next Steps**

1. **Set up monitoring**: CloudWatch dashboards and alerts
2. **Add integration tests**: Test API endpoints after deployment
3. **Implement blue/green deployments**: Zero-downtime deployments
4. **Add staging environment**: Test changes before production
