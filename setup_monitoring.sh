#!/bin/bash
################################################################################
# Workshop Monitoring Setup
# Creates CloudWatch Alarms and shows AWS Budgets setup for tenant tracking
################################################################################

echo "================================================================================"
echo "🎯 Part A: Creating CloudWatch Alarms for Tenant Monitoring"
echo "================================================================================"
echo ""

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
REGION="us-west-2"
TENANT_A_PROFILE_ID="5gematyf83m0"
TENANT_B_PROFILE_ID="yku79b5wumnr"

# Daily limits (adjust as needed)
DAILY_INPUT_TOKEN_LIMIT=6000000   # 6M tokens
DAILY_OUTPUT_TOKEN_LIMIT=6000000  # 6M tokens
DAILY_INVOCATION_LIMIT=1000       # 1000 calls

echo "📊 Configuration:"
echo "   Region: $REGION"
echo "   Tenant A Profile: $TENANT_A_PROFILE_ID (Marketing)"
echo "   Tenant B Profile: $TENANT_B_PROFILE_ID (Sales)"
echo "   Daily Input Token Limit: $(numfmt --to=si $DAILY_INPUT_TOKEN_LIMIT) tokens"
echo "   Daily Output Token Limit: $(numfmt --to=si $DAILY_OUTPUT_TOKEN_LIMIT) tokens"
echo "   Daily Invocation Limit: $DAILY_INVOCATION_LIMIT calls"
echo ""

################################################################################
# Tenant A (Marketing) Alarms
################################################################################

echo -e "${BLUE}Creating alarms for Tenant A (Marketing)...${NC}"

# Tenant A - Input Token Warning (80%)
echo "  ⏳ Creating InputTokens alarm..."
aws cloudwatch put-metric-alarm \
  --alarm-name "TenantA-Marketing-InputTokens-Warning" \
  --alarm-description "Tenant A Marketing: 80% of daily input token limit (4.8M tokens)" \
  --namespace "AWS/Bedrock" \
  --metric-name "InputTokenCount" \
  --dimensions Name=InferenceProfileId,Value=$TENANT_A_PROFILE_ID \
  --statistic Sum \
  --period 86400 \
  --evaluation-periods 1 \
  --threshold 4800000 \
  --comparison-operator GreaterThanThreshold \
  --treat-missing-data notBreaching \
  --region $REGION \
  --tags Key=tenant,Value=tenant_a Key=department,Value=marketing Key=alarm-type,Value=token-warning \
  > /dev/null 2>&1

echo -e "     ${GREEN}✅ Input token alarm created${NC}"

# Tenant A - Output Token Warning (80%)
echo "  ⏳ Creating OutputTokens alarm..."
aws cloudwatch put-metric-alarm \
  --alarm-name "TenantA-Marketing-OutputTokens-Warning" \
  --alarm-description "Tenant A Marketing: 80% of daily output token limit (4.8M tokens)" \
  --namespace "AWS/Bedrock" \
  --metric-name "OutputTokenCount" \
  --dimensions Name=InferenceProfileId,Value=$TENANT_A_PROFILE_ID \
  --statistic Sum \
  --period 86400 \
  --evaluation-periods 1 \
  --threshold 4800000 \
  --comparison-operator GreaterThanThreshold \
  --treat-missing-data notBreaching \
  --region $REGION \
  --tags Key=tenant,Value=tenant_a Key=department,Value=marketing Key=alarm-type,Value=token-warning \
  > /dev/null 2>&1

echo -e "     ${GREEN}✅ Output token alarm created${NC}"

# Tenant A - Invocation Warning
echo "  ⏳ Creating Invocations alarm..."
aws cloudwatch put-metric-alarm \
  --alarm-name "TenantA-Marketing-Invocations-Warning" \
  --alarm-description "Tenant A Marketing: High invocation count (>800/day)" \
  --namespace "AWS/Bedrock" \
  --metric-name "Invocations" \
  --dimensions Name=InferenceProfileId,Value=$TENANT_A_PROFILE_ID \
  --statistic Sum \
  --period 86400 \
  --evaluation-periods 1 \
  --threshold 800 \
  --comparison-operator GreaterThanThreshold \
  --treat-missing-data notBreaching \
  --region $REGION \
  --tags Key=tenant,Value=tenant_a Key=department,Value=marketing Key=alarm-type,Value=invocation-warning \
  > /dev/null 2>&1

