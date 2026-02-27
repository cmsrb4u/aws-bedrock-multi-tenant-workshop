# Poetry Setup Guide for CCWB v2.2.0

Complete guide for setting up Claude Code with Bedrock using Poetry.

---

## ✅ Setup Complete!

Both Poetry and pip installations are working with CCWB v2.2.0 (with bug fix applied).

---

## 📦 Two Installation Methods Available

### Method 1: Poetry (Development Setup)
**Location:** `/home/participant/guidance-for-claude-code-with-amazon-bedrock/source`
**Best for:** Development, source code access, contributing

### Method 2: Pip (Production Setup)
**Location:** `/workshop/venv`
**Best for:** Production use, simpler dependencies

---

## 🔧 Method 1: Poetry Setup (Completed)

### Installation Steps

```bash
# Clone the repository
git clone https://github.com/aws-solutions-library-samples/guidance-for-claude-code-with-amazon-bedrock
cd guidance-for-claude-code-with-amazon-bedrock

# Checkout v2.2.0
git checkout v2.2.0

# Navigate to source directory
cd source

# Install dependencies with Poetry
poetry install
```

### Bug Fix Applied
**File:** `source/claude_code_with_bedrock/cli/commands/quota.py:987`
**Change:** `required=False` → `optional=True`

### Using Poetry Commands

```bash
cd /home/participant/guidance-for-claude-code-with-amazon-bedrock/source

# Check version
poetry run ccwb --version

# List commands
poetry run ccwb list

# Show quota commands
poetry run ccwb quota list --help

# Initialize profile
poetry run ccwb init

# Deploy infrastructure
poetry run ccwb deploy

# All other commands
poetry run ccwb <command>
```

---

## 🔧 Method 2: Pip Setup (Also Completed)

### Installation Steps

```bash
cd /workshop
source venv/bin/activate

# Install from GitHub
pip install git+https://github.com/aws-solutions-library-samples/guidance-for-claude-code-with-amazon-bedrock.git@v2.2.0#subdirectory=source
```

### Bug Fix Applied
**File:** `venv/lib/python3.12/site-packages/claude_code_with_bedrock/cli/commands/quota.py:987`
**Change:** `required=False` → `optional=True`

### Using Pip Commands

```bash
cd /workshop
source venv/bin/activate

# Check version
ccwb --version

# List commands
ccwb list

# Show quota commands
ccwb quota list --help

# All other commands work directly
ccwb <command>
```

---

## 📊 Comparison

| Feature | Poetry | Pip |
|---------|--------|-----|
| **Location** | Full repo clone | Installed package |
| **Source Code** | ✅ Full access | ❌ Binary only |
| **Development** | ✅ Ideal | ⚠️ Limited |
| **Production** | ⚠️ Overhead | ✅ Lightweight |
| **Updates** | `git pull` + `poetry install` | `pip install --upgrade` |
| **Command** | `poetry run ccwb` | `ccwb` |
| **Isolation** | Poetry virtualenv | Custom venv |
| **Size** | ~500MB (with repo) | ~50MB (package only) |

---

## ✅ Verification

### Poetry Installation
```bash
$ cd /home/participant/guidance-for-claude-code-with-amazon-bedrock/source
$ poetry run ccwb --version
Claude Code With Bedrock (version 1.0.0)

$ poetry run ccwb list
# Shows all 26 commands including quota management ✓
```

### Pip Installation
```bash
$ cd /workshop
$ source venv/bin/activate
$ ccwb --version
Claude Code With Bedrock (version 1.0.0)

$ ccwb list
# Shows all 26 commands including quota management ✓
```

---

## 🎯 Which Should You Use?

### Use Poetry When:
- ✅ Contributing to CCWB development
- ✅ Need to modify source code
- ✅ Testing new features
- ✅ Building from source
- ✅ Have the full repository cloned

### Use Pip When:
- ✅ Just using CCWB (not developing)
- ✅ Want simpler installation
- ✅ Need lightweight setup
- ✅ Integrating into other projects
- ✅ Production deployments

---

## 📚 Available Commands (Both Methods)

### Core (10 commands)
```bash
poetry run ccwb init              # OR: ccwb init
poetry run ccwb deploy            # OR: ccwb deploy
poetry run ccwb status            # OR: ccwb status
poetry run ccwb test              # OR: ccwb test
poetry run ccwb destroy           # OR: ccwb destroy
poetry run ccwb cleanup           # OR: ccwb cleanup
poetry run ccwb package           # OR: ccwb package
poetry run ccwb builds            # OR: ccwb builds
poetry run ccwb distribute        # OR: ccwb distribute
poetry run ccwb help              # OR: ccwb help
```

