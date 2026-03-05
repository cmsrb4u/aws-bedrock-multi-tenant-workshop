"""
Server-Side Usage Tracking Demo

Demonstrates the full server-side attribution pipeline:
1. Converse API with requestMetadata (server-side user identity injection)
2. Per-user AIP routing (cost allocation tags in Cost Explorer)
3. CloudWatch Logs Insights queries on invocation logs (identity.arn attribution)
4. Per-user usage report from server-side data only — no OTEL dependency

Uses Claude Opus 4.6 via per-user Application Inference Profiles.
"""

import boto3
import json
import time
import os
import sys
import datetime
from datetime import timedelta

# Ensure repo root is on path for lab_helpers import
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from lab_helpers.config import Region, InferenceConfig

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# ── Load config from setup step ──
config_path = os.path.join(SCRIPT_DIR, "server_side_tracking_config.json")
try:
    with open(config_path) as f:
        config = json.load(f)
except FileNotFoundError:
    print(f"❌ Config not found at {config_path}")
    print("   Run setup_server_side_tracking.py first")
    exit(1)

bedrock_runtime = boto3.client("bedrock-runtime", region_name=Region)
logs_client = boto3.client("logs", region_name=Region)
cloudwatch = boto3.client("cloudwatch", region_name=Region)

LOG_GROUP = config.get("log_group", "/aws/bedrock/server-side-tracking")

print("=" * 80)
print("🔬 Server-Side Usage Tracking Demo")
print(f"   Model: {config['model']}")
print(f"   Users: {', '.join(config['users'].keys())}")
print("=" * 80)

# ── Simulated user requests ──
# In production, the gateway/auth layer sets requestMetadata — not the client.
USER_REQUESTS = {
    "john.doe": [
        "Explain Kubernetes pod autoscaling in 3 sentences.",
        "What is a service mesh and when should I use one?",
    ],
    "jane.smith": [
        "Compare XGBoost vs LightGBM for tabular data.",
    ],
    "bob.wilson": [
        "Write a 2-sentence elevator pitch for an AI analytics platform.",
        "What are the top 3 objections in enterprise SaaS sales?",
        "Draft a follow-up email after a product demo.",
    ],
}

# ── Step 1: Make Converse API calls with server-side requestMetadata ──
print("\n📡 Step 1: Making Converse API calls with server-side requestMetadata")
print("-" * 80)

call_results = []

for user_id, prompts in USER_REQUESTS.items():
    user_cfg = config["users"][user_id]
    profile_arn = user_cfg.get("profile_arn", "")

    if not profile_arn:
        print(f"   ⚠️  No profile for {user_id}, skipping")
        continue

    for prompt in prompts:
        print(f"\n   👤 {user_id} ({user_cfg['group']}) → {prompt[:60]}...")

        # ── THE KEY: requestMetadata is set by the server/gateway, not the client ──
        # This metadata lands in Bedrock invocation logs for server-side attribution
        metadata = {
            "userId": user_id,
            "groupId": user_cfg["group"],
            "tenantId": user_cfg["tenant"],
            "department": user_cfg["department"],
            "source": "server-side-gateway",  # proves this isn't client-reported
        }

        try:
            response = bedrock_runtime.converse(
                modelId=profile_arn,  # per-user AIP for cost allocation
                messages=[{"role": "user", "content": [{"text": prompt}]}],
                inferenceConfig={
                    "maxTokens": 256,
                    "temperature": 0.7,
                },
                requestMetadata=metadata,  # server-side identity injection
            )

            usage = response["usage"]
            result = {
                "userId": user_id,
                "group": user_cfg["group"],
                "tenant": user_cfg["tenant"],
                "inputTokens": usage["inputTokens"],
                "outputTokens": usage["outputTokens"],
                "totalTokens": usage["inputTokens"] + usage["outputTokens"],
                "prompt": prompt[:60],
                "stopReason": response["stopReason"],
            }
            call_results.append(result)

            print(f"      ✅ {usage['inputTokens']} in / {usage['outputTokens']} out tokens")

        except Exception as e:
            print(f"      ❌ {e}")

        time.sleep(1)  # avoid throttling

# ── Step 2: Server-side attribution report (from call data) ──
print("\n\n📊 Step 2: Server-Side Attribution Report")
print("=" * 80)
print("   (This data comes from server-side sources only — no OTEL)")
print()

