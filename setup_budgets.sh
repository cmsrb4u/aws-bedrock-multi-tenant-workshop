#!/bin/bash
################################################################################
# AWS Budgets Setup Script
# Creates budgets for Tenant A and Tenant B with email notifications
################################################################################

set -e

echo "================================================================================"
echo "💰 AWS Budgets Setup for Multi-Tenant Application Inference Profiles"
echo "================================================================================"
echo ""

# Get AWS Account ID
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
echo "📋 AWS Account ID: $ACCOUNT_ID"
echo ""

################################################################################
# Step 1: Check Cost Allocation Tags Status
################################################################################

echo "================================================================================"
echo "📊 Step 1: Checking Cost Allocation Tags"
echo "================================================================================"
echo ""

echo "⚠️  IMPORTANT: Cost allocation tags must be activated before budgets can filter by them."
echo ""
echo "🔗 To activate tags manually:"
echo "   1. Go to: https://console.aws.amazon.com/billing/home#/tags"
echo "   2. Find and activate these tags:"
echo "      ☑ tenant"
echo "      ☑ department"
echo "      ☑ costcenter"
echo "   3. Wait 24 hours for tags to appear in billing data"
echo ""

# Check if tags are already active (note: this requires Billing API permissions)
echo "Attempting to check tag activation status..."
aws ce list-cost-allocation-tags \
  --status Active \
  --region us-east-1 \
  2>/dev/null | jq -r '.CostAllocationTags[] | select(.TagKey == "tenant" or .TagKey == "department" or .TagKey == "costcenter") | "  ✅ Tag activated: \(.TagKey)"' \
  || echo "  ⚠️  Unable to check tag status (may require additional permissions)"

echo ""
read -p "Press Enter to continue with budget creation (or Ctrl+C to exit)..."
echo ""

################################################################################
# Step 2: Create Budget for Tenant A (Marketing)
################################################################################

echo "================================================================================"
echo "💼 Step 2: Creating Budget for Tenant A (Marketing)"
echo "================================================================================"
echo ""

echo "Budget Configuration:"
echo "  Name: TenantA-Marketing-Monthly"
echo "  Amount: $500/month"
echo "  Filter: tenant=tenant_a, Service=Amazon Bedrock"
echo "  Alerts: 80% and 100% thresholds"
echo ""

# Check if budget already exists
if aws budgets describe-budget \
  --account-id $ACCOUNT_ID \
  --budget-name "TenantA-Marketing-Monthly" \
  --region us-east-1 \
  >/dev/null 2>&1; then
  echo "⚠️  Budget 'TenantA-Marketing-Monthly' already exists."
  read -p "Do you want to delete and recreate it? (y/N): " -n 1 -r
  echo
  if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "🗑️  Deleting existing budget..."
    aws budgets delete-budget \
      --account-id $ACCOUNT_ID \
      --budget-name "TenantA-Marketing-Monthly" \
      --region us-east-1
    echo "✅ Existing budget deleted"
  else
    echo "⏭️  Skipping Tenant A budget creation"
    SKIP_TENANT_A=true
  fi
fi

if [ "$SKIP_TENANT_A" != "true" ]; then
  echo "🔨 Creating budget..."
  aws budgets create-budget \
    --account-id $ACCOUNT_ID \
    --budget file:///workshop/tenant-a-budget.json \
    --notifications-with-subscribers file:///workshop/tenant-a-notifications.json \
    --region us-east-1

  echo "✅ Budget created successfully for Tenant A!"
fi

echo ""

################################################################################
# Step 3: Create Budget for Tenant B (Sales)
################################################################################

echo "================================================================================"
echo "💼 Step 3: Creating Budget for Tenant B (Sales)"
echo "================================================================================"
echo ""

echo "Budget Configuration:"
echo "  Name: TenantB-Sales-Monthly"
echo "  Amount: $750/month"
echo "  Filter: tenant=tenant_b, Service=Amazon Bedrock"
echo "  Alerts: 80% and 100% thresholds"
echo ""

# Check if budget already exists
if aws budgets describe-budget \
  --account-id $ACCOUNT_ID \
  --budget-name "TenantB-Sales-Monthly" \
  --region us-east-1 \
  >/dev/null 2>&1; then
  echo "⚠️  Budget 'TenantB-Sales-Monthly' already exists."
  read -p "Do you want to delete and recreate it? (y/N): " -n 1 -r
  echo
  if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "🗑️  Deleting existing budget..."
    aws budgets delete-budget \
      --account-id $ACCOUNT_ID \
      --budget-name "TenantB-Sales-Monthly" \
      --region us-east-1
    echo "✅ Existing budget deleted"
  else
    echo "⏭️  Skipping Tenant B budget creation"
    SKIP_TENANT_B=true
  fi
fi

