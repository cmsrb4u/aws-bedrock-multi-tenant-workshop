# CCWB Quota Management Automation - Summary

## The Problem

Manual quota management doesn't scale:
- ❌ Creating users one-by-one
- ❌ Manually assigning groups
- ❌ Setting quotas individually
- ❌ No sync with HR systems
- ❌ Stale users when employees leave

## 6 Automation Strategies

### 1. 🏆 Identity Provider Sync (RECOMMENDED)

**Best for: Enterprise deployments with existing IdP**

Automatically sync users and groups from your corporate identity provider.

#### How It Works
```
Corporate IdP (Okta/Azure AD)
    → SCIM/OIDC Sync
        → AWS Cognito
            → CCWB Quota Policies Auto-Apply
```

#### Setup (Okta Example)
```json
{
  "provider_type": "okta",
  "provider_domain": "company.okta.com",
  "group_claim": "groups"
}
```

#### Workflow
1. HR adds user to "Engineering" in Okta
2. User authenticates via CCWB
3. CCWB reads `groups` claim from JWT token
4. Engineering quota (400M/month) applies automatically

**Benefits:**
- ✅ Zero manual user management
- ✅ Real-time synchronization
- ✅ Single source of truth (your IdP)
- ✅ Automatic user deactivation

---

### 2. 📋 Infrastructure as Code (Terraform)

**Best for: Version-controlled quota policies**

Manage quotas like infrastructure with Git + Terraform.

#### Example: terraform/quotas.tf
```hcl
variable "group_quotas" {
  default = {
    "engineering" = { monthly_limit = 400000000 }
    "ml-team"     = { monthly_limit = 600000000 }
    "product"     = { monthly_limit = 225000000 }
  }
}

resource "aws_dynamodb_table_item" "group_quotas" {
  for_each   = var.group_quotas
  table_name = "QuotaPolicies"

  item = jsonencode({
    policy_type         = { S = "group" }
    identifier          = { S = each.key }
    monthly_token_limit = { N = tostring(each.value.monthly_limit) }
  })
}
```

#### Workflow
```bash
# 1. Update quota in Git
vim terraform/quotas.tf
git commit -m "Increase engineering quota to 500M"

# 2. CI/CD deploys automatically
terraform apply

# 3. Changes live in seconds
```

**Benefits:**
- ✅ Version control (audit trail)
- ✅ Change review (pull requests)
- ✅ Rollback capability
- ✅ CI/CD integration

---

### 3. 📊 Bulk CSV Import/Export

**Best for: Large-scale updates, quarterly reviews**

Manage 100+ policies at once via spreadsheet.

#### Example: quotas.csv
```csv
type,identifier,monthly_limit,daily_limit,enforcement_mode,enabled
default,default,225M,8M,alert,true
group,engineering,400M,,alert,true
group,ml-team,600M,25M,alert,true
user,ceo@company.com,1000M,50M,alert,true
```

#### Workflow
```bash
# Export current policies
ccwb quota export current-policies.csv

# Team managers update in Excel/Google Sheets

# Re-import updated policies
ccwb quota import updated-policies.csv
```

**Benefits:**
- ✅ Bulk operations
- ✅ Non-technical friendly (Excel)
- ✅ Easy quarterly reviews
- ✅ Backup/restore capability

---

### 4. 🔄 Automated Directory Sync

**Best for: Active Directory / LDAP environments**

Daily sync from AD to Cognito to CCWB quotas.

#### Python Script: sync-ad-to-cognito.py
```python
def sync_ad_groups():
    # 1. Connect to Active Directory
    conn = ldap3.Connection("ldap://corporate-ad.company.com")

    # 2. Get groups and members
    conn.search('DC=company,DC=com', '(objectClass=group)')

    # 3. Create groups in Cognito
    for group in groups:
        cognito.create_group(GroupName=group_name)

        # 4. Add members
        for user in members:
            cognito.admin_add_user_to_group(...)
```

#### Schedule
```bash
# Cron: Run daily at 2 AM
0 2 * * * python3 sync-ad-to-cognito.py

# Or AWS Lambda with EventBridge
aws events put-rule --schedule-expression "cron(0 2 * * ? *)"
```

**Benefits:**
- ✅ Automated daily sync
- ✅ Works with existing AD
- ✅ Lambda deployment option
- ✅ No manual intervention

---

### 5. 🌐 Self-Service Portal

**Best for: Empowering team managers**

Web portal for team managers to request quota changes.

#### Features
- Team managers request quota increases
- Approval workflow (finance/admin)
- Usage dashboards
- Email notifications

#### API Example
```python
@app.route('/api/quota/request', methods=['POST'])
def request_quota_change():
    """Team manager submits quota request"""
    data = request.json

    # Create approval request
    create_approval_request(
        requester=data['requester'],
        group=data['group'],
        requested_limit=data['monthly_limit'],
        justification=data['justification']
    )

    # Notify approvers
    send_approval_email(data)
```

**Benefits:**
- ✅ Self-service for managers
- ✅ Approval workflow
- ✅ Audit trail
- ✅ Reduces admin burden

---

### 6. 🤖 Attribute-Based Auto-Assignment