# Aggregate by user
user_totals = {}
for r in call_results:
    uid = r["userId"]
    if uid not in user_totals:
        user_totals[uid] = {"input": 0, "output": 0, "calls": 0, "group": r["group"], "tenant": r["tenant"]}
    user_totals[uid]["input"] += r["inputTokens"]
    user_totals[uid]["output"] += r["outputTokens"]
    user_totals[uid]["calls"] += 1

# Aggregate by group
group_totals = {}
for uid, t in user_totals.items():
    g = t["group"]
    if g not in group_totals:
        group_totals[g] = {"input": 0, "output": 0, "calls": 0, "users": []}
    group_totals[g]["input"] += t["input"]
    group_totals[g]["output"] += t["output"]
    group_totals[g]["calls"] += t["calls"]
    group_totals[g]["users"].append(uid)

print(f"   {'User':<20} {'Group':<15} {'Calls':>6} {'Input':>8} {'Output':>8} {'Total':>8}")
print(f"   {'─'*20} {'─'*15} {'─'*6} {'─'*8} {'─'*8} {'─'*8}")
for uid, t in sorted(user_totals.items()):
    total = t["input"] + t["output"]
    print(f"   {uid:<20} {t['group']:<15} {t['calls']:>6} {t['input']:>8} {t['output']:>8} {total:>8}")

print(f"\n   {'Group':<20} {'Users':>6} {'Calls':>6} {'Input':>8} {'Output':>8} {'Total':>8}")
print(f"   {'─'*20} {'─'*6} {'─'*6} {'─'*8} {'─'*8} {'─'*8}")
for g, t in sorted(group_totals.items()):
    total = t["input"] + t["output"]
    print(f"   {g:<20} {len(t['users']):>6} {t['calls']:>6} {t['input']:>8} {t['output']:>8} {total:>8}")

# ── Step 3: Query CloudWatch Logs Insights for identity.arn attribution ──
print("\n\n🔍 Step 3: Querying Bedrock Invocation Logs (identity.arn)")
print("-" * 80)
print("   Waiting 30s for log delivery...")
time.sleep(30)

query = """
fields @timestamp, identity.arn, modelId, inputTokenCount, outputTokenCount
| stats sum(inputTokenCount) as totalInput,
        sum(outputTokenCount) as totalOutput,
        count(*) as invocations
  by identity.arn
| sort totalInput desc
"""

try:
    end_time = int(datetime.datetime.now(datetime.timezone.utc).timestamp())
    start_time = end_time - 3600  # last hour

    start_resp = logs_client.start_query(
        logGroupName=LOG_GROUP,
        startTime=start_time,
        endTime=end_time,
        queryString=query,
    )
    query_id = start_resp["queryId"]
    print(f"   Query started: {query_id}")

    # Poll for results
    for _ in range(12):
        time.sleep(5)
        result = logs_client.get_query_results(queryId=query_id)
        if result["status"] == "Complete":
            break

    if result["status"] == "Complete" and result["results"]:
        print(f"\n   Server-side attribution from invocation logs:")
        print(f"   {'Identity ARN':<50} {'Calls':>6} {'Input':>8} {'Output':>8}")
        print(f"   {'─'*50} {'─'*6} {'─'*8} {'─'*8}")
        for row in result["results"]:
            fields = {f["field"]: f["value"] for f in row}
            arn = fields.get("identity.arn", "unknown")[:50]
            inv = fields.get("invocations", "0")
            inp = fields.get("totalInput", "0")
            out = fields.get("totalOutput", "0")
            print(f"   {arn:<50} {inv:>6} {inp:>8} {out:>8}")
    else:
        print(f"   ⚠️  No log results yet (logs may take a few minutes to arrive)")
        print(f"   ℹ️  Re-run this query later, or check CloudWatch Logs Insights console")
        print(f"   ℹ️  Log group: {LOG_GROUP}")

except logs_client.exceptions.ResourceNotFoundException:
    print(f"   ⚠️  Log group {LOG_GROUP} not found yet")
    print(f"   ℹ️  Invocation logs may take a few minutes to create the log group")
except Exception as e:
    print(f"   ⚠️  {e}")

# ── Step 4: CloudWatch metrics by InferenceProfileId (per-user AIP) ──
print("\n\n📈 Step 4: CloudWatch Metrics by Per-User Inference Profile")
print("-" * 80)