if [ "$SKIP_TENANT_B" != "true" ]; then
  echo "🔨 Creating budget..."
  aws budgets create-budget \
    --account-id $ACCOUNT_ID \
    --budget file:///workshop/tenant-b-budget.json \
    --notifications-with-subscribers file:///workshop/tenant-b-notifications.json \
    --region us-east-1

  echo "✅ Budget created successfully for Tenant B!"
fi

echo ""

################################################################################
# Step 4: Verify Budgets
################################################################################

echo "================================================================================"
echo "📊 Step 4: Verifying Created Budgets"
echo "================================================================================"
echo ""

echo "Listing all budgets in account..."
aws budgets describe-budgets \
  --account-id $ACCOUNT_ID \
  --region us-east-1 \
  --query 'Budgets[*].[BudgetName,BudgetLimit.Amount,BudgetLimit.Unit,TimeUnit]' \
  --output table

echo ""

################################################################################
# Step 5: Show Budget Details
################################################################################

echo "================================================================================"
echo "📈 Step 5: Budget Details"
echo "================================================================================"
echo ""

if [ "$SKIP_TENANT_A" != "true" ]; then
  echo "Tenant A (Marketing) Budget:"
  aws budgets describe-budget \
    --account-id $ACCOUNT_ID \
    --budget-name "TenantA-Marketing-Monthly" \
    --region us-east-1 \
    --query 'Budget.{Name:BudgetName,Amount:BudgetLimit.Amount,Period:TimeUnit,Filters:CostFilters}' \
    --output json | jq '.'
  echo ""
fi

if [ "$SKIP_TENANT_B" != "true" ]; then
  echo "Tenant B (Sales) Budget:"
  aws budgets describe-budget \
    --account-id $ACCOUNT_ID \
    --budget-name "TenantB-Sales-Monthly" \
    --region us-east-1 \
    --query 'Budget.{Name:BudgetName,Amount:BudgetLimit.Amount,Period:TimeUnit,Filters:CostFilters}' \
    --output json | jq '.'
  echo ""
fi

################################################################################
# Summary
################################################################################

echo "================================================================================"
echo "✅ Budget Setup Complete!"
echo "================================================================================"
echo ""

echo "📊 Summary:"
if [ "$SKIP_TENANT_A" != "true" ]; then
  echo "  ✅ Tenant A (Marketing): $500/month budget created"
fi
if [ "$SKIP_TENANT_B" != "true" ]; then
  echo "  ✅ Tenant B (Sales): $750/month budget created"
fi
echo "  📧 Email notifications configured for 80% and 100% thresholds"
echo "  🏷️  Filtered by: tenant tags + Amazon Bedrock service"
echo ""

echo "⚠️  IMPORTANT NOTES:"
echo "  1. Email subscribers must CONFIRM their subscription via email"
echo "  2. Cost allocation tags must be activated (wait 24 hours for data)"
echo "  3. Budgets track costs starting from the current month"
echo "  4. Check AWS Budgets console for real-time status"
echo ""

echo "🔗 Quick Links:"
echo "  AWS Budgets Console:"
echo "    https://console.aws.amazon.com/billing/home#/budgets"
echo ""
echo "  Cost Allocation Tags:"
echo "    https://console.aws.amazon.com/billing/home#/tags"
echo ""
echo "  Cost Explorer (by tenant):"
echo "    https://console.aws.amazon.com/cost-management/home#/cost-explorer"
echo ""

echo "💡 Next Steps:"
echo "  1. Check your email and confirm SNS subscription"
echo "  2. Activate cost allocation tags in AWS Billing console"
echo "  3. Wait 24 hours for historical cost data to populate"
echo "  4. Review budgets in the AWS Budgets console"
echo ""

################################################################################
# Optional: Show current month's costs
################################################################################

echo "================================================================================"
echo "💵 Current Month Costs (Optional Preview)"
echo "================================================================================"
echo ""

read -p "Would you like to see current month costs? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
  echo ""
  echo "Fetching costs for current month..."

  START_DATE=$(date -u +%Y-%m-01)
  END_DATE=$(date -u +%Y-%m-%d)

  echo ""
  echo "📊 Bedrock costs from $START_DATE to $END_DATE:"

  # Create filter file
  cat > /tmp/bedrock-filter.json << EOF
{
  "Dimensions": {
    "Key": "SERVICE",
    "Values": ["Amazon Bedrock"]
  }
}
EOF

  aws ce get-cost-and-usage \
    --time-period Start=$START_DATE,End=$END_DATE \
    --granularity MONTHLY \
    --metrics "UnblendedCost" \
    --group-by Type=DIMENSION,Key=SERVICE \
    --filter file:///tmp/bedrock-filter.json \
    --region us-east-1 \
    --query 'ResultsByTime[0].Groups[*].[Keys[0],Metrics.UnblendedCost.Amount]' \
    --output table

  echo ""
  echo "Note: Tag-based filtering will be available 24 hours after activating cost allocation tags"
fi

echo ""
echo "================================================================================"
echo "🎉 Setup Complete!"
echo "================================================================================"
