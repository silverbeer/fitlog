# 🏃‍♂️ Fitlog Project Requirements & Specifications

## 📋 **Project Overview**
Personal CLI tool for tracking daily exercise habits (runs and pushups) with progression tracking and cloud migration planned.

---

## 🎯 **V1 Current Implementation (Local CLI)**

### **Core Features**
- ✅ Track daily runs (duration, distance, pace calculation)
- ✅ Track daily pushups (count tracking)
- ✅ Import runs from Smashrun API with timezone support
- ✅ Beautiful Rich CLI with tables and progress displays
- ✅ Historical data viewing and reporting
- ✅ Debug mode (`--debug` flag) for all commands
- ✅ Backfilling support for past dates

### **CLI Commands**
```bash
fitlog log-run --duration "HH:MM:SS" --distance MILES [--date "MM/DD/YY"] [--debug]
fitlog log-pushups --count NUMBER [--date "MM/DD/YY"] [--debug]
fitlog get-run [--days N] [--debug]
fitlog status [--days N] [--debug]
fitlog report [--days N] [--debug]
fitlog import-smashrun [--access-token TOKEN] [--days N]
fitlog drop-db [--force]
```

### **Data Storage**
- **Database**: DuckDB (local file: `data/fitlog.db`)
- **Data Types**: Runs, Pushups, Splits (per-mile data)
- **Validation**: Pydantic models with type safety
- **Features**: Activity IDs, weather data, heart rate, cadence

### **Modern Python Tooling Requirements**
- **Package Manager**: UV (not pip/poetry)
- **Configuration**: Single `pyproject.toml` (no requirements.txt files)
- **Python Version**: 3.13+
- **Dependency Management**: Optional dependencies for dev/test
- **Code Quality**: Ruff (linting), Black (formatting), MyPy (typing)
- **Testing**: Pytest with coverage
- **Pre-commit**: Automated code quality checks
- **Entry Point**: Console script via pyproject.toml

### **Project Structure**
```
fitlog/
├── .gitignore                  # Comprehensive Python gitignore
├── .pre-commit-config.yaml     # Code quality automation
├── pyproject.toml             # ALL project configuration
├── README.md                  # Modern installation/usage docs
├── data/
│   ├── .gitkeep              # Preserve directory
│   └── fitlog.db             # Local DuckDB (gitignored)
├── fitlog/                   # Core package
│   ├── __init__.py
│   ├── cli.py               # Typer-based CLI
│   ├── db.py                # DuckDB operations
│   ├── models.py            # Pydantic models
│   ├── renderer.py          # Rich UI components
│   └── smashrun.py          # API integration
└── tests/                   # Test files
```

### **Git Configuration**
- **Multi-account setup**: Work vs Personal
- **Personal projects** (`~/silverbeer/`, `~/projects/`): `silverbeer <silverbeer.io@gmail.com>`
- **Work projects** (`~/work/`): `tdrake <tdrake@viantinc.com>`
- **Repository**: https://github.com/silverbeer/fitlog
- **Version**: v1.0.0 tagged and released

---

## 🚀 **V2 Cloud Migration Requirements**

### **Architecture Goals**
- **Serverless**: AWS Lambda + API Gateway (no EC2/containers)
- **Cost-effective**: Pay-per-request model for personal use
- **Stateless**: No server management
- **Maintainable**: Infrastructure as Code

### **Cloud Architecture**
```
CLI (local) → API Gateway → Lambda (FastAPI) → DuckDB (S3)
```

### **AWS Services**
- **API Gateway**: REST API endpoints (no web UI initially)
- **Lambda**: Python 3.13 FastAPI application
- **S3**: DuckDB storage with direct S3 extensions
- **CloudWatch**: Logging and monitoring
- **IAM**: Authentication and permissions

### **DuckDB S3 Strategy** (PREFERRED APPROACH)
- **Method**: Use DuckDB S3 extensions for direct S3 operations
- **Storage Format**: Parquet files partitioned by date
- **Benefits**: No file downloads, true concurrency, better performance
- **Structure**:
  ```
  s3://fitlog-bucket/
  ├── runs/year=2025/month=06/day=07/runs.parquet
  ├── pushups/year=2025/month=06/day=07/pushups.parquet
  └── metadata/schema.json
  ```

### **FastAPI Design**
- **Framework**: FastAPI (same Pydantic models as V1)
- **Endpoints**: Mirror CLI commands as REST API
  ```
  POST /runs              # log_run
  POST /pushups           # log_pushups
  GET  /runs              # get_run
  GET  /activities/status # status
  GET  /activities/report # report
  POST /import/smashrun   # import_smashrun
  GET  /health           # health check
  ```

