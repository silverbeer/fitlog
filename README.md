# 🏃‍♂️ fitlog - Daily Exercise Tracking CLI

[![🚀 Deploy Status](https://github.com/silverbeer/fitlog/actions/workflows/deploy.yml/badge.svg?branch=feature%2Fv2-cloud-migration)](https://github.com/silverbeer/fitlog/actions/workflows/deploy.yml)
[![🧪 Tests](https://img.shields.io/badge/tests-passing-brightgreen.svg)](https://github.com/silverbeer/fitlog/actions/workflows/deploy.yml)
[![🏥 API Health](https://img.shields.io/badge/API-healthy-brightgreen.svg)](https://2054k0hh9j.execute-api.us-east-1.amazonaws.com/dev)
[![🐍 Python](https://img.shields.io/badge/python-3.13-blue.svg)](https://python.org)
[![⚡ AWS Lambda](https://img.shields.io/badge/AWS-Lambda-orange.svg)](https://aws.amazon.com/lambda/)
[![📊 DuckDB](https://img.shields.io/badge/database-DuckDB-yellow.svg)](https://duckdb.org)

**fitlog** is a personal command-line tool for tracking your daily exercise habits, designed to help you stay consistent with your weekly, monthly, and yearly fitness goals. Built with Python 3.13 and styled beautifully using Rich CLI, fitlog lets you log workouts and instantly see how you're progressing over time.

---

## ✨ Project Goals

- Log daily workouts quickly via a CLI
- Track consistency and performance over time
- Display beautiful summaries and progress dashboards
- Store all data locally using DuckDB
- Provide goal-driven feedback to motivate habit-building
- Import runs from Smashrun to keep your data in sync

---

## 🏋️‍♂️ Activities Tracked

### 🏃 Running
- **Goal:** Run **every day**
  - Weekly: 7/7 days
  - Monthly: All days
  - Yearly: 365 days
- **Metrics Tracked:**
  - Total time (HH:MM:SS)
  - Total distance (miles)
  - Average pace per mile
- **Data Sources:**
  - Manual entry via CLI
  - Automatic import from Smashrun

### 💪 Pushups
- **Goal:** At least 100 pushups
  - Weekly: 5 days
  - Monthly: 25 days
  - Yearly: 200 days

---

## 🧰 Tech Stack

- **Language:** Python 3.13
- **Package Management:** UV (modern Python package manager)
- **CLI Framework:** Typer + Rich (beautiful command-line interfaces)
- **Database:** DuckDB (lightweight embedded SQL)
- **Data Validation:** Pydantic (type-safe data models)
- **External APIs:** Smashrun API integration
- **Code Quality:** Ruff (linting), Black (formatting), MyPy (type checking)

---

## 🚀 Installation

### Prerequisites
- Python 3.13+
- [UV](https://docs.astral.sh/uv/) (modern Python package manager)

### Install UV
```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Or via Homebrew
brew install uv

# Or via pip
pip install uv
```

### Install fitlog
```bash
# Clone the repository
git clone https://github.com/yourusername/fitlog.git
cd fitlog

# Create virtual environment and install
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
uv pip install -e ".[dev]"

# Setup pre-commit hooks (optional but recommended)
uv run pre-commit install
```

### Quick Start
```bash
# Test the installation
fitlog status

# Log your first run
fitlog log-run --duration "30:00:00" --distance 3.1

# Log some pushups
fitlog log-pushups --count 50

# Check your progress
fitlog status
```

---

## 💻 CLI Features

### `fitlog log-run` and `fitlog log-pushups`
Log your daily activities:
```bash
# Log a run with time and distance
fitlog log-run --duration "33:44:00" --distance 3.54

# Log pushups
fitlog log-pushups --count 120

# Log activities for a specific date
fitlog log-run --duration "30:15:00" --distance 3.2 --date "06/06/25"
fitlog log-pushups --count 100 --date "06/06/25"

# Debug mode to see database queries
fitlog log-run --duration "25:30:00" --distance 2.8 --debug
```

### `fitlog import-smashrun`
Import your runs from Smashrun:
```bash
# Import runs from the last 30 days (default)
fitlog import-smashrun

# Import runs from the last 7 days
fitlog import-smashrun --days 7

# Import runs using a specific access token
fitlog import-smashrun --access-token YOUR_TOKEN
```

To use the Smashrun integration:
1. Get your API token from https://smashrun.com/settings/api
2. Set it in your `.env` file:
   ```
   SMASHRUN_ACCESS_TOKEN=your_token_here
   ```
3. Run the import command

The importer will:
- Convert distances from kilometers to miles
- Calculate pace per mile
- Store dates in local timezone format
- Persist runs in the local DuckDB database
- Show detailed progress and any errors

### `fitlog get-run`
View your recent runs:
```bash
# View runs from the last day (default)
fitlog get-run

# View runs from the last 7 days
fitlog get-run --days 7

# Debug mode to see database queries
fitlog get-run --days 30 --debug
```

This will display a beautiful table showing:
- Date and time of each run
- Distance in miles
- Duration and pace
- Heart rate and cadence
- Weather conditions

### Debug Mode
All commands support a `--debug` flag to show detailed information:
```bash
# See database queries and connection info
fitlog status --debug
fitlog get-run --days 7 --debug
fitlog log-run --duration "25:00:00" --distance 3.0 --debug
```

### Data Validation
All inputs are validated using Pydantic models to ensure:
- Run times are in correct HH:MM:SS format
- Distances are positive numbers
- Pushup counts are positive integers
- Dates are properly formatted

### `fitlog status`
See your progress and recent activities:
```bash
# View recent activities and statistics
fitlog status

# Show more days of history
fitlog status --days 30

# Debug mode to see database queries
fitlog status --debug
```

This displays a beautiful table of recent activities and statistics showing your running and pushups progress over time.

### `fitlog report`
Generate detailed reports:
```bash
# Weekly report (default)
fitlog report

# Monthly report
fitlog report --days 30

# Yearly report with debug info
fitlog report --days 365 --debug
```

### `fitlog goals`
Review or customize your current activity goals (future version)

---

## 📦 Project Structure

```
fitlog/
├── .gitignore                  # Python gitignore
├── .pre-commit-config.yaml     # Code quality automation
├── pyproject.toml             # All project configuration
├── README.md                  # This file
├── data/
│   ├── .gitkeep              # Preserve directory in git
│   └── fitlog.db             # Local DuckDB database
├── fitlog/                   # Core package
│   ├── __init__.py
│   ├── cli.py               # CLI entry point using Typer
│   ├── db.py                # DuckDB setup and queries
│   ├── models.py            # Pydantic data models
│   ├── renderer.py          # Rich-based UI rendering
│   └── smashrun.py          # Smashrun API client
└── tests/                   # Unit tests
```

---

## 🚧 Roadmap

- [x] CLI commands: `log`, `status`, `get-run`
- [x] DuckDB schema and storage layer
- [x] Weekly/monthly/yearly calculations
- [x] Rich output formatting
- [x] Smashrun integration with local timezone support
- [x] Persistent data storage
- [ ] Custom activity and goal support
- [ ] Add bar graphs and summaries

---

## 🧪 Example Workflow

```bash
# Log today's activities
fitlog log-run --duration "33:44:00" --distance 3.54
fitlog log-pushups --count 100

# Import recent runs from Smashrun
fitlog import-smashrun --days 7

# Check your progress
fitlog status

# Generate a weekly report
fitlog report --days 7

# View recent runs with debug info
fitlog get-run --days 5 --debug
```

---

## 🛠️ Development

### Code Quality Tools
```bash
# Format code
uv run black .
uv run ruff format .

# Lint code
uv run ruff check .
uv run ruff check . --fix

# Type checking
uv run mypy fitlog/

# Run tests
uv run pytest

# Run all checks via pre-commit
uv run pre-commit run --all-files
```

### Project Commands
```bash
# Install development dependencies
uv pip install -e ".[dev]"

# Install test dependencies only
uv pip install -e ".[test]"

# Sync dependencies
uv pip sync pyproject.toml

# Build package
uv build
```

---

## 🧠 Future Ideas

- OpenAI summaries for motivational feedback
- Visual graphs using Rich or Textual
- Support for additional workouts (e.g., biking, swimming)
- Export to CSV or JSON
- Integration with more fitness services (Strava, Garmin, etc.)

---

## 📄 License

MIT (to be added)

---

## 🚀 GitHub Actions

Instead of this manual process:
```bash
git push
cd infrastructure
zip lambda_function.zip main.py
aws lambda update-function-code ...
terraform apply
```

You'll get this:
```bash
git push  # 🎉 Everything deploys automatically!
```
