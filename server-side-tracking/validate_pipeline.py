"""
Validate Server-Side Tracking Pipeline

End-to-end validation that checks all three data paths:
1. CloudWatch Metrics — per-user AIP metrics (Invocations, InputTokenCount, OutputTokenCount)
2. CloudWatch Logs — invocation logs with identity.arn and requestMetadata
3. S3 — raw invocation log files landing in the bucket

Run after server_side_tracking_demo.py has made at least one round of calls.
"""

import boto3
import json
import os
import sys
import time
import datetime
from datetime import timedelta

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from lab_helpers.config import Region

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

config_path = os.path.join(SCRIPT_DIR, "server_side_tracking_config.json")
try:
    with open(config_path) as f:
        config = json.load(f)
except FileNotFoundError:
    print(f"❌ Config not found at {config_path}")
    print("   Run setup_server_side_tracking.py first, then server_side_tracking_demo.py")
    sys.exit(1)

cloudwatch = boto3.client("cloudwatch", region_name=Region)
logs_client = boto3.client("logs", region_name=Region)
s3 = boto3.client("s3", region_name=Region)

BUCKET = config["log_bucket"]
LOG_GROUP = config.get("log_group", "/aws/bedrock/server-side-tracking")
METRICS = ["Invocations", "InputTokenCount", "OutputTokenCount"]

end_time = datetime.datetime.now(datetime.timezone.utc)
start_time = end_time - timedelta(hours=2)

passed = 0
failed = 0
warnings = 0

print("=" * 80)
print("🔍 Validating Server-Side Tracking Pipeline")
print(f"   Time window: last 2 hours")
print(f"   Users: {', '.join(config['users'].keys())}")
print("=" * 80)


# ═══════════════════════════════════════════════════════════════════════════════
# CHECK 1: CloudWatch Metrics per User AIP
# ═══════════════════════════════════════════════════════════════════════════════
print("\n\n━━━ CHECK 1: CloudWatch Metrics (per-user AIP) ━━━")
print("   Verifying each user's AIP has Invocations, InputTokenCount, OutputTokenCount\n")

user_metrics = {}

for user_id, user_cfg in config["users"].items():
    profile_arn = user_cfg.get("profile_arn", "")
    if not profile_arn:
        print(f"   ❌ {user_id}: no profile_arn in config")
        failed += 1
        continue

    profile_id = profile_arn.split("/")[-1]
    user_metrics[user_id] = {}

    for metric_name in METRICS:
        resp = cloudwatch.get_metric_statistics(
            Namespace="AWS/Bedrock",
            MetricName=metric_name,
            Dimensions=[{"Name": "InferenceProfileId", "Value": profile_id}],
            StartTime=start_time,
            EndTime=end_time,
            Period=300,
            Statistics=["Sum"],
        )
        total = sum(dp["Sum"] for dp in resp["Datapoints"])
        user_metrics[user_id][metric_name] = total

    inv = user_metrics[user_id]["Invocations"]
    inp = user_metrics[user_id]["InputTokenCount"]
    out = user_metrics[user_id]["OutputTokenCount"]

    if inv > 0 and inp > 0 and out > 0:
        print(f"   ✅ {user_id:<20} invocations={int(inv):>4}  input_tokens={int(inp):>6}  output_tokens={int(out):>6}")
        passed += 1
    elif inv > 0:
        print(f"   ⚠️  {user_id:<20} invocations={int(inv):>4}  input_tokens={int(inp):>6}  output_tokens={int(out):>6}  (partial data)")
        warnings += 1
    else:
        print(f"   ❌ {user_id:<20} no metrics yet (wait 3-5 min after demo calls)")
        failed += 1


# ═══════════════════════════════════════════════════════════════════════════════
# CHECK 2: CloudWatch Logs — identity.arn attribution
# ═══════════════════════════════════════════════════════════════════════════════
print("\n\n━━━ CHECK 2: CloudWatch Logs (identity.arn + requestMetadata) ━━━")
print(f"   Log group: {LOG_GROUP}\n")

identity_query = """
fields @timestamp, identity.arn, modelId, inputTokenCount, outputTokenCount
| stats sum(inputTokenCount) as totalInput,
        sum(outputTokenCount) as totalOutput,
        count(*) as invocations
  by identity.arn
| sort totalInput desc
"""

metadata_query = """
fields @timestamp, requestMetadata.userId, requestMetadata.groupId,
       requestMetadata.tenantId, inputTokenCount, outputTokenCount
| stats sum(inputTokenCount) as totalInput,
        sum(outputTokenCount) as totalOutput,
        count(*) as invocations
  by requestMetadata.userId, requestMetadata.groupId
| sort totalInput desc
"""