echo -e "     ${GREEN}✅ Invocation alarm created${NC}"

echo ""

################################################################################
# Tenant B (Sales) Alarms
################################################################################

echo -e "${BLUE}Creating alarms for Tenant B (Sales)...${NC}"

# Tenant B - Input Token Warning (80%)
echo "  ⏳ Creating InputTokens alarm..."
aws cloudwatch put-metric-alarm \
  --alarm-name "TenantB-Sales-InputTokens-Warning" \
  --alarm-description "Tenant B Sales: 80% of daily input token limit (4.8M tokens)" \
  --namespace "AWS/Bedrock" \
  --metric-name "InputTokenCount" \
  --dimensions Name=InferenceProfileId,Value=$TENANT_B_PROFILE_ID \
  --statistic Sum \
  --period 86400 \
  --evaluation-periods 1 \
  --threshold 4800000 \
  --comparison-operator GreaterThanThreshold \
  --treat-missing-data notBreaching \
  --region $REGION \
  --tags Key=tenant,Value=tenant_b Key=department,Value=sales Key=alarm-type,Value=token-warning \
  > /dev/null 2>&1

echo -e "     ${GREEN}✅ Input token alarm created${NC}"

# Tenant B - Output Token Warning (80%)
echo "  ⏳ Creating OutputTokens alarm..."
aws cloudwatch put-metric-alarm \
  --alarm-name "TenantB-Sales-OutputTokens-Warning" \
  --alarm-description "Tenant B Sales: 80% of daily output token limit (4.8M tokens)" \
  --namespace "AWS/Bedrock" \
  --metric-name "OutputTokenCount" \
  --dimensions Name=InferenceProfileId,Value=$TENANT_B_PROFILE_ID \
  --statistic Sum \
  --period 86400 \
  --evaluation-periods 1 \
  --threshold 4800000 \
  --comparison-operator GreaterThanThreshold \
  --treat-missing-data notBreaching \
  --region $REGION \
  --tags Key=tenant,Value=tenant_b Key=department,Value=sales Key=alarm-type,Value=token-warning \
  > /dev/null 2>&1

echo -e "     ${GREEN}✅ Output token alarm created${NC}"

# Tenant B - Invocation Warning
echo "  ⏳ Creating Invocations alarm..."
aws cloudwatch put-metric-alarm \
  --alarm-name "TenantB-Sales-Invocations-Warning" \
  --alarm-description "Tenant B Sales: High invocation count (>800/day)" \
  --namespace "AWS/Bedrock" \
  --metric-name "Invocations" \
  --dimensions Name=InferenceProfileId,Value=$TENANT_B_PROFILE_ID \
  --statistic Sum \
  --period 86400 \
  --evaluation-periods 1 \
  --threshold 800 \
  --comparison-operator GreaterThanThreshold \
  --treat-missing-data notBreaching \
  --region $REGION \
  --tags Key=tenant,Value=tenant_b Key=department,Value=sales Key=alarm-type,Value=invocation-warning \
  > /dev/null 2>&1

echo -e "     ${GREEN}✅ Invocation alarm created${NC}"

echo ""
echo -e "${GREEN}🎉 All CloudWatch alarms created successfully!${NC}"
echo ""

################################################################################
# List Created Alarms
################################################################################

echo "================================================================================"
echo "📊 Created Alarms Summary"
echo "================================================================================"
echo ""

aws cloudwatch describe-alarms \
  --alarm-names \
    "TenantA-Marketing-InputTokens-Warning" \
    "TenantA-Marketing-OutputTokens-Warning" \
    "TenantA-Marketing-Invocations-Warning" \
    "TenantB-Sales-InputTokens-Warning" \
    "TenantB-Sales-OutputTokens-Warning" \
    "TenantB-Sales-Invocations-Warning" \
  --region $REGION \
  --query 'MetricAlarms[*].[AlarmName,StateValue,Threshold]' \
  --output table

echo ""
echo "================================================================================"
echo "🎯 Part B: AWS Budgets Setup Guide"
echo "================================================================================"
echo ""

cat << 'BUDGETS'
AWS Budgets allow you to set cost thresholds and receive alerts when exceeded.
Since your Application Inference Profiles have cost allocation tags, you can
create separate budgets for each tenant.

📋 Setup Steps:

1. Activate Cost Allocation Tags (one-time setup):
   ---------------------------------------------------
   a. Go to: https://console.aws.amazon.com/billing/home#/tags
   b. Find and activate these tags:
      ☑ tenant
      ☑ department
      ☑ costcenter
   c. Wait 24 hours for tags to appear in billing data

2. Create Budget for Tenant A (Marketing):
   ------------------------------------------
   a. Go to: https://console.aws.amazon.com/billing/home#/budgets
   b. Click "Create budget"
   c. Choose "Cost budget"
   d. Configure:
      - Budget name: "TenantA-Marketing-Monthly"
      - Period: Monthly
      - Start month: Current month
      - Budgeted amount: $500 (adjust as needed)
   e. Set filters:
      - Tag: tenant = tenant_a
      - Service: Amazon Bedrock
   f. Configure alerts:
      - 80% threshold → Email notification
      - 100% threshold → Email notification
   g. Add email addresses for alerts
   h. Create budget

3. Create Budget for Tenant B (Sales):
   ---------------------------------------
   Repeat step 2 with:
   - Budget name: "TenantB-Sales-Monthly"
   - Tag filter: tenant = tenant_b
   - Adjust amount as needed

4. Create Department-Level Budgets (Optional):
   ----------------------------------------------
   - Filter by: department = marketing
   - Filter by: department = sales
   - Useful for broader cost tracking

📊 Budget Types Available:
   • Cost Budget - Track spending against a fixed amount
   • Usage Budget - Track token usage directly
   • RI/Savings Plans Budget - Track reserved capacity

💡 Best Practices:
   • Set 80% warning, 100% critical thresholds
   • Add multiple notification emails
   • Review budgets monthly
   • Adjust limits based on actual usage patterns

🔗 Direct Links:
   AWS Budgets Console:
   https://console.aws.amazon.com/billing/home#/budgets

   Cost Allocation Tags:
   https://console.aws.amazon.com/billing/home#/tags

   Cost Explorer (filter by tags):
   https://console.aws.amazon.com/cost-management/home#/cost-explorer

BUDGETS

echo ""
echo "================================================================================"
echo "🔧 AWS CLI Commands for Budget Creation"
echo "================================================================================"
echo ""

cat << 'BUDGET_CLI'
# Create budget for Tenant A using AWS CLI:

aws budgets create-budget \
  --account-id $(aws sts get-caller-identity --query Account --output text) \
  --budget file://tenant-a-budget.json \
  --notifications-with-subscribers file://tenant-a-notifications.json

# tenant-a-budget.json:
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

# tenant-a-notifications.json:
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
  }
]

BUDGET_CLI

echo ""
echo "================================================================================"
echo "📊 Monitoring Dashboard Links"
echo "================================================================================"
echo ""
echo "CloudWatch Alarms:"
echo "  https://${REGION}.console.aws.amazon.com/cloudwatch/home?region=${REGION}#alarmsV2:"
echo ""
echo "CloudWatch Metrics (Tenant A):"
echo "  https://${REGION}.console.aws.amazon.com/cloudwatch/home?region=${REGION}#metricsV2:graph=~();query=~(~(~'*7bAWS*2fBedrock*2cInferenceProfileId*7d~'${TENANT_A_PROFILE_ID})"
echo ""
echo "CloudWatch Metrics (Tenant B):"
echo "  https://${REGION}.console.aws.amazon.com/cloudwatch/home?region=${REGION}#metricsV2:graph=~();query=~(~(~'*7bAWS*2fBedrock*2cInferenceProfileId*7d~'${TENANT_B_PROFILE_ID})"
echo ""
echo "Cost Explorer:"
echo "  https://console.aws.amazon.com/cost-management/home#/cost-explorer"
echo ""

echo "================================================================================"
echo "✅ Setup Complete!"
echo "================================================================================"
echo ""
echo "Summary:"
echo "  ✅ 6 CloudWatch alarms created (3 per tenant)"
echo "  ✅ AWS Budgets setup guide provided"
echo "  ✅ Monitoring dashboard links ready"
echo ""
echo "Next Steps:"
echo "  1. Configure SNS topics for alarm notifications (optional)"
echo "  2. Activate cost allocation tags in AWS Billing console"
echo "  3. Create AWS Budgets for each tenant"
echo "  4. Review alarms in CloudWatch console"
echo ""
