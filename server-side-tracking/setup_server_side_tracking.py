"""
Setup Server-Side Usage Tracking Infrastructure

Implements the thesis recommendations:
1. Reads infrastructure outputs from CloudFormation stack (infra.yaml)
2. Enables Bedrock model invocation logging (metadata-only to control costs)
3. Creates per-USER Application Inference Profiles (not just per-tenant)
4. Tags encode user + group + tenant for server-side attribution

Prerequisites:
  aws cloudformation deploy \
    --template-file infra.yaml \
    --stack-name bedrock-server-side-tracking \
    --capabilities CAPABILITY_NAMED_IAM

Uses Claude Opus 4.6 as the base model.
"""

import boto3
import json
import os
import sys

# Ensure repo root is on path for lab_helpers import
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from lab_helpers.config import Region, ModelId

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
STACK_NAME = "bedrock-server-side-tracking"

bedrock = boto3.client('bedrock', region_name=Region)
s3 = boto3.client('s3', region_name=Region)
sts = boto3.client('sts', region_name=Region)
cfn = boto3.client('cloudformation', region_name=Region)

account_id = sts.get_caller_identity()['Account']

# --- User/Group definitions (simulating CCWB identity layer) ---
USERS = {
    "john.doe": {"group": "engineering", "tenant": "tenant_a", "department": "platform"},
    "jane.smith": {"group": "data-science", "tenant": "tenant_a", "department": "ml-ops"},
    "bob.wilson": {"group": "sales", "tenant": "tenant_b", "department": "sales-ops"},
}

print("=" * 80)
print("🔧 Setting Up Server-Side Usage Tracking")
print(f"   Model: Claude Opus 4.6 ({ModelId.CLAUDE_OPUS_4_6})")
print(f"   Region: {Region}")
print(f"   Account: {account_id}")
print("=" * 80)

# ── Step 1: Read CloudFormation outputs ──
print("\n📦 Step 1: Reading infrastructure from CloudFormation stack...")
try:
    stack = cfn.describe_stacks(StackName=STACK_NAME)["Stacks"][0]
    outputs = {o["OutputKey"]: o["OutputValue"] for o in stack["Outputs"]}
    BUCKET_NAME = outputs["BucketName"]
    LOG_GROUP = outputs["LogGroupName"]
    LOGGING_ROLE_ARN = outputs["LoggingRoleArn"]
    print(f"   ✅ S3 Bucket:       {BUCKET_NAME}")
    print(f"   ✅ Log Group:       {LOG_GROUP}")
    print(f"   ✅ Logging Role:    {LOGGING_ROLE_ARN}")
except cfn.exceptions.ClientError:
    print(f"   ❌ Stack '{STACK_NAME}' not found. Deploy it first:")
    print(f"      aws cloudformation deploy \\")
    print(f"        --template-file {os.path.join(SCRIPT_DIR, 'infra.yaml')} \\")
    print(f"        --stack-name {STACK_NAME} \\")
    print(f"        --capabilities CAPABILITY_NAMED_IAM")
    sys.exit(1)

# ── Step 2: Enable Bedrock model invocation logging ──
print("\n📝 Step 2: Enabling Bedrock model invocation logging...")
try:
    bedrock.put_model_invocation_logging_configuration(
        loggingConfig={
            "s3Config": {
                "bucketName": BUCKET_NAME,
                "keyPrefix": "invocation-logs/"
            },
            "cloudWatchConfig": {
                "logGroupName": LOG_GROUP,
                "roleArn": LOGGING_ROLE_ARN,
                "largeDataDeliveryS3Config": {
                    "bucketName": BUCKET_NAME,
                    "keyPrefix": "invocation-logs-large/"
                }
            },
            "textDataDeliveryEnabled": False,  # metadata-only to control costs
            "imageDataDeliveryEnabled": False,
            "embeddingDataDeliveryEnabled": False,
        }
    )
    print("   ✅ Invocation logging enabled (metadata-only mode)")
    print(f"   📁 S3 → s3://{BUCKET_NAME}/invocation-logs/")
    print(f"   📁 CloudWatch → {LOG_GROUP}")
    print("   ℹ️  Captures: requestId, identity, modelId, token counts")
    print("   ℹ️  Excludes: request/response bodies (cost optimization)")
