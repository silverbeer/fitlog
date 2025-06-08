# 🔐 Fitlog API Authentication Setup

The Fitlog API uses API key authentication to protect your personal fitness data.

## 🔑 API Key Management

### For Local Development

1. **Generate a secure API key:**
   ```bash
   export TF_VAR_api_key="fitlog_$(openssl rand -base64 32 | tr -d '/+=')"
   echo "Your API key: $TF_VAR_api_key"
   ```

2. **Or use the existing key:**
   ```bash
   export TF_VAR_api_key="fitlog_z-e8yE_lWLIZAkRcKy6AVW5ZaJJ3qmaGS5eFVZjtnHw"
   ```

3. **Deploy infrastructure:**
   ```bash
   cd infrastructure
   ./deploy.sh
   ```

### For GitHub Actions (CI/CD)

Set up the API key as a GitHub secret:

1. Go to your repository settings
2. Navigate to **Secrets and Variables** → **Actions**
3. Add a new repository secret:
   - **Name**: `API_KEY`
   - **Value**: `fitlog_z-e8yE_lWLIZAkRcKy6AVW5ZaJJ3qmaGS5eFVZjtnHw`

## 🧪 Testing with Authentication

### E2E Tests
```bash
# Set the API key for testing
export API_KEY="fitlog_z-e8yE_lWLIZAkRcKy6AVW5ZaJJ3qmaGS5eFVZjtnHw"

# Run E2E tests
./run_e2e_tests.sh prod
```

### Manual API Testing
```bash
# Example API request with authentication
curl -H "X-API-Key: fitlog_z-e8yE_lWLIZAkRcKy6AVW5ZaJJ3qmaGS5eFVZjtnHw" \
     https://2054k0hh9j.execute-api.us-east-1.amazonaws.com/dev/runs
```

## 🔒 Security Best Practices

### ✅ What we do:
- API key stored as environment variable (not in git)
- GitHub secrets for CI/CD
- terraform.tfvars is git-ignored
- Separate clients for authenticated/unauthenticated endpoints

### ❌ What we avoid:
- Never commit API keys to git
- Never log API keys in plain text
- Never share API keys in chat/email

## 🌐 Public vs Protected Endpoints

### Public Endpoints (No API key required):
- `GET /` - Health check

### Protected Endpoints (API key required):
- `GET /runs` - List runs
- `POST /runs` - Create run
- `GET /pushups` - List pushups
- `POST /pushups` - Create pushup
- `GET /activities/status` - Activity statistics
- `GET /test` - Test endpoint

## 🚨 If API Key is Compromised

1. **Generate a new key:**
   ```bash
   export TF_VAR_api_key="fitlog_$(openssl rand -base64 32 | tr -d '/+=')"
   ```

2. **Update infrastructure:**
   ```bash
   cd infrastructure
   ./deploy.sh
   ```

3. **Update GitHub secret** with new key

4. **Update local environment** and any scripts using the old key

## 🔄 Rotating API Keys

For production systems, consider rotating API keys regularly:
- Monthly rotation recommended
- Use AWS Secrets Manager for automatic rotation
- Update all clients when rotating

---

> 💡 **Tip**: Save your API key securely in a password manager and never share it publicly!
