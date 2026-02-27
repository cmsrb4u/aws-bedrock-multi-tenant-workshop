# Quota Management: CCWB vs Native AWS Solutions

This guide compares the enterprise CCWB quota commands with native AWS solutions for your workshop environment.

---

## 🏢 **Enterprise CCWB Quota Commands**

These require full infrastructure deployment (auth + monitoring + quota stacks).

### Prerequisites
- ✅ OIDC identity provider configured
- ✅ Dashboard stack deployed (ClaudeCodeMetrics DynamoDB)
- ✅ Monitoring stack deployed (OpenTelemetry collector)
- ✅ Quota stack deployed (QuotaPolicies + UserQuotaMetrics DynamoDB)

### Command Examples

#### 1. Set User-Specific Policy
```bash
poetry run ccwb quota set-user john.doe@company.com \
  --monthly-limit 500M \
  --daily-limit 20M \
  --enforcement block
```

**What it does:**
- Creates fine-grained policy for specific user
- Sets monthly limit: 500 million tokens
- Sets daily limit: 20 million tokens
- Blocks access when exceeded

#### 2. Set Group Policy
```bash
poetry run ccwb quota set-group engineering \
  --monthly-limit 400M \
  --daily-limit 15M \
  --enforcement alert
```

**What it does:**
- Applies policy to all users in "engineering" group
- Group membership from JWT claims
- Alert-only mode (no blocking)

#### 3. Set Default Policy
```bash
poetry run ccwb quota set-default \
  --monthly-limit 225M \
  --daily-limit 8M \
  --enforcement block
```

**What it does:**
- Applies to all users without specific/group policy
- Policy precedence: user > group > default

#### 4. List All Policies
```bash
# List all policies
poetry run ccwb quota list

# Filter by type
poetry run ccwb quota list --type group
poetry run ccwb quota list --type user
```

**Output example:**
```
╭──────────────────────────────────────────────────────────────╮
│ Quota Policies                                               │
├──────────────┬───────────┬──────────────┬─────────┬──────────┤
│ Type         │ ID        │ Monthly      │ Daily   │ Mode     │
├──────────────┼───────────┼──────────────┼─────────┼──────────┤
│ user         │ john.doe  │ 500M tokens  │ 20M     │ block    │
│ group        │ eng       │ 400M tokens  │ 15M     │ alert    │
│ default      │ *         │ 225M tokens  │ 8M      │ block    │
╰──────────────┴───────────┴──────────────┴─────────┴──────────╯
```

#### 5. Show Effective Policy
```bash
poetry run ccwb quota show john.doe@company.com --groups "engineering,ml-team"
```

**What it does:**
- Calculates effective policy for user
- Considers user → group → default precedence
- Shows which policy applies

#### 6. View Usage vs Limits
```bash
poetry run ccwb quota usage john.doe@company.com
```

**Output example:**
```
Usage Report for john.doe@company.com

Monthly Usage (May 2026):
  Consumed: 350M tokens (70% of 500M limit)
  Remaining: 150M tokens
  Status: ✅ Within limits

Daily Usage (Today):
  Consumed: 15M tokens (75% of 20M limit)
  Remaining: 5M tokens
  Status: ⚠️ Approaching limit
```

#### 7. Delete Policy
```bash
poetry run ccwb quota delete user john.doe@company.com
poetry run ccwb quota delete group engineering
```

#### 8. Temporarily Unblock User
```bash
poetry run ccwb quota unblock john.doe@company.com --duration 24h
```

**What it does:**
- Allows user to continue despite exceeding quota
- Temporary override (24 hours)
- Useful for emergency access

### Policy Precedence
1. **User policy** (highest priority)
2. **Group policy** (if user is member)
3. **Default policy** (fallback)

### Enforcement Modes
- **alert**: Send notifications, allow continued use
- **block**: Deny credential issuance when exceeded

---

## 🔧 **Native AWS Solutions (Your Workshop)**

These work NOW without additional infrastructure!

### Solution A: CloudWatch Alarms

Monitor token usage and invocations per Application Inference Profile.

#### Create Alarms (Script Provided)
```bash
bash /workshop/setup_monitoring.sh
```

**What it creates:**
- **Tenant A (Marketing) - 3 alarms:**
  - Input token warning (80% of daily limit)
  - Output token warning (80% of daily limit)
  - Invocation count warning (>800/day)

- **Tenant B (Sales) - 3 alarms:**
  - Input token warning (80% of daily limit)
  - Output token warning (80% of daily limit)
  - Invocation count warning (>800/day)

#### Manual Alarm Creation
```bash
# Example: Tenant A input token alarm
aws cloudwatch put-metric-alarm \
  --alarm-name "TenantA-Marketing-InputTokens-Warning" \
  --alarm-description "Tenant A: 80% of daily limit (4.8M tokens)" \
  --namespace "AWS/Bedrock" \
  --metric-name "InputTokenCount" \
  --dimensions Name=InferenceProfileId,Value=5gematyf83m0 \
  --statistic Sum \
  --period 86400 \
  --threshold 4800000 \
  --comparison-operator GreaterThanThreshold \
  --region us-west-2
```

#### View Alarms
```bash
# List all alarms
aws cloudwatch describe-alarms --region us-west-2

# Check specific tenant alarms
aws cloudwatch describe-alarms \
  --alarm-name-prefix "TenantA-" \
  --region us-west-2 \
  --output table
```

### Solution B: AWS Budgets

Track costs per tenant using cost allocation tags.

#### Prerequisites (One-Time)
1. Go to AWS Billing Console → Cost Allocation Tags
2. Activate tags:
   - `tenant`
   - `department`
   - `costcenter`
3. Wait 24 hours for tags to appear in billing

