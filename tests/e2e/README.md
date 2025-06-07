# 🧪 End-to-End Tests

This directory contains end-to-end (E2E) tests that verify the deployed Fitlog API is working correctly in the cloud environment.

## 📋 Overview

The E2E tests run against the actual deployed Lambda function via API Gateway to ensure:
- All endpoints are responding correctly
- Data validation is working
- Error handling is functioning
- Performance is acceptable
- The Lambda environment is configured properly

## 🚀 Running Tests

### Automated (GitHub Actions)
E2E tests run automatically after every successful deployment via GitHub Actions.

### Manual Testing

#### 1. Quick Smoke Test
```bash
# Test using API ID and region
python tests/e2e/run_e2e_tests.py --api-id 2054k0hh9j --region us-east-1 --smoke-only

# Test using full URL  
python tests/e2e/run_e2e_tests.py --api-url https://2054k0hh9j.execute-api.us-east-1.amazonaws.com/dev --smoke-only
```

#### 2. Full Test Suite
```bash
# Comprehensive E2E testing
python tests/e2e/run_e2e_tests.py --api-id 2054k0hh9j --region us-east-1 --verbose

# With custom timeout
python tests/e2e/run_e2e_tests.py --api-url https://api.example.com/dev --timeout 60 --verbose
```

#### 3. Using pytest directly
```bash
# Set API URL and run pytest
export API_BASE_URL="https://2054k0hh9j.execute-api.us-east-1.amazonaws.com/dev"
pytest tests/e2e/test_api_endpoints.py -v -m e2e
```

## 🧩 Test Categories

### Health & Status Tests
- `test_health_check_endpoint()` - Verifies health endpoint and environment variables
- `test_test_endpoint()` - Validates GitHub Actions test endpoint

### API Endpoint Tests  
- `test_get_runs_endpoint()` - Tests GET /runs
- `test_create_run_endpoint()` - Tests POST /runs with data
- `test_create_run_without_date()` - Tests POST /runs with default date
- `test_get_pushups_endpoint()` - Tests GET /pushups
- `test_create_pushup_endpoint()` - Tests POST /pushups with data
- `test_create_pushup_without_date()` - Tests POST /pushups with default date
- `test_activity_status_endpoint()` - Tests GET /activities/status

### Error Handling Tests
- `test_invalid_endpoint()` - Tests 404 for non-existent endpoints
- `test_invalid_run_data()` - Tests validation errors for runs
- `test_invalid_pushup_data()` - Tests validation errors for pushups

### Performance Tests
- `test_health_check_response_time()` - Ensures health check responds < 5s
- `test_multiple_concurrent_requests()` - Tests concurrent request handling

## 📊 Expected Responses

### Health Check (`GET /`)
```json
{
    "message": "🏃‍♂️ Fitlog API v2.0.0 - Cloud Edition",
    "status": "healthy", 
    "environment": "dev",
    "s3_bucket": "fitlog-dev-data",
    "lambda_function": "fitlog-dev-api",
    "timestamp": "2025-01-06T10:30:00Z"
}
```

### Runs (`GET /runs`)
```json
{
    "message": "Get runs endpoint - ready for DuckDB S3 implementation",
    "data": [],
    "todo": ["Connect to DuckDB on S3", "Query runs from cloud database"]
}
```

### Create Run (`POST /runs`)
```json
{
    "message": "Create run endpoint - ready for DuckDB S3 implementation",
    "received_data": {
        "duration": "30:15:00",
        "distance": 3.2,
        "date": "06/07/25"
    },
    "todo": ["Validate run data", "Store in DuckDB on S3"]
}
```

## 🔧 Configuration

### Environment Variables
- `API_BASE_URL` - Base URL for the deployed API (required for pytest)

### Command Line Options
- `--api-url` - Full API Gateway URL
- `--api-id` - API Gateway ID (used with `--region`)
- `--region` - AWS region (default: us-east-1)
- `--stage` - API Gateway stage (default: dev)
- `--smoke-only` - Run only quick smoke test
- `--skip-availability-check` - Skip initial API availability check
- `--verbose` - Verbose output
- `--timeout` - Timeout for availability check (default: 30s)

## 🚨 Troubleshooting

### API Not Available
```
❌ API not available: Connection timeout
```
**Solution:** Check if the Lambda function is deployed and API Gateway is configured correctly.

### Tests Failing After Deployment
```
💥 E2E tests FAILED! Check the output above for details.
```
**Solution:** Check the specific test failures. Common issues:
- Lambda environment variables not set correctly
- API Gateway integration issues
- Lambda function timeout or memory issues

### Permission Errors
```
❌ Could not find API Gateway: Access denied
```
**Solution:** Ensure AWS credentials have permission to access API Gateway.

## 📈 GitHub Actions Integration

The E2E tests are automatically run in GitHub Actions after successful deployment:

1. **Deploy Job** - Deploys the Lambda function
2. **E2E Tests Job** - Runs comprehensive E2E tests
   - Discovers API Gateway URL
   - Waits for API to be ready
   - Runs smoke test first
   - Runs full test suite
   - Reports results

## 🔮 Future Improvements

- [ ] Add performance benchmarking
- [ ] Test data persistence after DuckDB S3 implementation  
- [ ] Add load testing scenarios
- [ ] Test error scenarios (S3 unavailable, etc.)
- [ ] Add metrics collection during testing
- [ ] Test authentication when added 