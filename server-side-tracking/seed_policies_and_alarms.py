"""
Seed DynamoDB Quota Policies and Create Per-User CloudWatch Alarms

Run after infra.yaml is deployed and setup_server_side_tracking.py has created AIPs.

Creates:
1. Quota policies in DynamoDB (user, group, default)
2. CloudWatch Alarms per user at 80% and 95% thresholds
3. Alarms route to SNS → Lambda enforcement function
"""

import boto3
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from lab_helpers.config import Region

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
STACK_NAME = "bedrock-server-side-tracking"

cfn = boto3.client("cloudformation", region_name=Region)
dynamodb = boto3.resource("dynamodb", region_name=Region)
cloudwatch = boto3.client("cloudwatch", region_name=Region)

# ── Read CFN outputs ──
try:
    stack = cfn.describe_stacks(StackName=STACK_NAME)["Stacks"][0]
    outputs = {o["OutputKey"]: o["OutputValue"] for o in stack["Outputs"]}
except Exception:
    print(f"❌ Stack '{STACK_NAME}' not found. Deploy infra.yaml first.")
    sys.exit(1)

POLICIES_TABLE = dynamodb.Table(outputs["QuotaPoliciesTableName"])
ALERT_TOPIC = outputs["AlertTopicArn"]

# ── Read tracking config ──
config_path = os.path.join(SCRIPT_DIR, "server_side_tracking_config.json")
try:
    with open(config_path) as f:
        config = json.load(f)
except FileNotFoundError:
    print(f"❌ Config not found. Run setup_server_side_tracking.py first.")
    sys.exit(1)

print("=" * 80)
print("🔒 Seeding Quota Policies & Creating Alarms")
print("=" * 80)

# ═══════════════════════════════════════════════════════════════════════════════
# QUOTA POLICIES
# ═══════════════════════════════════════════════════════════════════════════════

POLICIES = [
    # Default — applies to everyone without a specific policy
    {
        "policyId": "default",
        "policyType": "default",
        "monthlyLimit": 225_000_000,
        "dailyLimit": 8_000_000,
        "enforcementMode": "alert",
        "enabled": True,
        "description": "Organization-wide default",
    },
    # Group policies
    {
        "policyId": "group#engineering",
        "policyType": "group",
        "monthlyLimit": 500_000_000,
        "dailyLimit": 20_000_000,
        "enforcementMode": "block",
        "enabled": True,
        "description": "Engineering team",
    },
    {
        "policyId": "group#data-science",
        "policyType": "group",
        "monthlyLimit": 750_000_000,
        "dailyLimit": 30_000_000,
        "enforcementMode": "alert",
        "enabled": True,
        "description": "Data science team — higher limit for training workloads",
    },
    {
        "policyId": "group#sales",
        "policyType": "group",
        "monthlyLimit": 300_000_000,
        "dailyLimit": 12_000_000,
        "enforcementMode": "block",
        "enabled": True,
        "description": "Sales team",
    },
    # User overrides
    {
        "policyId": "user#john.doe",
        "policyType": "user",
        "monthlyLimit": 500_000_000,
        "dailyLimit": 25_000_000,
        "enforcementMode": "block",
        "enabled": True,
        "description": "Power user override — platform lead",
    },
]

print("\n📋 Seeding quota policies...")
for policy in POLICIES:
    POLICIES_TABLE.put_item(Item=policy)
    mode_icon = "🔴" if policy["enforcementMode"] == "block" else "🟡"
    monthly_m = policy["monthlyLimit"] / 1_000_000
    print(f"   {mode_icon} {policy['policyId']:<30} {monthly_m:>6.0f}M tokens/month  ({policy['enforcementMode']})")

# ═══════════════════════════════════════════════════════════════════════════════
# CLOUDWATCH ALARMS
# ═══════════════════════════════════════════════════════════════════════════════

print("\n🔔 Creating per-user CloudWatch Alarms...")

THRESHOLDS = [
    {"pct": 80, "suffix": "warning", "action": "warning"},
    {"pct": 95, "suffix": "critical", "action": "critical"},
]

alarms_created = 0

for user_id, user_cfg in config["users"].items():
    profile_arn = user_cfg.get("profile_arn", "")
    if not profile_arn:
        continue
    profile_id = profile_arn.split("/")[-1]

    # Resolve user's effective monthly limit
    user_policy = next((p for p in POLICIES if p["policyId"] == f"user#{user_id}"), None)
    group_policy = next((p for p in POLICIES if p["policyId"] == f"group#{user_cfg['group']}"), None)
    default_policy = next((p for p in POLICIES if p["policyId"] == "default"), None)
    effective = user_policy or group_policy or default_policy
    monthly_limit = effective["monthlyLimit"]

    for threshold in THRESHOLDS:
        token_threshold = int(monthly_limit * threshold["pct"] / 100)
        alarm_name = f"bedrock-quota-{user_id}-InputTokenCount-{threshold['suffix']}"

        cloudwatch.put_metric_alarm(
            AlarmName=alarm_name,
            AlarmDescription=f"{user_id} Bedrock usage at {threshold['pct']}% of {monthly_limit:,} monthly limit",
            Namespace="AWS/Bedrock",
            MetricName="InputTokenCount",
            Dimensions=[{"Name": "InferenceProfileId", "Value": profile_id}],
            Statistic="Sum",
            Period=86400,  # daily evaluation
            EvaluationPeriods=1,
            Threshold=token_threshold,
            ComparisonOperator="GreaterThanThreshold",
            TreatMissingData="notBreaching",
            AlarmActions=[ALERT_TOPIC],
            OKActions=[ALERT_TOPIC],
            Tags=[
                {"Key": "userId", "Value": user_id},
                {"Key": "group", "Value": user_cfg["group"]},
                {"Key": "threshold", "Value": str(threshold["pct"])},
            ],
        )
        alarms_created += 1
        icon = "🟡" if threshold["pct"] == 80 else "🔴"
        print(f"   {icon} {alarm_name}")
        print(f"      threshold: {token_threshold:>12,} tokens ({threshold['pct']}% of {monthly_limit:,})")

print(f"\n✅ Created {alarms_created} alarms across {len(config['users'])} users")
print(f"   Alarm → SNS ({ALERT_TOPIC.split(':')[-1]}) → Lambda enforcement")
print("=" * 80)
