"""
Bedrock Quota Enforcement Lambda

Triggered by CloudWatch Alarm → SNS → this Lambda.

Flow:
1. Parse alarm to identify which user/AIP breached
2. Look up user's quota policy in DynamoDB (user → group → default precedence)
3. Record breach in UserQuotaMetrics table
4. Take enforcement action based on policy mode (alert or block)
5. Publish notification to QuotaBreachTopic with user details

DynamoDB QuotaPolicies schema:
  policyId (PK): "user#john.doe" | "group#engineering" | "default"
  policyType: "user" | "group" | "default"
  monthlyLimit: 500000000
  dailyLimit: 20000000
  enforcementMode: "alert" | "block"
  enabled: true

DynamoDB UserQuotaMetrics schema:
  userId (PK): "john.doe"
  periodKey (SK): "monthly#2026-03" | "daily#2026-03-05"
  inputTokens: 12345678
  outputTokens: 9876543
  totalTokens: 22222221
  blocked: false
  ttl: 1234567890
"""

import json
import os
import re
import time
import datetime
import boto3
from boto3.dynamodb.conditions import Key

dynamodb = boto3.resource("dynamodb")
sns = boto3.client("sns")
cloudwatch = boto3.client("cloudwatch")
bedrock = boto3.client("bedrock")

POLICIES_TABLE = dynamodb.Table(os.environ["QUOTA_POLICIES_TABLE"])
METRICS_TABLE = dynamodb.Table(os.environ["USER_METRICS_TABLE"])
BREACH_TOPIC = os.environ["QUOTA_BREACH_TOPIC"]
ALERT_TOPIC = os.environ["ALERT_TOPIC"]
DEFAULT_LIMIT = int(os.environ.get("DEFAULT_MONTHLY_LIMIT", "500000000"))
REGION = os.environ.get("REGION", "us-west-2")


def lambda_handler(event, context):
    """Entry point — handles SNS messages from CloudWatch Alarms."""
    for record in event.get("Records", []):
        try:
            message = json.loads(record["Sns"]["Message"])
            process_alarm(message)
        except Exception as e:
            print(f"Error processing record: {e}")
            raise


def process_alarm(alarm_message):
    """Process a CloudWatch Alarm state change."""
    alarm_name = alarm_message.get("AlarmName", "")
    new_state = alarm_message.get("NewStateValue", "")
    reason = alarm_message.get("NewStateReason", "")

    print(f"Alarm: {alarm_name}, State: {new_state}, Reason: {reason}")

    if new_state != "ALARM":
        print(f"Ignoring non-ALARM state: {new_state}")
        return

    # Extract user ID and profile ID from alarm name
    # Convention: bedrock-quota-{userId}-{metric}-{threshold}
    user_id, profile_id = extract_user_from_alarm(alarm_name, alarm_message)
    if not user_id:
        print(f"Could not extract user from alarm: {alarm_name}")
        return

    # Get current usage from CloudWatch
    usage = get_current_usage(profile_id)

    # Resolve effective quota policy (user → group → default)
    policy = resolve_policy(user_id)

    # Record usage in DynamoDB
    record_usage(user_id, usage)

    # Evaluate and enforce
    enforce(user_id, usage, policy, alarm_name)


def extract_user_from_alarm(alarm_name, alarm_message):
    """Extract userId and profileId from alarm metadata."""
    # Try alarm name convention: bedrock-quota-{userId}-{metric}
    match = re.match(r"bedrock-quota-(.+?)-(InputToken|OutputToken|Invocations)", alarm_name)
    if match:
        user_id = match.group(1)
        # Get profile ID from alarm dimensions
        dimensions = alarm_message.get("Trigger", {}).get("Dimensions", [])
        profile_id = None
        for dim in dimensions:
            if dim.get("name") == "InferenceProfileId":
                profile_id = dim.get("value")
                break
        return user_id, profile_id

    # Fallback: look up profile ID from alarm dimensions and resolve via tags
    dimensions = alarm_message.get("Trigger", {}).get("Dimensions", [])
    for dim in dimensions:
        if dim.get("name") == "InferenceProfileId":
            profile_id = dim["value"]
            user_id = resolve_user_from_profile(profile_id)
            return user_id, profile_id

    return None, None


def resolve_user_from_profile(profile_id):
    """Look up userId tag from an Application Inference Profile."""
    try:
        profile_arn = f"arn:aws:bedrock:{REGION}:{get_account_id()}:inference-profile/{profile_id}"
        tags = bedrock.list_tags_for_resource(resourceARN=profile_arn)
        for tag in tags.get("tags", []):
            if tag["key"] == "userId":
                return tag["value"]
    except Exception as e:
        print(f"Could not resolve user from profile {profile_id}: {e}")
    return None


def get_account_id():
    """Get current account ID from context."""
    return boto3.client("sts").get_caller_identity()["Account"]


def get_current_usage(profile_id):
    """Fetch current month's token usage from CloudWatch metrics."""
    if not profile_id:
        return {"inputTokens": 0, "outputTokens": 0, "totalTokens": 0, "invocations": 0}

    now = datetime.datetime.now(datetime.timezone.utc)
    start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    usage = {}
    for metric_name in ["InputTokenCount", "OutputTokenCount", "Invocations"]:
        resp = cloudwatch.get_metric_statistics(
            Namespace="AWS/Bedrock",
            MetricName=metric_name,
            Dimensions=[{"Name": "InferenceProfileId", "Value": profile_id}],
            StartTime=start_of_month,
            EndTime=now,
            Period=2592000,  # 30 days
            Statistics=["Sum"],
        )
        total = sum(dp["Sum"] for dp in resp.get("Datapoints", []))
        usage[metric_name] = int(total)

    return {
        "inputTokens": usage.get("InputTokenCount", 0),
        "outputTokens": usage.get("OutputTokenCount", 0),
        "totalTokens": usage.get("InputTokenCount", 0) + usage.get("OutputTokenCount", 0),
        "invocations": usage.get("Invocations", 0),
    }