### Context Management (4 commands)
```bash
poetry run ccwb context list      # OR: ccwb context list
poetry run ccwb context current   # OR: ccwb context current
poetry run ccwb context use       # OR: ccwb context use
poetry run ccwb context show      # OR: ccwb context show
```

### Quota Management (9 commands)
```bash
poetry run ccwb quota list                           # OR: ccwb quota list
poetry run ccwb quota set-user user@example.com      # OR: ccwb quota set-user
poetry run ccwb quota set-group engineering          # OR: ccwb quota set-group
poetry run ccwb quota set-default                    # OR: ccwb quota set-default
poetry run ccwb quota show user@example.com          # OR: ccwb quota show
poetry run ccwb quota usage user@example.com         # OR: ccwb quota usage
poetry run ccwb quota delete user user@example.com   # OR: ccwb quota delete
poetry run ccwb quota unblock user@example.com       # OR: ccwb quota unblock
poetry run ccwb quota export policies.json           # OR: ccwb quota export
poetry run ccwb quota import policies.json           # OR: ccwb quota import
```

### Configuration (3 commands)
```bash
poetry run ccwb config export     # OR: ccwb config export
poetry run ccwb config import     # OR: ccwb config import
poetry run ccwb config validate   # OR: ccwb config validate
```

**Total: 26 commands** ✅

---

## 🔄 Updating

### Update Poetry Installation
```bash
cd /home/participant/guidance-for-claude-code-with-amazon-bedrock

# Pull latest changes
git pull origin main

# Or checkout specific version
git fetch --tags
git checkout v2.3.0  # When available

# Reinstall
cd source
poetry install

# Re-apply bug fix if needed
```

### Update Pip Installation
```bash
cd /workshop
source venv/bin/activate

# Uninstall
pip uninstall claude-code-with-bedrock -y

# Reinstall latest
pip install git+https://github.com/aws-solutions-library-samples/guidance-for-claude-code-with-amazon-bedrock.git@v2.3.0#subdirectory=source

# Re-apply bug fix if needed
```

---

## 🐛 Bug Fix Details

### The Issue
v2.1.0 and v2.2.0 have a compatibility bug with the cleo CLI framework.

**Error:**
```
TypeError: argument() got an unexpected keyword argument 'required'
```

**Location:**
```
claude_code_with_bedrock/cli/commands/quota.py:987
```

### The Fix
**Change line 987 from:**
```python
argument("file", description="Output file path (.json or .csv)", required=False),
```

**To:**
```python
argument("file", description="Output file path (.json or .csv)", optional=True),
```

### Applied To:
✅ Poetry installation (source code)
✅ Pip installation (installed package)

---

## 📁 Directory Structure

### Poetry Setup
```
/home/participant/guidance-for-claude-code-with-amazon-bedrock/
├── source/
│   ├── claude_code_with_bedrock/     # Source code
│   │   ├── cli/
│   │   │   └── commands/
│   │   │       └── quota.py          # Bug fixed here
│   │   └── ...
│   ├── pyproject.toml                # Poetry config
│   ├── poetry.lock                   # Dependencies
│   └── ...
├── deployment/                        # CloudFormation templates
├── assets/                            # Documentation
└── ...
```

### Pip Setup
```
/workshop/
├── venv/
│   └── lib/python3.12/site-packages/
│       └── claude_code_with_bedrock/
│           └── cli/commands/
│               └── quota.py          # Bug fixed here
├── Python scripts (workshop)
├── Documentation
└── ...
```

---

## 🎓 Quick Start Examples

### Poetry Example
```bash
# Navigate to Poetry setup
cd /home/participant/guidance-for-claude-code-with-amazon-bedrock/source

# Initialize (requires OIDC)
poetry run ccwb init

# Deploy
poetry run ccwb deploy

# Set quota
poetry run ccwb quota set-default --monthly-limit 225M
```

### Pip Example
```bash
# Navigate to workshop
cd /workshop
source venv/bin/activate

# Initialize (requires OIDC)
ccwb init

# Deploy
ccwb deploy

# Set quota
ccwb quota set-default --monthly-limit 225M
```

---

## ✅ Both Methods Working!

- ✅ Poetry installation: v2.2.0 with bug fix
- ✅ Pip installation: v2.2.0 with bug fix
- ✅ All 26 commands functional
- ✅ Quota management working
- ✅ Ready for development or production

---

## 📚 Additional Resources

**Repository:**
https://github.com/aws-solutions-library-samples/guidance-for-claude-code-with-amazon-bedrock

**Workshop Repository:**
https://github.com/cmsrb4u/aws-bedrock-multi-tenant-workshop

**Poetry Documentation:**
https://python-poetry.org/docs/

---

**Last Updated:** February 27, 2026
**CCWB Version:** v2.2.0 (fixed)
**Status:** ✅ Both methods working perfectly!