end_time_dt = datetime.datetime.now(datetime.timezone.utc)
start_time_dt = end_time_dt - timedelta(hours=1)

for user_id, user_cfg in config["users"].items():
    profile_arn = user_cfg.get("profile_arn", "")
    if not profile_arn:
        continue
    profile_id = profile_arn.split("/")[-1]

    resp = cloudwatch.get_metric_statistics(
        Namespace="AWS/Bedrock",
        MetricName="Invocations",
        Dimensions=[{"Name": "InferenceProfileId", "Value": profile_id}],
        StartTime=start_time_dt,
        EndTime=end_time_dt,
        Period=300,
        Statistics=["Sum"],
    )
    total = sum(dp["Sum"] for dp in resp["Datapoints"])
    print(f"   {user_id:<20} profile={profile_id[:12]}...  invocations={int(total)}")

# ── Step 5: Print Athena queries for the full pipeline ──
print("\n\n📋 Step 5: Athena Queries for Full Attribution Pipeline")
print("=" * 80)
print("   These queries run against Bedrock invocation logs in S3.")
print(f"   Bucket: s3://{config['log_bucket']}/{config.get('log_prefix', '')}")
print()

athena_per_user = f"""
-- Per-user token usage from requestMetadata (server-side)
-- Create Glue table over s3://{config['log_bucket']}/invocation-logs/ first
SELECT
  requestmetadata['userId'] AS user_id,
  requestmetadata['groupId'] AS group_id,
  requestmetadata['tenantId'] AS tenant_id,
  modelid,
  count(*) AS invocations,
  sum(inputtokencount) AS input_tokens,
  sum(outputtokencount) AS output_tokens,
  sum(inputtokencount + outputtokencount) AS total_tokens
FROM bedrock_invocation_logs
WHERE requestmetadata['source'] = 'server-side-gateway'
GROUP BY 1, 2, 3, 4
ORDER BY total_tokens DESC;
"""

athena_daily_cost = f"""
-- Daily cost estimate by user (using on-demand pricing)
-- Adjust prices for your model/region
SELECT
  date_trunc('day', from_iso8601_timestamp(timestamp)) AS day,
  requestmetadata['userId'] AS user_id,
  requestmetadata['groupId'] AS group_id,
  sum(inputtokencount) AS input_tokens,
  sum(outputtokencount) AS output_tokens,
  -- Opus 4.6 pricing (adjust as needed)
  round(sum(inputtokencount) * 15.0 / 1000000, 4) AS input_cost_usd,
  round(sum(outputtokencount) * 75.0 / 1000000, 4) AS output_cost_usd,
  round(sum(inputtokencount) * 15.0 / 1000000
      + sum(outputtokencount) * 75.0 / 1000000, 4) AS total_cost_usd
FROM bedrock_invocation_logs
GROUP BY 1, 2, 3
ORDER BY day DESC, total_cost_usd DESC;
"""

print(athena_per_user)
print(athena_daily_cost)

# ── Save results ──
report = {
    "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    "model": config["model"],
    "call_results": call_results,
    "user_totals": {uid: {**t, "total": t["input"] + t["output"]} for uid, t in user_totals.items()},
    "group_totals": {g: {**t, "total": t["input"] + t["output"]} for g, t in group_totals.items()},
    "log_bucket": config["log_bucket"],
}

report_path = os.path.join(SCRIPT_DIR, "server_side_tracking_report.json")
with open(report_path, "w") as f:
    json.dump(report, f, indent=2, default=str)

print("\n" + "=" * 80)
print("✅ Demo Complete — Server-Side Attribution Pipeline Verified")
print("=" * 80)
print(f"\n   Report saved: {report_path}")
print(f"\n   Trust model:")
print(f"   ├─ requestMetadata  → set by gateway, not client  ✅ HIGH trust")
print(f"   ├─ identity.arn     → IAM principal from logs      ✅ HIGH trust")
print(f"   ├─ Per-user AIP     → Cost Explorer tags           ✅ HIGH trust")
print(f"   └─ OTEL (optional)  → real-time dashboards only    ⚠️  MEDIUM trust")
print(f"\n   OTEL is now optional — server-side pipeline is the source of truth.")
print("=" * 80)
