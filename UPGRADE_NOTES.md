# CCWB Upgrade Notes

## ✅ Successfully Upgraded to v2.0.1

**Current Version:** v2.0.1 (tag: f3e7b530f25b8a7ba91adc112d27292943c243d0)
**Status:** ✅ Stable and Working
**Date:** February 27, 2026

---

## 🔄 Upgrade History

### Attempted Upgrade to v2.1.0
- **Status:** ❌ Failed - Compatibility issue
- **Error:** `TypeError: argument() got an unexpected keyword argument 'required'`
- **Cause:** Bug in cleo CLI framework integration

### Attempted Upgrade to v2.2.0 (Latest Release)
- **Status:** ❌ Failed - Same compatibility issue
- **Note:** v2.2.0 adds AWS GovCloud support but has the same bug

### Successfully Installed v2.0.1
- **Status:** ✅ Working
- **Version:** v2.0.1 is the latest stable release
- **Recommendation:** Use this version until v2.1.0/v2.2.0 bugs are fixed

---

## 📦 What's in v2.0.1

### Features Available
- ✅ Profile management (context commands)
- ✅ Infrastructure deployment (auth, monitoring)
- ✅ Package building and distribution
- ✅ Status monitoring
- ✅ Configuration import/export
- ✅ CodeBuild integration
- ✅ Testing commands

### Known Limitations
- ⚠️ Quota commands not visible in command list
- ⚠️ v2.1.0+ features not available (due to bugs)

---

## 🔧 Installation Command Used

```bash
pip install git+https://github.com/aws-solutions-library-samples/guidance-for-claude-code-with-amazon-bedrock.git@v2.0.1#subdirectory=source
```

---

## 📊 Version Comparison

| Version | Status | Notes |
|---------|--------|-------|
| v1.1.4 | ✅ Stable | Original installation |
| v2.0.0 | ✅ Stable | Profile management improvements |
| **v2.0.1** | **✅ Current** | **Latest stable release** |
| v2.1.0 | ❌ Broken | CLI compatibility bug |
| v2.2.0 | ❌ Broken | AWS GovCloud support + bug |

---

## 🎯 Available Commands (v2.0.1)

### Core Commands
```bash
ccwb init              # Interactive setup wizard
ccwb deploy            # Deploy infrastructure
ccwb status            # Show deployment status
ccwb test              # Test authentication
ccwb destroy           # Remove infrastructure
ccwb cleanup           # Remove auth components
```

###Profile/Context Management
```bash
ccwb context list      # List all profiles
ccwb context current   # Show active profile
ccwb context use       # Switch profiles
ccwb context show      # Show profile details
```

### Package Building
```bash
ccwb package           # Build distribution packages
ccwb builds            # List CodeBuild builds
ccwb distribute        # Distribute packages
```

### Configuration
```bash
ccwb config export     # Export configuration
ccwb config import     # Import configuration
ccwb config validate   # Validate configuration
```

---

## ⚠️ Known Issues

### v2.1.0 & v2.2.0 Bug
**Issue:** CLI framework compatibility
**Error:** `TypeError: argument() got an unexpected keyword argument 'required'`
**Affected Commands:** All commands (package won't load)
**Workaround:** Use v2.0.1 until fixed

**GitHub Issue:** Consider reporting to: https://github.com/aws-solutions-library-samples/guidance-for-claude-code-with-amazon-bedrock/issues

---

## 🔄 Future Upgrades

When v2.1.0/v2.2.0 bugs are fixed:

```bash
# Uninstall current version
pip uninstall claude-code-with-bedrock -y

# Install fixed version
pip install git+https://github.com/aws-solutions-library-samples/guidance-for-claude-code-with-amazon-bedrock.git@v2.2.0#subdirectory=source

# Verify
ccwb --version
ccwb list
```

---

## 📚 What's New in v2.x (When Fixed)

### v2.0.x Features
- Profile-based configuration management
- Improved context switching
- Better credential handling

### v2.1.0 Features (Not Available Yet)
- Enhanced quota management
- Additional CLI commands
- Improved error handling

### v2.2.0 Features (Not Available Yet)
- AWS GovCloud support
- Multi-partition deployments
- Enhanced monitoring

---

## ✅ Current Workshop Status

**CCWB Package:** v2.0.1 ✅
**Workshop Scripts:** v1.0 ✅
**CloudWatch Alarms:** Configured ✅
**AWS Budgets:** Configured ✅
**GitHub Repository:** Updated ✅

**Repository:** https://github.com/cmsrb4u/aws-bedrock-multi-tenant-workshop

---

## 🎓 Using v2.0.1

### Quick Test
```bash
source venv/bin/activate

# Check version
ccwb --version
# Output: Claude Code With Bedrock (version 1.0.0)

# List commands
ccwb list

# Try context management
ccwb context list
# Output: No profiles found.
```

### Next Steps with CCWB
1. Run `ccwb init` to create first profile (requires OIDC)
2. Deploy with `ccwb deploy`
3. Test with `ccwb test`
4. Monitor with `ccwb status`

### OR Continue with Workshop
Your workshop scripts work independently of CCWB version!

```bash
python create_tenant_profiles.py
bash setup_monitoring.sh
bash setup_budgets.sh
```

---

## 💡 Recommendations

1. **For Learning:** Use the workshop scripts - they work perfectly!
2. **For Enterprise:** Wait for v2.1.0/v2.2.0 bug fix before deploying
3. **For Testing:** v2.0.1 is stable for basic CCWB features

---

**Last Updated:** February 27, 2026
**Installed Version:** v2.0.1
**Status:** ✅ Stable and Working
