# CCWB User & Team Management Automation Guide

## Overview

This guide shows how to automate CCWB user and team management at scale, eliminating manual administration.

## Problem: Manual Management Doesn't Scale

**Manual Approach Issues:**
- ❌ Creating users one-by-one in Cognito
- ❌ Manually assigning groups
- ❌ Setting quota policies individually
- ❌ No synchronization with corporate directory
- ❌ Stale users when employees leave
- ❌ Error-prone and time-consuming

## Solution: Automated Management

### 1. Identity Provider (IdP) Sync (Recommended)

**Leverage your existing corporate IdP as the source of truth.**

#### AWS Cognito with SCIM Provisioning

Connect Cognito to Azure AD, Okta, or OneLogin:

**Setup:**
```bash
# Enable SCIM provisioning in your IdP
# Configure SCIM endpoint in Cognito User Pool
# Users and groups sync automatically
```

**Benefits:**
- ✅ Users created automatically when added to IdP
- ✅ Groups sync in real-time
- ✅ User deactivation propagates immediately
- ✅ Zero manual user management
- ✅ Single source of truth

#### Direct Okta Integration

**CCWB Profile Configuration:**
```json
{
  "provider_type": "okta",
  "provider_domain": "company.okta.com",
  "client_id": "your-client-id",
  "group_claim": "groups"
}
```

**Automatic Flow:**
1. Cloud Administrator adds user to "Engineering" in Okta
2. User authenticates via CCWB
3. CCWB reads `groups` claim from JWT token
4. Engineering quota policy (400M/month) applies automatically

**No manual steps required!**

### 2. Infrastructure as Code (IaC)

Manage quota policies like infrastructure using Terraform:

**Example: terraform/quotas.tf**
```hcl
# Default organizational policy
resource "aws_dynamodb_table_item" "default_quota" {
  table_name = "QuotaPolicies"
  hash_key   = "policy_type"
  range_key  = "identifier"

  item = jsonencode({
    policy_type         = { S = "default" }
    identifier          = { S = "default" }
    monthly_token_limit = { N = "225000000" }
    daily_token_limit   = { N = "8000000" }
    enforcement_mode    = { S = "alert" }
    enabled             = { BOOL = true }
  })
}

# Group quotas
variable "group_quotas" {
  type = map(object({
    monthly_limit = number
    daily_limit   = number
  }))
  default = {
    "engineering" = { monthly_limit = 400000000, daily_limit = 0 }
    "ml-team"     = { monthly_limit = 600000000, daily_limit = 25000000 }
    "product"     = { monthly_limit = 225000000, daily_limit = 8000000 }
  }
}

resource "aws_dynamodb_table_item" "group_quotas" {
  for_each   = var.group_quotas
  table_name = "QuotaPolicies"
  hash_key   = "policy_type"
  range_key  = "identifier"

  item = jsonencode({
    policy_type         = { S = "group" }
    identifier          = { S = each.key }
    monthly_token_limit = { N = tostring(each.value.monthly_limit) }
    daily_token_limit   = { N = tostring(each.value.daily_limit) }
    enforcement_mode    = { S = "alert" }
    enabled             = { BOOL = true }
  })
}
```

**Workflow:**
```bash
# 1. Update quota in Git
vim terraform/quotas.tf
git commit -m "Increase engineering quota to 500M"
git push

# 2. CI/CD deploys automatically
terraform apply -auto-approve

# 3. Changes live in seconds
```

**Benefits:**
- ✅ Version control (Git history)
- ✅ Change review (pull requests)
- ✅ Automated deployment (CI/CD)
- ✅ Rollback capability
- ✅ Audit trail

### 3. Bulk Import/Export

For large-scale policy updates:

**Create CSV file: quotas.csv**
```csv
type,identifier,monthly_limit,daily_limit,enforcement_mode,enabled
default,default,225M,8M,alert,true
group,engineering,400M,,alert,true
group,ml-team,600M,25M,alert,true
group,sales,100M,5M,block,true
user,ceo@company.com,1000M,50M,alert,true
```

**Bulk Operations:**
```bash
# Import 100+ policies at once
poetry run ccwb quota import quotas.csv

# Export for backup/audit
poetry run ccwb quota export backup-$(date +%Y%m%d).csv

# Quarterly review process:
# 1. Export current policies
poetry run ccwb quota export current-policies.csv

# 2. Team Leads update in Excel/Google Sheets

# 3. Re-import updated policies
poetry run ccwb quota import updated-policies.csv
```

### 4. Automated Directory Sync

Sync Active Directory/LDAP to Cognito daily:

**Python Script: sync-ad-to-cognito.py**
```python
#!/usr/bin/env python3
import boto3
import ldap3
from datetime import datetime

def sync_ad_groups():
    """Sync AD groups to Cognito, then update CCWB quotas"""

    # 1. Connect to Active Directory
    server = ldap3.Server("ldap://corporate-ad.company.com")
    conn = ldap3.Connection(server, "service@company.com", "password")
    conn.bind()

    # 2. Get groups and members
    conn.search('DC=company,DC=com', '(objectClass=group)',
                attributes=['cn', 'member'])

    cognito = boto3.client('cognito-idp', region_name='us-west-2')

    for entry in conn.entries:
        group_name = str(entry.cn)

        # 3. Create group in Cognito
        try:
            cognito.create_group(
                GroupName=group_name,
                UserPoolId='us-west-2_qsKNoAXWR'
            )
        except cognito.exceptions.GroupExistsException:
            pass

        # 4. Add members
        for member_dn in entry.member:
            email = extract_email(member_dn)
            cognito.admin_add_user_to_group(
                UserPoolId='us-west-2_qsKNoAXWR',
                Username=email,
                GroupName=group_name
            )

# Schedule: Run daily at 2 AM
# crontab: 0 2 * * * /usr/bin/python3 sync-ad-to-cognito.py
```