**Best for: Rule-based quota allocation**

Automatically assign quotas based on user attributes (department, job level).

#### Lambda Function (On Login)
```python
def lambda_handler(event, context):
    # Read from JWT token
    department = event['userAttributes']['custom:department']
    job_level = event['userAttributes']['custom:job_level']

    # Calculate quota
    BASE = {
        'Engineering': 300M,
        'ML-Team': 500M,
        'Sales': 100M
    }

    MULTIPLIERS = {
        'IC': 1.0,
        'Manager': 1.5,
        'Director': 2.0,
        'VP': 3.0
    }

    quota = BASE[department] * MULTIPLIERS[job_level]

    # Auto-assign in DynamoDB
    dynamodb.put_item({
        'policy_type': 'user',
        'identifier': email,
        'monthly_token_limit': quota
    })
```

#### Example Calculation
```
User: Jane Doe
Department: Engineering (300M base)
Job Level: Manager (1.5x multiplier)
Auto-assigned: 450M/month
```

**Benefits:**
- ✅ Rule-based automation
- ✅ Scales to any org size
- ✅ Fair allocation
- ✅ Zero manual work

---

## Recommended Architecture

```
┌─────────────────────────────────────────┐
│   Corporate Identity Provider           │
│   (Azure AD / Okta / OneLogin)          │
│   - Users                                │
│   - Groups                               │
│   - Attributes (dept, role)             │
└───────────────┬─────────────────────────┘
                │ SCIM / OIDC Sync
                ↓
┌─────────────────────────────────────────┐
│   AWS Cognito User Pool                 │
│   - Synced users/groups                 │
│   - JWT tokens with group claims        │
└───────────────┬─────────────────────────┘
                │ Authentication
                ↓
┌─────────────────────────────────────────┐
│   CCWB (Reads JWT claims)               │
│   - Applies quota based on groups       │
│   - Enforces limits                     │
└───────────────┬─────────────────────────┘
                │ Policy Lookup
                ↓
┌─────────────────────────────────────────┐
│   DynamoDB (QuotaPolicies)              │
│   - Managed via Terraform/CSV           │
│   - Version controlled in Git           │
└─────────────────────────────────────────┘
```

---

## Strategy Comparison

| Strategy | Setup | Maintenance | Scale | Real-time | Best For |
|----------|-------|-------------|-------|-----------|----------|
| **IdP Sync** | Medium | Low | ⭐⭐⭐⭐⭐ | Yes | Enterprise |
| **Terraform** | Low | Medium | ⭐⭐⭐⭐ | No | DevOps teams |
| **CSV Import** | Low | High | ⭐⭐⭐ | No | Manual reviews |
| **AD Sync** | Medium | Low | ⭐⭐⭐⭐ | Scheduled | AD environments |
| **Self-Service** | High | Low | ⭐⭐⭐⭐⭐ | Yes | Large orgs |
| **Attribute-Based** | Medium | Low | ⭐⭐⭐⭐⭐ | Yes | Rule-based |

---

## Quick Implementation Guide

### Phase 1: Foundation (Week 1)
1. ✅ Configure IdP integration (Cognito ↔ Azure AD/Okta)
2. ✅ Enable SCIM provisioning
3. ✅ Test user/group sync

### Phase 2: Quota Automation (Week 2)
1. ✅ Convert quota policies to Terraform
2. ✅ Set up CI/CD pipeline
3. ✅ Test policy deployments

### Phase 3: Self-Service (Week 3-4)
1. ✅ Build approval workflow
2. ✅ Deploy team manager portal
3. ✅ Enable usage dashboards

### Phase 4: Advanced (Ongoing)
1. ✅ Implement attribute-based assignment
2. ✅ Add anomaly detection
3. ✅ Automate quota optimization

---

## Real-World Example

### Scenario: 500-person company

**Manual Approach (Old Way):**
- Create 500 Cognito users manually
- Assign to groups one-by-one
- Set 50+ quota policies individually
- **Time**: 40 hours/week ongoing
- **Error rate**: High

**Automated Approach (New Way):**
```
IdP Sync (Okta)
    ↓
Users/groups auto-sync
    ↓
Terraform manages quotas
    ↓
Self-service for exceptions
```
- **Setup time**: 1 week
- **Ongoing maintenance**: 2 hours/month
- **Error rate**: Near zero
- **Time saved**: 95%

---

## Key Takeaways

1. 🏆 **Use IdP sync as foundation** - Leverage existing corporate directory
2. 📋 **Manage quotas as code** - Version control with Terraform
3. 📊 **Enable self-service** - Empower team managers
4. 🤖 **Automate everything** - Zero manual user management
5. 📈 **Scale effortlessly** - Works for 10 or 10,000 users

## Getting Started

**Recommended path for most organizations:**

1. **Day 1**: Enable SCIM sync between IdP and Cognito
2. **Day 2**: Convert existing quotas to Terraform
3. **Week 2**: Deploy self-service portal (optional)
4. **Ongoing**: Zero manual work, automatic scaling

**Result**: 95% time savings, zero manual errors, scales to any size.

---

**For complete implementation details, see**: `/workshop/CCWB_AUTOMATION_GUIDE.md`