### **Authentication Strategy**
- **Phase 1**: Simple API Keys (stored in CLI config)
- **Future**: AWS Cognito + JWT tokens
- **CLI Flow**:
  ```bash
  fitlog auth login    # Get/store token
  fitlog status        # Use token in headers
  ```

### **Infrastructure as Code**
- **Tool**: Terraform (preferred over OpenTofu for AWS provider support)
- **Structure**:
  ```
  infrastructure/
  ├── modules/
  │   ├── api-gateway/
  │   ├── lambda/
  │   ├── s3/
  │   └── iam/
  ├── environments/
  │   ├── dev/
  │   └── prod/
  └── main.tf
  ```

### **CI/CD Pipeline**
- **Platform**: GitHub Actions
- **Triggers**: Push to main branch
- **Workflow**:
  ```yaml
  test → lint → terraform plan → terraform apply → package lambda → deploy
  ```

### **Migration Strategy**
1. **Phase 1**: API-first development (new repo: `fitlog-cloud`)
2. **Phase 2**: Data migration script (local → S3)
3. **Phase 3**: Hybrid CLI (local/cloud/fallback modes)
4. **Phase 4**: Cloud-first with local backup

### **CLI V2 Modifications**
- **Configuration**: `~/.fitlog/config.yaml`
  ```yaml
  mode: "cloud"  # local, cloud, hybrid
  cloud:
    api_url: "https://api.fitlog.com"
    auth_token: "..."
  local:
    db_path: "data/fitlog.db"
  ```
- **Client Architecture**:
  ```python
  class FitlogClient:
      def __init__(self):
          self.mode = get_config_mode()
          if self.mode == "cloud":
              self.client = CloudClient()
          elif self.mode == "local":
              self.client = LocalClient()
          else:  # hybrid
              self.client = HybridClient()
  ```

---

## 🛠️ **Development Workflow Requirements**

### **Code Quality Standards**
- **Linting**: Ruff with strict rules
- **Formatting**: Black (line-length: 88)
- **Type Checking**: MyPy with strict mode
- **Testing**: Pytest with coverage reporting
- **Pre-commit**: All checks must pass

### **UV Workflow**
```bash
# Environment management
uv venv
source .venv/bin/activate
uv pip install -e ".[dev]"

# Development commands
uv run pytest
uv run black .
uv run ruff check . --fix
uv run mypy fitlog/
uv run pre-commit run --all-files

# Package building
uv build
```

### **Repository Strategy**
- **V1 Repo**: `github.com/silverbeer/fitlog` (current, stable)
- **V2 Repo**: `github.com/silverbeer/fitlog-cloud` (planned)
- **Branching**: Feature branches → main → deploy
- **Versioning**: Semantic versioning with git tags

---

## 🎯 **Success Criteria**

### **V1 (Completed)**
- ✅ Modern Python tooling with UV and pyproject.toml
- ✅ Working CLI with all required features
- ✅ Debug mode for troubleshooting
- ✅ Professional git setup and GitHub publication
- ✅ Clean, maintainable codebase

### **V2 (Planned)**
- 🎯 Serverless AWS deployment with Terraform
- 🎯 DuckDB S3 integration working smoothly
- 🎯 FastAPI REST endpoints matching CLI functionality
- 🎯 Hybrid CLI supporting both local and cloud modes
- 🎯 Automated CI/CD pipeline
- 🎯 Cost-effective personal fitness tracking in the cloud

---

## 📝 **Key Design Decisions**

1. **UV over Poetry/pip**: Faster, more modern dependency management
2. **Single pyproject.toml**: No scattered config files
3. **DuckDB S3 extensions**: Direct cloud operations, no file staging
4. **Serverless architecture**: Cost-effective for personal use
5. **Terraform over CDK**: Better AWS resource management
6. **API-first migration**: Safe parallel development
7. **Multi-account git**: Clean separation of work/personal projects

---

## 🚨 **Non-Requirements**

- ❌ Web UI (initially - API only)
- ❌ Multi-user support
- ❌ Complex authentication (initially)
- ❌ Real-time features
- ❌ Mobile apps
- ❌ Docker/containerization (serverless approach)
- ❌ Multiple databases (DuckDB only)

---

*This document serves as the single source of truth for fitlog project requirements and should be updated as specifications evolve.*