def resolve_policy(user_id):
    """Resolve effective quota policy: user → group → default precedence."""
    # 1. Check user-specific policy
    user_policy = get_policy(f"user#{user_id}")
    if user_policy and user_policy.get("enabled", True):
        print(f"Using user policy for {user_id}")
        return user_policy

    # 2. Check group policies (user may belong to multiple groups)
    # Group membership would come from IdP claims stored in DynamoDB
    # For now, check if there's a group tag on the user's profile
    group_policies = POLICIES_TABLE.query(
        IndexName="byType",
        KeyConditionExpression=Key("policyType").eq("group"),
    )
    for gp in group_policies.get("Items", []):
        if gp.get("enabled", True):
            print(f"Using group policy: {gp['policyId']}")
            return gp

    # 3. Fall back to default
    default_policy = get_policy("default")
    if default_policy:
        print("Using default policy")
        return default_policy

    # 4. Hardcoded fallback
    print("Using hardcoded default limit")
    return {
        "policyId": "hardcoded-default",
        "monthlyLimit": DEFAULT_LIMIT,
        "dailyLimit": DEFAULT_LIMIT // 30,
        "enforcementMode": "alert",
        "enabled": True,
    }


def get_policy(policy_id):
    """Get a specific policy from DynamoDB."""
    try:
        resp = POLICIES_TABLE.get_item(Key={"policyId": policy_id})
        return resp.get("Item")
    except Exception as e:
        print(f"Error fetching policy {policy_id}: {e}")
        return None


def record_usage(user_id, usage):
    """Record current usage snapshot in UserQuotaMetrics."""
    now = datetime.datetime.now(datetime.timezone.utc)
    month_key = f"monthly#{now.strftime('%Y-%m')}"
    day_key = f"daily#{now.strftime('%Y-%m-%d')}"

    # TTL: 90 days from now
    ttl = int(time.time()) + (90 * 86400)

    for period_key in [month_key, day_key]:
        try:
            METRICS_TABLE.put_item(Item={
                "userId": user_id,
                "periodKey": period_key,
                "inputTokens": usage["inputTokens"],
                "outputTokens": usage["outputTokens"],
                "totalTokens": usage["totalTokens"],
                "invocations": usage["invocations"],
                "updatedAt": now.isoformat(),
                "ttl": ttl,
            })
        except Exception as e:
            print(f"Error recording usage for {user_id}/{period_key}: {e}")


def enforce(user_id, usage, policy, alarm_name):
    """Evaluate quota and take enforcement action."""
    monthly_limit = int(policy.get("monthlyLimit", DEFAULT_LIMIT))
    mode = policy.get("enforcementMode", "alert")
    total_tokens = usage["totalTokens"]
    pct = (total_tokens / monthly_limit * 100) if monthly_limit > 0 else 0

    print(f"User: {user_id}, Usage: {total_tokens:,} / {monthly_limit:,} ({pct:.1f}%), Mode: {mode}")

    # Determine severity
    if pct >= 100:
        severity = "CRITICAL"
        action = "BLOCKED" if mode == "block" else "WARNING"
    elif pct >= 95:
        severity = "HIGH"
        action = "WARNING"
    elif pct >= 80:
        severity = "MEDIUM"
        action = "INFO"
    else:
        severity = "LOW"
        action = "INFO"

    # Block user if in block mode and over limit
    if mode == "block" and pct >= 100:
        block_user(user_id)

    # Publish notification
    notification = {
        "userId": user_id,
        "severity": severity,
        "action": action,
        "enforcementMode": mode,
        "currentUsage": total_tokens,
        "monthlyLimit": monthly_limit,
        "utilizationPct": round(pct, 1),
        "inputTokens": usage["inputTokens"],
        "outputTokens": usage["outputTokens"],
        "invocations": usage["invocations"],
        "alarmName": alarm_name,
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    }

    topic = BREACH_TOPIC if severity in ("CRITICAL", "HIGH") else ALERT_TOPIC
    sns.publish(
        TopicArn=topic,
        Subject=f"[{severity}] Bedrock Quota {action}: {user_id} at {pct:.0f}%",
        Message=json.dumps(notification, indent=2),
    )
    print(f"Published {severity} notification for {user_id}")


def block_user(user_id):
    """Mark user as blocked in DynamoDB. Gateway checks this flag before forwarding requests."""
    now = datetime.datetime.now(datetime.timezone.utc)
    month_key = f"monthly#{now.strftime('%Y-%m')}"

    try:
        METRICS_TABLE.update_item(
            Key={"userId": user_id, "periodKey": month_key},
            UpdateExpression="SET blocked = :b, blockedAt = :t",
            ExpressionAttributeValues={":b": True, ":t": now.isoformat()},
        )
        print(f"BLOCKED user {user_id} — gateway should deny further requests")
    except Exception as e:
        print(f"Error blocking user {user_id}: {e}")
