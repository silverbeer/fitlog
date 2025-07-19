# 🚀 Fitlog V2 Cloud Development

This branch contains the V2 cloud migration for fitlog, transforming the local CLI into a serverless AWS-based solution.

## 📋 **Current Status**

### ✅ **Completed**
- [x] Feature branch created (`feature/v2-cloud-migration`)
- [x] FastAPI application structure
- [x] REST API endpoints matching CLI commands
- [x] Terraform infrastructure modules (S3)
- [x] Updated pyproject.toml with cloud dependencies

### 🚧 **In Progress**
- [ ] DuckDB S3 integration
- [ ] Complete Terraform modules (IAM, Lambda, API Gateway)
- [ ] Cloud database implementation
- [ ] CLI client modifications for cloud mode

### 📂 **New Structure**

```
fitlog/
├── api/                          # 🆕 FastAPI backend
│   ├── main.py                   # Main FastAPI app
│   ├── routers/                  # API endpoints
│   │   ├── runs.py              # Runs management
│   │   ├── pushups.py           # Pushups management
│   │   └── activities.py        # Status/reports
├── infrastructure/               # 🆕 Terraform IaC
│   ├── main.tf                  # Main configuration
│   └── modules/
│       ├── s3/                  # DuckDB storage
│       ├── lambda/              # Function deployment
│       ├── api-gateway/         # REST API
│       └── iam/                 # Permissions
├── migration/                    # 🆕 Data migration tools
├── fitlog/                      # 📝 Updated CLI (V1 + cloud support)
└── tests/                       # 📝 Updated tests
```

---

## 🎯 **V2 Goals**

### **API Endpoints** (FastAPI)
```
GET  /                           # API info
GET  /health                     # Health check
POST /runs                       # Log run
GET  /runs                       # Get runs
POST /pushups                    # Log pushups
GET  /pushups                    # Get pushups
GET  /activities/status          # Activity status
GET  /activities/report          # Generate report
POST /activities/import/smashrun # Import from Smashrun
```

### **Infrastructure** (AWS Serverless)
- **S3**: DuckDB storage with partitioned Parquet files
- **Lambda**: FastAPI app with Python 3.13
- **API Gateway**: REST endpoints with authentication
- **IAM**: Least-privilege access policies

### **DuckDB S3 Strategy**
- Direct S3 operations using DuckDB extensions
- Partitioned storage: `s3://bucket/runs/year=2025/month=06/day=07/`
- No file downloads - query S3 directly

---

## 🛠️ **Development Setup**

### **Install Cloud Dependencies**
```bash
# Install FastAPI and AWS tools
uv pip install -e ".[cloud]"

# Verify FastAPI setup
cd api
python main.py  # Starts dev server on localhost:8000
```

### **Test API Locally**
```bash
# Start FastAPI development server
uvicorn api.main:app --reload --port 8000

# Visit API documentation
open http://localhost:8000/docs
```

### **Terraform Setup** (Not yet functional)
```bash
cd infrastructure
terraform init
terraform plan
# terraform apply  # When ready
```

---

## 🔄 **Migration Strategy**

### **Phase 1: API Development** (Current)
- ✅ FastAPI structure with placeholder endpoints
- ✅ Terraform infrastructure modules
- 🚧 DuckDB S3 integration
- 🚧 Complete infrastructure deployment

### **Phase 2: Data Migration**
- Local DuckDB → S3 Parquet conversion
- Data validation and integrity checks
- Backup and rollback procedures

### **Phase 3: Hybrid CLI**
- CLI configuration for local/cloud/hybrid modes
- Cloud client implementation
- Fallback to local storage

### **Phase 4: Production**
- AWS deployment via GitHub Actions
- Monitoring and alerting
- Cost optimization

---

## 🧪 **Testing V2**

### **Local API Testing**
```bash
# Start the API
uvicorn api.main:app --reload

# Test health endpoint
curl http://localhost:8000/health

# Test API documentation
open http://localhost:8000/docs
```

### **CLI Integration** (Future)
```bash
# Configure cloud mode
fitlog config set mode cloud
fitlog config set api_url https://api.fitlog.com

# Test cloud operations
fitlog log-run --duration "30:00:00" --distance 3.5  # → API call
fitlog status                                        # → API call
```

---

## 📚 **Architecture Decisions**

1. **FastAPI over Flask**: Better async support, automatic API docs
2. **DuckDB S3 Extensions**: Direct cloud operations, no file staging
3. **Terraform Modules**: Reusable, maintainable infrastructure
4. **Mangum for Lambda**: ASGI adapter for FastAPI on AWS Lambda
5. **Parquet Storage**: Efficient columnar format for analytics

---

## 🔗 **Related Documentation**

- [REQUIREMENTS.md](REQUIREMENTS.md) - Complete project requirements
- [README.md](README.md) - V1 CLI documentation
- [FastAPI Docs](https://fastapi.tiangolo.com/) - API framework
- [DuckDB S3 Guide](https://duckdb.org/docs/guides/import/s3_import.html) - Cloud storage

---

*This is an active development branch. V1 remains stable on `main` branch.*
