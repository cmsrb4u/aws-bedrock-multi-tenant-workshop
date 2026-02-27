# Installing Claude Code with Bedrock (CCWB)

This guide shows how to install the `claude-code-with-bedrock` package in your workshop environment.

## ✅ Installation Complete

The CCWB package has been installed from GitHub source!

## 📦 Installation Methods

### Method 1: Install from GitHub Source (Recommended)

```bash
# Activate virtual environment
source venv/bin/activate

# Install from GitHub
pip install git+https://github.com/aws-solutions-library-samples/guidance-for-claude-code-with-amazon-bedrock.git#subdirectory=source
```

### Method 2: Clone and Install Locally

```bash
# Clone repository
git clone https://github.com/aws-solutions-library-samples/guidance-for-claude-code-with-amazon-bedrock.git
cd guidance-for-claude-code-with-amazon-bedrock/source

# Install with Poetry
poetry install

# Use commands
poetry run ccwb --help
```

## 🎯 Available Commands

After installation, you have access to the full CCWB CLI:

```bash
# Show version
ccwb --version

# List all commands
ccwb list

# Show help
ccwb --help
```

### Core Commands

```bash
# Initialize configuration (requires OIDC setup)
ccwb init

# Deploy infrastructure
ccwb deploy                    # Deploy all stacks
ccwb deploy auth               # Deploy authentication only
ccwb deploy quota              # Deploy quota monitoring

# View deployment status
ccwb status

# Test setup
ccwb test
```

### Context/Profile Management

```bash
# List profiles
ccwb context list

# Show current profile
ccwb context current

# Switch profile
ccwb context use <profile-name>

# Show profile details
ccwb context show
```

### Quota Management (Enterprise)

```bash
# List all quota policies
ccwb quota list
ccwb quota list --type user
ccwb quota list --type group

# Set user quota
ccwb quota set-user john.doe@example.com \
  --monthly-limit 500M \
  --daily-limit 20M \
  --enforcement block

# Set group quota
ccwb quota set-group engineering \
  --monthly-limit 400M \
  --daily-limit 15M

# Set default quota
ccwb quota set-default \
  --monthly-limit 225M \
  --daily-limit 8M

# Show effective quota for user
ccwb quota show user@example.com --groups "engineering,ml"

# View usage
ccwb quota usage user@example.com

# Delete quota policy
ccwb quota delete user john.doe@example.com
ccwb quota delete group engineering

# Temporarily unblock user
ccwb quota unblock user@example.com --duration 24h
```

### Package Building

```bash
# Build distribution packages
ccwb package --target-platform all

# Check build status
ccwb builds

# Distribute packages
ccwb distribute
```

### Configuration Management

```bash
# Export configuration
ccwb config export > config.json

# Import configuration
ccwb config import config.json profile-name

# Validate configuration
ccwb config validate
```

### Cleanup

```bash
# Remove authentication components
ccwb cleanup

# Destroy all infrastructure
ccwb destroy
```

## 🔄 Difference from Workshop Scripts

| Feature | CCWB Tool | Workshop Scripts |
|---------|-----------|------------------|
| **Target** | Enterprise multi-user | Multi-tenant (per-tenant) |
| **Auth** | OIDC required | Direct AWS credentials |
| **Setup** | Full infrastructure | Lightweight scripts |
| **Quotas** | Per-user/group | Per-tenant via CloudWatch |
| **Monitoring** | OpenTelemetry | Native CloudWatch |
| **Deployment** | CloudFormation | Manual setup |

## 💡 When to Use What

### Use CCWB (`ccwb` commands) When:
- Deploying enterprise multi-user environment
- Need user/group-level quotas
- Have OIDC identity provider
- Want automated credential management
- Need comprehensive monitoring

### Use Workshop Scripts When:
- Learning about Application Inference Profiles
- Setting up multi-tenant architecture
- Need quick setup without OIDC
- Using direct AWS credentials
- Focused on cost allocation per tenant

## 🚀 Quick Test

Verify CCWB is working:

```bash
# Check version
ccwb --version

# Try listing contexts (will show none if not initialized)
ccwb context list

# Show all available commands
ccwb list
```

## ⚠️ Prerequisites for Full CCWB Deployment

To use CCWB deployment commands, you need:

1. **OIDC Identity Provider**
   - Okta, Azure AD, Auth0, or Cognito User Pools
   - Client ID and issuer URL
   - Ability to create application registrations

2. **AWS Permissions**
   - CloudFormation stack creation
   - IAM role/policy creation
   - VPC and networking (for monitoring)
   - ECS, Lambda (for monitoring)

3. **Configuration**
   - Run `ccwb init` to set up profile
   - Answer interactive prompts
   - Configure OIDC details

## 📚 Additional Resources

- [CCWB GitHub Repository](https://github.com/aws-solutions-library-samples/guidance-for-claude-code-with-amazon-bedrock)
- [Quick Start Guide](https://github.com/aws-solutions-library-samples/guidance-for-claude-code-with-amazon-bedrock/blob/main/QUICK_START.md)
- [Architecture Documentation](https://github.com/aws-solutions-library-samples/guidance-for-claude-code-with-amazon-bedrock/blob/main/assets/docs/ARCHITECTURE.md)

---

## ✅ Installation Status

- **Package:** `claude-code-with-bedrock` v1.1.4
- **Source:** GitHub (aws-solutions-library-samples)
- **Installed in:** `/workshop/venv`
- **Command:** `ccwb`
- **Status:** ✅ Ready to use

---

**Note:** The workshop scripts provide a simpler alternative for multi-tenant setups without requiring OIDC infrastructure. Choose the approach that best fits your needs!
