#!/bin/bash
set -euo pipefail

# ═══════════════════════════════════════════════════════════════════════════════
# Deploy Server-Side Bedrock Usage Tracking — Full Production Stack
# ═══════════════════════════════════════════════════════════════════════════════

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
STACK_NAME="bedrock-server-side-tracking"
REGION="${AWS_REGION:-us-west-2}"

echo "════════════════════════════════════════════════════════════════════════"
echo "🚀 Deploying Server-Side Bedrock Usage Tracking"
echo "   Stack:  $STACK_NAME"
echo "   Region: $REGION"
echo "════════════════════════════════════════════════════════════════════════"

# ── Prompt for alert email ──
if [ -z "${ALERT_EMAIL:-}" ]; then
    read -rp "📧 Alert email for quota breach notifications: " ALERT_EMAIL
fi

# ── Step 1: Deploy CloudFormation (SAM build + deploy) ──
echo ""
echo "━━━ Step 1: Building and deploying infrastructure ━━━"

if command -v sam &> /dev/null; then
    cd "$SCRIPT_DIR"
    sam build --template-file infra.yaml
    sam deploy \
        --stack-name "$STACK_NAME" \
        --region "$REGION" \
        --capabilities CAPABILITY_NAMED_IAM \
        --parameter-overrides "AlertEmail=$ALERT_EMAIL" \
        --resolve-s3 \
        --no-confirm-changeset
else
    echo "⚠️  SAM CLI not found. Install: https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/install-sam-cli.html"
    echo "   Or deploy manually:"
    echo "   sam build --template-file $SCRIPT_DIR/infra.yaml"
    echo "   sam deploy --stack-name $STACK_NAME --capabilities CAPABILITY_NAMED_IAM --parameter-overrides AlertEmail=$ALERT_EMAIL --resolve-s3"
    exit 1
fi

# ── Step 2: Create AIPs + enable logging ──
echo ""
echo "━━━ Step 2: Creating per-user AIPs and enabling logging ━━━"
cd "$SCRIPT_DIR/.."
python "$SCRIPT_DIR/setup_server_side_tracking.py"

# ── Step 3: Seed quota policies + create alarms ──
echo ""
echo "━━━ Step 3: Seeding quota policies and creating alarms ━━━"
python "$SCRIPT_DIR/seed_policies_and_alarms.py"

# ── Step 4: Generate test traffic ──
echo ""
echo "━━━ Step 4: Generating test traffic ━━━"
python "$SCRIPT_DIR/server_side_tracking_demo.py"

# ── Step 5: Wait and validate ──
echo ""
echo "━━━ Step 5: Waiting 60s for metrics propagation ━━━"
sleep 60
python "$SCRIPT_DIR/validate_pipeline.py"

# ── Step 6: Deploy dashboard ──
echo ""
echo "━━━ Step 6: Deploying CloudWatch dashboard ━━━"
python "$SCRIPT_DIR/deploy_dashboard.py"

# ── Step 7: Run Glue crawler ──
echo ""
echo "━━━ Step 7: Starting Glue crawler (first run) ━━━"
aws glue start-crawler --name bedrock-invocation-log-crawler --region "$REGION" 2>/dev/null || echo "   ⚠️  Crawler may already be running or no data yet"

echo ""
echo "════════════════════════════════════════════════════════════════════════"
echo "✅ Deployment Complete"
echo "════════════════════════════════════════════════════════════════════════"
echo ""
echo "   📧 Confirm the SNS subscription email sent to: $ALERT_EMAIL"
echo ""
echo "   📊 Dashboard:"
echo "   https://$REGION.console.aws.amazon.com/cloudwatch/home?region=$REGION#dashboards/dashboard/Bedrock-ServerSide-UserTracking"
echo ""
echo "   🔍 Athena (after crawler completes):"
echo "   https://$REGION.console.aws.amazon.com/athena/home?region=$REGION#/query-editor"
echo "   Workgroup: bedrock-tracking | Database: bedrock_tracking"
echo ""
echo "   🗑️  Teardown:"
echo "   aws cloudformation delete-stack --stack-name $STACK_NAME --region $REGION"
echo "════════════════════════════════════════════════════════════════════════"
