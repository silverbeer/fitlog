# 🎯 Pre-Commit Hooks Setup

This project uses pre-commit hooks to automatically catch and fix linting errors before they reach the repository, preventing GitHub Actions failures and maintaining consistent code quality.

## 🚀 What's Configured

### ✅ Active Hooks
- **Ruff Linting** - Catches style and code quality issues, auto-fixes when possible
- **Ruff Formatting** - Consistent code formatting (similar to Black)
- **File Validation** - Checks YAML, TOML, JSON syntax
- **File Cleanup** - Removes trailing whitespace, ensures files end with newline
- **Security** - Prevents large files, merge conflicts, case conflicts

### 🔄 Auto-Fixes Applied
- Code formatting and spacing
- Import sorting
- Trailing whitespace removal
- End-of-file newlines
- Quote style standardization

### 🚫 Temporarily Disabled (for rapid development)
- **MyPy** type checking - Will re-enable after fixing type annotations
- **Bandit** security scanning - Will re-enable after addressing security patterns

## 🎬 How It Works

1. **Developer writes code** with any formatting
2. **Developer runs `git commit`**
3. **Pre-commit hooks run automatically**:
   - If issues found → **commit BLOCKED**, files auto-fixed
   - If no issues → **commit succeeds**
4. **Developer adds fixed files and commits again**

## 📋 Demo Example

**Before (bad formatting):**
```python
def bad_function( ):
    x=1+2
    print('hello world')
```

**After (auto-fixed by hooks):**
```python
def bad_function():
    x = 1 + 2
    print("hello world")
```

## 🛠 Commands

```bash
# Run hooks on all files manually
uv run pre-commit run --all-files

# Run hooks on specific files
uv run pre-commit run --files file1.py file2.py

# Update hook versions
uv run pre-commit autoupdate

# Skip hooks for a specific commit (emergency use only)
git commit --no-verify -m "emergency commit"
```

## 🔧 Configuration Files

- **`.pre-commit-config.yaml`** - Hook definitions and versions
- **`pyproject.toml`** - Ruff and other tool configurations
- **`.git/hooks/pre-commit`** - Installed hook script (auto-generated)

## 🎯 Benefits

- ✅ **Prevents linting errors** from reaching GitHub Actions
- ✅ **Automatic code formatting** on every commit
- ✅ **Consistent code style** across the team
- ✅ **Faster CI/CD** since issues caught locally
- ✅ **Better code quality** with automated checks

## 🔮 Future Enhancements

When development stabilizes, we can re-enable:
- **MyPy** type checking for better type safety
- **Bandit** security scanning for vulnerability detection
- **Additional hooks** like documentation linting, commit message validation

## 🚨 Troubleshooting

### Hook fails with "command not found"
```bash
# Reinstall dev dependencies
uv pip install -e ".[dev]"
uv run pre-commit install
```

### Need to bypass hooks temporarily
```bash
# Emergency bypass (use sparingly!)
git commit --no-verify -m "urgent fix"
```

### Update hook versions
```bash
# Update to latest versions
uv run pre-commit autoupdate
git add .pre-commit-config.yaml
git commit -m "Update pre-commit hooks"
```

---

**Result:** No more linting failures in GitHub Actions! 🎉
