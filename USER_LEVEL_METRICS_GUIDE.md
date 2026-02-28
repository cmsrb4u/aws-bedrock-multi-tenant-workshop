# CCWB User-Level Metrics Implementation Guide

## 🎯 The Problem

The current CCWB dashboard shown in the [monitoring documentation](https://github.com/aws-solutions-library-samples/guidance-for-claude-code-with-amazon-bedrock/blob/main/assets/docs/MONITORING.md#cloudwatch-dashboard) displays **tenant-level metrics** (Marketing team, Sales team) but **NOT individual user-level metrics** (john@company.com, alice@marketing.com).

## 📊 Current State vs. Desired State

### Current State (Tenant-Level Only)
- ✅ Metrics grouped by Application Inference Profile (AIP)
- ✅ Team-level aggregation (Marketing vs Sales)
- ❌ No individual user identification
- ❌ No per-user quota tracking
- ❌ No user-specific cost attribution

### Desired State (True User-Level)
- ✅ Individual user metrics (john@company.com: 5,000 tokens)
- ✅ Per-user quota enforcement
- ✅ User-specific dashboards
- ✅ Cost attribution per user
- ✅ User behavior analytics

## 🔧 What's Missing for True User-Level Metrics

### 1. **Authentication & User Identification**
```python
# MISSING: User context extraction
# Current: Bedrock calls have no user identity
# Needed: JWT token with user email

event['requestContext']['authorizer']['claims']['email']  # Not available without auth
```

### 2. **Custom Metrics with User Dimensions**
```python
# MISSING: CloudWatch metrics with UserEmail dimension
# Current metrics only have:
Dimensions: [
    {'Name': 'InferenceProfileId', 'Value': 'tenant_id'}
]

# Needed:
Dimensions: [
    {'Name': 'UserEmail', 'Value': 'alice@marketing.com'},
    {'Name': 'TenantId', 'Value': 'marketing_tenant'}
]
```

### 3. **DynamoDB Tables for Quota Tracking**
```yaml
# MISSING: User quota storage
QuotaPolicies:
  PrimaryKey: UserEmail
  Attributes:
    - DailyTokenLimit
    - MonthlyTokenLimit
    - RateLimitPerMinute

UserQuotaMetrics:
  PrimaryKey: UserEmail
  SortKey: Date
  Attributes:
    - InputTokensUsed
    - OutputTokensUsed
    - APICallCount
```

## 🚀 Implementation Solutions

### Solution 1: Full CCWB Deployment with Auth (Recommended)

#### Step 1: Deploy API Gateway with Cognito
```bash
# Deploy CCWB with authentication enabled
cdk deploy CCWBStack --context auth=cognito
```

#### Step 2: Modify Lambda to Capture User Context
```python
# In your CCWB Lambda function
def lambda_handler(event, context):
    # Extract user from JWT
    user_email = event['requestContext']['authorizer']['claims']['email']

    # Call Bedrock
    response = bedrock.invoke_model(...)

    # Publish custom metric
    cloudwatch.put_metric_data(
        Namespace='CCWB/UserQuota',
        MetricData=[{
            'MetricName': 'UserTokens',
            'Value': response['usage']['total_tokens'],
            'Dimensions': [
                {'Name': 'UserEmail', 'Value': user_email}
            ]
        }]
    )
```

#### Step 3: Create User-Level Dashboard
```python
# Run the enhanced dashboard creator
python create_user_level_dashboard.py
```

### Solution 2: CloudWatch Logs Parsing (Quick Workaround)

#### Step 1: Update Lambda Logging
```python
# Add structured logging to CCWB Lambda
logger.info(json.dumps({
    'userEmail': user_email,
    'inputTokens': input_tokens,
    'outputTokens': output_tokens,
    'timestamp': datetime.utcnow().isoformat()
}))
```

#### Step 2: Create Metric Filters
```python
# Extract metrics from logs
filter_pattern = '[timestamp, request_id, user_email, input_tokens, output_tokens]'
```

#### Step 3: Use CloudWatch Insights
```sql
-- Query user metrics from logs
fields @timestamp, userEmail, inputTokens, outputTokens
| stats sum(inputTokens) as totalInput by userEmail
| sort totalInput desc
```

### Solution 3: Custom Authorizer with Request Context

#### Add Custom Authorizer
```python
def custom_authorizer(event, context):
    # Extract user from header/token
    user_email = extract_user_from_token(event['authorizationToken'])

    return {
        'principalId': user_email,
        'context': {
            'userEmail': user_email,
            'tenantId': get_tenant_id(user_email)
        }
    }
```

## 📋 Implementation Checklist

### Immediate Actions (Can Do Now)
- [ ] Run `create_user_level_dashboard.py` to see the dashboard structure
- [ ] Run `implement_user_metrics_logs.py` to set up log-based metrics
- [ ] Create CloudWatch Insights queries for user analysis

### Required Infrastructure Changes
- [ ] Deploy API Gateway with authentication
- [ ] Add Cognito User Pool or OAuth provider
- [ ] Create DynamoDB tables for quota management
- [ ] Update Lambda to capture user context
- [ ] Implement custom metric publishing

### Dashboard Enhancements
- [ ] Add user selection dropdown
- [ ] Create per-user quota gauges
- [ ] Implement user leaderboard
- [ ] Add cost attribution widgets
- [ ] Create user comparison views

## 🎯 Quick Start Commands

```bash
# 1. Create the enhanced dashboard (shows what's possible)
python create_user_level_dashboard.py

# 2. Implement log-based metrics (interim solution)
python implement_user_metrics_logs.py

# 3. View current metrics (tenant-level only)
python create_quota_dashboard.py
```

## 📊 Dashboard Comparison

### Current Dashboard (Tenant-Level)
```
┌─────────────────────────────────┐
│  Total Tokens (All AIPs)        │
├─────────────────────────────────┤
│  Marketing Team: 50,000 tokens  │
│  Sales Team: 30,000 tokens      │
└─────────────────────────────────┘
```

### Enhanced Dashboard (User-Level)
```
┌─────────────────────────────────┐
│  User Token Usage               │
├─────────────────────────────────┤
│  alice@marketing.com: 15,000    │
│  bob@sales.com: 12,000          │
│  john@company.com: 8,000        │
│  sarah@engineering.com: 5,000   │
└─────────────────────────────────┘
```

## 🔑 Key Takeaways

1. **Current Limitation**: CCWB metrics are at the Application Inference Profile level, not user level
2. **Root Cause**: No user authentication/identification in the request flow
3. **Solution**: Add authentication layer and custom metric publishing
4. **Workaround**: Use CloudWatch Logs Insights to parse user data from logs
5. **Timeline**: Full implementation requires CCWB infrastructure changes (1-2 days)

## 💡 Recommendations

### For POC/Demo
Use the log-based approach with CloudWatch Insights for quick user-level visibility.

### For Production
1. Deploy full CCWB with authentication
2. Implement custom metrics with user dimensions
3. Use DynamoDB for quota management
4. Create comprehensive user-level dashboard

### For Cost Management
- Implement user-level cost attribution
- Set up billing alerts per user/team
- Create chargeback reports

## 📚 Resources

- [CCWB Documentation](https://github.com/aws-solutions-library-samples/guidance-for-claude-code-with-amazon-bedrock)
- [CloudWatch Custom Metrics](https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/publishingMetrics.html)
- [CloudWatch Logs Insights](https://docs.aws.amazon.com/AmazonCloudWatch/latest/logs/AnalyzingLogData.html)
- [API Gateway Authorizers](https://docs.aws.amazon.com/apigateway/latest/developerguide/apigateway-use-lambda-authorizer.html)

## 🆘 Support

For implementation assistance:
1. Review the provided Python scripts
2. Check CloudWatch Logs for CCWB Lambda
3. Verify DynamoDB table creation
4. Test metric filters with sample data
5. Validate dashboard JSON syntax