#### Create Budget via Console
1. Go to: https://console.aws.amazon.com/billing/home#/budgets
2. Click "Create budget"
3. Choose "Cost budget"
4. Configure:
   - Name: "TenantA-Marketing-Monthly"
   - Amount: $500/month
   - Filters:
     - Tag: `tenant = tenant_a`
     - Service: Amazon Bedrock
5. Set alerts:
   - 80% threshold → Email
   - 100% threshold → Email

#### Create Budget via CLI

**Step 1: Create budget definition file**
```json
// tenant-a-budget.json
{
  "BudgetName": "TenantA-Marketing-Monthly",
  "BudgetLimit": {
    "Amount": "500",
    "Unit": "USD"
  },
  "TimeUnit": "MONTHLY",
  "BudgetType": "COST",
  "CostFilters": {
    "TagKeyValue": ["user:tenant$tenant_a"],
    "Service": ["Amazon Bedrock"]
  }
}
```

**Step 2: Create notifications file**
```json
// tenant-a-notifications.json
[
  {
    "Notification": {
      "NotificationType": "ACTUAL",
      "ComparisonOperator": "GREATER_THAN",
      "Threshold": 80,
      "ThresholdType": "PERCENTAGE"
    },
    "Subscribers": [
      {
        "SubscriptionType": "EMAIL",
        "Address": "admin@example.com"
      }
    ]
  },
  {
    "Notification": {
      "NotificationType": "ACTUAL",
      "ComparisonOperator": "GREATER_THAN",
      "Threshold": 100,
      "ThresholdType": "PERCENTAGE"
    },
    "Subscribers": [
      {
        "SubscriptionType": "EMAIL",
        "Address": "admin@example.com"
      }
    ]
  }
]
```

**Step 3: Create budget**
```bash
aws budgets create-budget \
  --account-id $(aws sts get-caller-identity --query Account --output text) \
  --budget file://tenant-a-budget.json \
  --notifications-with-subscribers file://tenant-a-notifications.json
```

#### View Budget Status
```bash
# List all budgets
aws budgets describe-budgets \
  --account-id $(aws sts get-caller-identity --query Account --output text)

# Check specific budget
aws budgets describe-budget \
  --account-id $(aws sts get-caller-identity --query Account --output text) \
  --budget-name "TenantA-Marketing-Monthly"
```

### Solution C: Cost Explorer

Query costs by Application Inference Profile tags.

#### Via Console
1. Go to: https://console.aws.amazon.com/cost-management/home#/cost-explorer
2. Set date range (e.g., last 30 days)
3. Group by: Tag → `tenant`
4. Filter: Service = Amazon Bedrock
5. View costs per tenant

#### Via CLI
```bash
# Get costs for last 30 days, grouped by tenant tag
aws ce get-cost-and-usage \
  --time-period Start=$(date -u -d '30 days ago' +%Y-%m-%d),End=$(date -u +%Y-%m-%d) \
  --granularity DAILY \
  --metrics "UnblendedCost" \
  --group-by Type=TAG,Key=tenant \
  --filter file://bedrock-filter.json
```

**bedrock-filter.json:**
```json
{
  "Dimensions": {
    "Key": "SERVICE",
    "Values": ["Amazon Bedrock"]
  }
}
```

---

## 📊 **Comparison Matrix**

| Feature | CCWB Quota Commands | Native AWS Solutions |
|---------|---------------------|---------------------|
| **Deployment** | Requires full stack | No additional infra |
| **User-level policies** | ✅ Yes | ❌ No (tenant-level only) |
| **Group policies** | ✅ Yes | ❌ No |
| **Auto-enforcement** | ✅ Yes (block/alert) | ⚠️ Manual (via alarms) |
| **Token tracking** | ✅ Automatic | ✅ CloudWatch metrics |
| **Cost tracking** | ✅ Via policies | ✅ Via Cost Explorer/Budgets |
| **Daily limits** | ✅ Yes | ✅ Yes (via alarms) |
| **Monthly limits** | ✅ Yes | ✅ Yes (via budgets) |
| **Real-time blocking** | ✅ Yes | ❌ No (alert only) |
| **Usage reports** | ✅ Built-in CLI | ⚠️ Manual queries |
| **Setup complexity** | 🔴 High (OIDC + stacks) | 🟢 Low (native AWS) |
| **Multi-tenant** | ✅ Per-user | ✅ Per-profile/tenant |

---

## 🎯 **Recommendations**

### For Your Workshop
Use **Native AWS Solutions**:
- ✅ No additional deployment needed
- ✅ Application Inference Profiles already provide tenant separation
- ✅ CloudWatch alarms for proactive monitoring
- ✅ AWS Budgets for cost control

### For Enterprise Production
Use **CCWB Quota Commands** when:
- Multiple users per tenant
- Need user-level quotas
- Require automatic blocking
- Want centralized policy management
- Have OIDC authentication infrastructure

---

## 🚀 **Quick Start (Workshop)**

Run the monitoring setup script:
```bash
bash /workshop/setup_monitoring.sh
```

This will:
1. ✅ Create 6 CloudWatch alarms (3 per tenant)
2. ✅ Provide AWS Budgets setup guide
3. ✅ Show monitoring dashboard links

---

## 📚 **Additional Resources**

- [CCWB Quota Monitoring Docs](https://github.com/aws-solutions-library-samples/guidance-for-claude-code-with-amazon-bedrock/blob/main/assets/docs/QUOTA_MONITORING.md)
- [AWS CloudWatch Alarms](https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/AlarmThatSendsEmail.html)
- [AWS Budgets](https://docs.aws.amazon.com/cost-management/latest/userguide/budgets-managing-costs.html)
- [Cost Allocation Tags](https://docs.aws.amazon.com/awsaccountbilling/latest/aboutv2/cost-alloc-tags.html)