except Exception as e:
    print(f"   ❌ Error: {e}")

# ── Step 3: Get system inference profile ARN for Opus 4.6 ──
print("\n🔍 Step 3: Locating Opus 4.6 system inference profile...")
system_profile_arn = None
try:
    response = bedrock.list_inference_profiles()
    # Look for opus 4.6 system profile, fall back to foundation model ARN
    for profile in response.get("inferenceProfileSummaries", []):
        pid = profile["inferenceProfileId"]
        if "opus-4-6" in pid or "opus_4_6" in pid:
            system_profile_arn = profile["inferenceProfileArn"]
            print(f"   ✅ Found system profile: {pid}")
            break

    if not system_profile_arn:
        # Fall back to foundation model ARN
        system_profile_arn = f"arn:aws:bedrock:{Region}::foundation-model/{ModelId.CLAUDE_OPUS_4_6}"
        print(f"   ⚠️  No system profile found, using foundation model ARN")
        print(f"   {system_profile_arn}")
except Exception as e:
    system_profile_arn = f"arn:aws:bedrock:{Region}::foundation-model/{ModelId.CLAUDE_OPUS_4_6}"
    print(f"   ⚠️  Fallback to foundation model ARN: {e}")

# ── Step 4: Create per-USER Application Inference Profiles ──
print("\n👤 Step 4: Creating per-user Application Inference Profiles...")
print("   (This is the key difference from per-tenant — each user gets their own AIP)")

created_profiles = {}

for user_id, attrs in USERS.items():
    profile_name = f"aip-user-{user_id.replace('.', '-')}"
    tags = [
        {"key": "userId", "value": user_id},
        {"key": "group", "value": attrs["group"]},
        {"key": "tenant", "value": attrs["tenant"]},
        {"key": "department", "value": attrs["department"]},
        {"key": "trackingLevel", "value": "user"},
    ]

    print(f"\n   Creating profile for {user_id}...")
    try:
        resp = bedrock.create_inference_profile(
            inferenceProfileName=profile_name,
            modelSource={"copyFrom": system_profile_arn},
            tags=tags,
        )
        created_profiles[user_id] = {
            "arn": resp["inferenceProfileArn"],
            "status": resp["status"],
            "tags": {t["key"]: t["value"] for t in tags},
        }
        print(f"   ✅ {profile_name} → {resp['inferenceProfileArn']}")
    except Exception as e:
        if "already exists" in str(e).lower() or "Conflict" in str(e):
            try:
                existing = bedrock.get_inference_profile(inferenceProfileIdentifier=profile_name)
                created_profiles[user_id] = {
                    "arn": existing["inferenceProfileArn"],
                    "status": existing["status"],
                    "tags": {t["key"]: t["value"] for t in tags},
                }
                print(f"   ⚠️  Already exists, reusing: {existing['inferenceProfileArn']}")
            except Exception as fe:
                print(f"   ❌ {fe}")
        else:
            print(f"   ❌ {e}")

# ── Save configuration ──
config = {
    "model": ModelId.CLAUDE_OPUS_4_6,
    "region": Region,
    "account_id": account_id,
    "log_bucket": BUCKET_NAME,
    "log_prefix": "invocation-logs/",
    "log_group": LOG_GROUP,
    "logging_role_arn": LOGGING_ROLE_ARN,
    "users": {
        uid: {**attrs, "profile_arn": created_profiles.get(uid, {}).get("arn", "")}
        for uid, attrs in USERS.items()
    },
}

config_path = os.path.join(SCRIPT_DIR, "server_side_tracking_config.json")
with open(config_path, 'w') as f:
    json.dump(config, f, indent=2)

print("\n" + "=" * 80)
print("✅ Setup Complete")
print("=" * 80)
print(f"\n   Config saved:   {config_path}")
print(f"   Log bucket:     s3://{BUCKET_NAME}/invocation-logs/")
print(f"   Log group:      {LOG_GROUP}")
print(f"   User profiles:  {len(created_profiles)} created")
print(f"\n💡 Next: Run  python server-side-tracking/server_side_tracking_demo.py")
print("=" * 80)