**Deploy as Lambda:**
```bash
# Run automatically via EventBridge
aws events put-rule \
  --name "DailyADSync" \
  --schedule-expression "cron(0 2 * * ? *)"
```

### 5. Self-Service Portal

Build a web portal for Team Leads:

**Features:**
- Team Leads request quota increases
- Automatic approval workflow
- Real-time usage dashboards
- Email notifications

**API Example:**
```python
@app.route('/api/quota/request', methods=['POST'])
def request_quota_change():
    """Team Lead requests quota increase"""
    data = request.json

    # Verify Team Lead has permission for group
    if not has_permission(data['requester'], data['group']):
        return {"error": "Unauthorized"}, 403

    # Create approval request
    create_approval_request(
        requester=data['requester'],
        group=data['group'],
        requested_limit=data['monthly_limit'],
        justification=data['justification']
    )

    # Notify approvers
    send_approval_email(data)

    return {"message": "Request submitted"}
```

### 6. Attribute-Based Automatic Assignment

Assign quotas automatically based on user attributes:

**Lambda Function (triggered on login):**
```python
def lambda_handler(event, context):
    """Auto-assign quota based on user attributes"""

    # Read from JWT token
    department = event['request']['userAttributes']['custom:department']
    job_level = event['request']['userAttributes']['custom:job_level']

    # Calculate quota
    quota = calculate_quota(department, job_level)

    # Auto-assign in DynamoDB
    dynamodb.Table('QuotaPolicies').put_item(Item={
        'policy_type': 'user',
        'identifier': event['userName'],
        'monthly_token_limit': quota['monthly'],
        'auto_assigned': True
    })
```

**Business Rules:**
```python
def calculate_quota(department, job_level):
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

    return BASE[department] * MULTIPLIERS[job_level]
```

## Recommended Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Corporate Identity Provider              │
│              (Azure AD / Okta / OneLogin)                   │
└────────────────────────┬────────────────────────────────────┘
                         │ SCIM / OIDC Sync
                         ↓
┌─────────────────────────────────────────────────────────────┐
│                    AWS Cognito User Pool                    │
│                  (Users + Groups synced)                    │
└────────────────────────┬────────────────────────────────────┘
                         │ Authentication
                         ↓
┌─────────────────────────────────────────────────────────────┐
│                         CCWB Layer                          │
│          (Reads groups from JWT, applies quotas)            │
└────────────────────────┬────────────────────────────────────┘
                         │ Quota Check
                         ↓
┌─────────────────────────────────────────────────────────────┐
│              DynamoDB (QuotaPolicies)                       │
│           Managed via Terraform / CI/CD                     │
└─────────────────────────────────────────────────────────────┘
```

## Automation Comparison

| Approach | Setup Effort | Maintenance | Scale | Real-time |
|----------|--------------|-------------|-------|-----------|
| **IdP Sync (SCIM)** | Medium | Low | ⭐⭐⭐⭐⭐ | Yes |
| **Terraform IaC** | Low | Medium | ⭐⭐⭐⭐ | No |
| **Bulk CSV Import** | Low | High | ⭐⭐⭐ | No |
| **AD/LDAP Sync Script** | Medium | Low | ⭐⭐⭐⭐ | Scheduled |
| **Self-Service Portal** | High | Low | ⭐⭐⭐⭐⭐ | Yes |
| **Attribute-Based** | Medium | Low | ⭐⭐⭐⭐⭐ | Yes |

## Implementation Roadmap

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
2. ✅ Deploy Team Lead portal
3. ✅ Enable usage dashboards

### Phase 4: Advanced Automation (Ongoing)
1. ✅ Implement attribute-based assignment
2. ✅ Add anomaly detection
3. ✅ Automate quota optimization

## Best Practices

1. **Single Source of Truth**: Use IdP as the authoritative source for users/groups
2. **Infrastructure as Code**: Manage quotas in Git with Terraform
3. **Separation of Concerns**: Cloud Administrator manages users, FinOps Lead approves quotas
4. **Audit Everything**: Log all changes to quota policies
5. **Test in Dev**: Validate sync scripts in non-production first
6. **Gradual Rollout**: Start with one team, expand incrementally

## Summary

**Don't manage CCWB manually!** Automate using:

1. **IdP Sync** - Users/groups sync automatically
2. **Terraform** - Quota policies as code
3. **Bulk Import** - Large-scale updates
4. **Self-Service** - Team Leads request changes
5. **Attribute-Based** - Automatic assignment by role

**Result**: Zero manual user management, scalable to 1000+ users.

---

**Files Created:**
- `/tmp/ccwb-quota-terraform.tf` - Terraform example
- `/tmp/sync-groups-to-cognito.py` - AD sync script
- `/tmp/quota-portal-api.py` - Self-service API
- `/tmp/dynamic-quota-assignment.py` - Attribute-based Lambda