for label, query in [("identity.arn", identity_query), ("requestMetadata", metadata_query)]:
    print(f"   ── {label} query ──")
    try:
        start_resp = logs_client.start_query(
            logGroupName=LOG_GROUP,
            startTime=int(start_time.timestamp()),
            endTime=int(end_time.timestamp()),
            queryString=query,
        )
        query_id = start_resp["queryId"]

        for _ in range(15):
            time.sleep(3)
            result = logs_client.get_query_results(queryId=query_id)
            if result["status"] in ("Complete", "Failed", "Cancelled"):
                break

        if result["status"] == "Complete" and result["results"]:
            for row in result["results"]:
                fields = {f["field"]: f["value"] for f in row}
                parts = "  ".join(f"{k}={v}" for k, v in fields.items() if k != "@ptr")
                print(f"      ✅ {parts}")
            passed += 1
        elif result["status"] == "Complete":
            print(f"      ⚠️  Query returned 0 results (logs may take a few minutes)")
            warnings += 1
        else:
            print(f"      ❌ Query status: {result['status']}")
            failed += 1

    except logs_client.exceptions.ResourceNotFoundException:
        print(f"      ❌ Log group {LOG_GROUP} not found")
        print(f"         Invocation logs may take a few minutes to create the log group")
        failed += 1
    except Exception as e:
        print(f"      ❌ {e}")
        failed += 1


# ═══════════════════════════════════════════════════════════════════════════════
# CHECK 3: S3 — raw invocation log files
# ═══════════════════════════════════════════════════════════════════════════════
print("\n\n━━━ CHECK 3: S3 Invocation Logs ━━━")
print(f"   Bucket: s3://{BUCKET}/invocation-logs/\n")

try:
    resp = s3.list_objects_v2(
        Bucket=BUCKET,
        Prefix="invocation-logs/",
        MaxKeys=10,
    )
    objects = resp.get("Contents", [])
    if objects:
        print(f"   ✅ Found {resp.get('KeyCount', len(objects))} log files")
        for obj in objects[:5]:
            size_kb = obj["Size"] / 1024
            print(f"      {obj['Key']:<70} {size_kb:.1f} KB  {obj['LastModified']}")
        if len(objects) > 5:
            print(f"      ... and {len(objects) - 5} more")

        # Sample one file to verify structure
        sample_key = objects[0]["Key"]
        sample_obj = s3.get_object(Bucket=BUCKET, Key=sample_key)
        sample_body = sample_obj["Body"].read().decode("utf-8")

        # Invocation logs can be JSONL (one JSON per line)
        first_line = sample_body.strip().split("\n")[0]
        try:
            log_entry = json.loads(first_line)
            has_identity = "identity" in log_entry
            has_metadata = "requestMetadata" in log_entry
            has_tokens = "inputTokenCount" in log_entry or "input" in log_entry

            print(f"\n   Sample log entry fields: {list(log_entry.keys())}")
            if has_identity:
                print(f"   ✅ identity field present: {log_entry.get('identity', {})}")
            else:
                print(f"   ⚠️  identity field not found in log entry")
            if has_metadata:
                print(f"   ✅ requestMetadata present: {log_entry.get('requestMetadata', {})}")
            else:
                print(f"   ⚠️  requestMetadata not found (may use different field name)")
            passed += 1
        except json.JSONDecodeError:
            print(f"   ⚠️  Could not parse log entry as JSON")
            warnings += 1
    else:
        print(f"   ❌ No log files found yet")
        print(f"      Invocation logs can take 5-10 minutes to appear in S3")
        failed += 1

except Exception as e:
    print(f"   ❌ {e}")
    failed += 1


# ═══════════════════════════════════════════════════════════════════════════════
# SUMMARY
# ═══════════════════════════════════════════════════════════════════════════════
print("\n\n" + "=" * 80)
total = passed + failed + warnings
print(f"📋 Validation Summary: {passed} passed / {warnings} warnings / {failed} failed")
print("=" * 80)

if failed == 0 and warnings == 0:
    print("\n   🎉 All checks passed — pipeline is fully operational")
elif failed == 0:
    print("\n   ⚠️  Pipeline is working but some data hasn't propagated yet")
    print("   Re-run in 5 minutes for full validation")
else:
    print("\n   ❌ Some checks failed. Common causes:")
    print("   1. Run server_side_tracking_demo.py first to generate data")
    print("   2. Wait 3-5 min for CloudWatch metrics, 5-10 min for S3 logs")
    print("   3. Verify CloudFormation stack deployed successfully")

print("\n   Next: Run  python server-side-tracking/deploy_dashboard.py  to create the dashboard")
print("=" * 80)
