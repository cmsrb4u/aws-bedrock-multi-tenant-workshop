"""
Deploy CloudWatch Dashboard for Per-User Bedrock Usage Tracking

Creates a production-grade dashboard with:
  Row 1: Per-user token consumption (single-value with sparklines)
  Row 2: Per-user quota utilization gauges
  Row 3: Token usage trends over time (per user)
  Row 4: Invocation latency per user
  Row 5: Group-level comparison (bar charts)
  Row 6: Summary table

Reads user profiles and AIP IDs from server_side_tracking_config.json.
"""

import boto3
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from lab_helpers.config import Region

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DASHBOARD_NAME = "Bedrock-ServerSide-UserTracking"

config_path = os.path.join(SCRIPT_DIR, "server_side_tracking_config.json")
try:
    with open(config_path) as f:
        config = json.load(f)
except FileNotFoundError:
    print(f"❌ Config not found at {config_path}")
    print("   Run setup_server_side_tracking.py first")
    sys.exit(1)

cloudwatch = boto3.client("cloudwatch", region_name=Region)

# ── Build user list with profile IDs ──
users = []
for user_id, user_cfg in config["users"].items():
    profile_arn = user_cfg.get("profile_arn", "")
    if not profile_arn:
        continue
    profile_id = profile_arn.split("/")[-1]
    users.append({
        "id": user_id,
        "profile_id": profile_id,
        "group": user_cfg["group"],
        "tenant": user_cfg["tenant"],
        "department": user_cfg["department"],
    })

if not users:
    print("❌ No users with profile ARNs found in config")
    sys.exit(1)

# ── Color palette for users ──
COLORS = ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd", "#8c564b"]

# ── Monthly token limits per user (configurable) ──
DEFAULT_MONTHLY_LIMIT = 500_000_000  # 500M tokens
USER_LIMITS = {u["id"]: DEFAULT_MONTHLY_LIMIT for u in users}


def metric(namespace, name, profile_id, stat="Sum", period=300):
    """Build a CloudWatch metric definition (4 items + options dict)."""
    return [namespace, name, "InferenceProfileId", profile_id, {"stat": stat}]


def single_value_widget(user, y, x, width=6, height=4):
    """Single-value widget with sparkline for a user's monthly token usage."""
    return {
        "type": "metric",
        "x": x, "y": y, "width": width, "height": height,
        "properties": {
            "metrics": [
                ["AWS/Bedrock", "InputTokenCount", "InferenceProfileId", user["profile_id"], {"id": "m1", "visible": False}],
                ["AWS/Bedrock", "OutputTokenCount", "InferenceProfileId", user["profile_id"], {"id": "m2", "visible": False}],
                [{"expression": "m1 + m2", "label": "Total Tokens", "id": "total"}],
            ],
            "view": "singleValue",
            "region": Region,
            "title": f"{user['id']} — Monthly Tokens",
            "period": 3600,
            "stat": "Sum",
            "sparkline": True,
        },
    }


def gauge_widget(user, y, x, width=6, height=5):
    """Gauge widget showing quota utilization percentage."""
    limit = USER_LIMITS.get(user["id"], DEFAULT_MONTHLY_LIMIT)
    return {
        "type": "metric",
        "x": x, "y": y, "width": width, "height": height,
        "properties": {
            "metrics": [
                ["AWS/Bedrock", "InputTokenCount", "InferenceProfileId", user["profile_id"], {"id": "m1", "visible": False}],
                ["AWS/Bedrock", "OutputTokenCount", "InferenceProfileId", user["profile_id"], {"id": "m2", "visible": False}],
                [{
                    "expression": f"((m1 + m2) / {limit}) * 100",
                    "label": "Quota %",
                    "id": "pct",
                }],
            ],
            "view": "gauge",
            "region": Region,
            "title": f"{user['id']} — Quota %",
            "period": 2592000,  # 30 days
            "stat": "Sum",
            "yAxis": {"left": {"min": 0, "max": 100}},
            "annotations": {
                "horizontal": [
                    {"color": "#ff9900", "label": "Warning", "value": 80},
                    {"color": "#d13212", "label": "Critical", "value": 95},
                ],
            },
        },
    }


def timeseries_widget(users_list, metric_name, title, y, x=0, width=24, height=6, stat="Sum"):
    """Time-series graph showing a metric for all users."""
    metrics = []
    for i, user in enumerate(users_list):
        m = metric("AWS/Bedrock", metric_name, user["profile_id"], stat=stat, period=3600)
        m[-1]["label"] = user["id"]
        m[-1]["color"] = COLORS[i % len(COLORS)]
        metrics.append(m)

    widget = {
        "type": "metric",
        "x": x, "y": y, "width": width, "height": height,
        "properties": {
            "metrics": metrics,
            "view": "timeSeries",
            "stacked": False,
            "region": Region,
            "title": title,
            "period": 3600,
            "stat": stat,
            "yAxis": {"left": {"label": "Tokens" if "Token" in metric_name else "Count"}},
        },
    }

    # Add quota limit annotations for token metrics
    if "Token" in metric_name:
        annotations = []
        for i, user in enumerate(users_list):
            limit = USER_LIMITS.get(user["id"], DEFAULT_MONTHLY_LIMIT)
            # Hourly slice of monthly limit
            hourly_limit = limit / (30 * 24)
            annotations.append({
                "color": COLORS[i % len(COLORS)],
                "label": f"{user['id']} hourly limit",
                "value": hourly_limit,
                "fill": "none",
            })
        widget["properties"]["annotations"] = {"horizontal": annotations}

    return widget


def bar_chart_widget(users_list, title, y, x=0, width=12, height=6):
    """Bar chart comparing current token usage across users."""
    metrics = []
    for i, user in enumerate(users_list):
        metrics.append(["AWS/Bedrock", "InputTokenCount", "InferenceProfileId", user["profile_id"]])
        metrics.append(["AWS/Bedrock", "OutputTokenCount", "InferenceProfileId", user["profile_id"]])

    return {
        "type": "metric",
        "x": x, "y": y, "width": width, "height": height,
        "properties": {
            "metrics": metrics,
            "view": "bar",
            "region": Region,
            "title": title,
            "period": 86400,  # daily
            "stat": "Sum",
        },
    }


def text_widget(content, y, x=0, width=24, height=2):
    """Markdown text widget."""
    return {
        "type": "text",
        "x": x, "y": y, "width": width, "height": height,
        "properties": {"markdown": content},
    }


# ═══════════════════════════════════════════════════════════════════════════════
# BUILD DASHBOARD
# ═══════════════════════════════════════════════════════════════════════════════

widgets = []
y = 0

# ── Header ──
header_md = f"""# 🔬 Server-Side User-Level Bedrock Tracking
**Source of truth**: Bedrock invocation logs + per-user AIPs (server-side, high trust)
| User | Group | Tenant | Department | Profile ID |
|------|-------|--------|------------|------------|
"""
for u in users:
    header_md += f"| {u['id']} | {u['group']} | {u['tenant']} | {u['department']} | `{u['profile_id'][:12]}...` |\n"

widgets.append(text_widget(header_md, y))
y += 2

# ── Row 1: Single-value sparklines per user ──
col_width = 24 // max(len(users), 1)
for i, user in enumerate(users):
    widgets.append(single_value_widget(user, y, x=i * col_width, width=col_width))
y += 4

# ── Row 2: Quota gauges per user ──
for i, user in enumerate(users):
    widgets.append(gauge_widget(user, y, x=i * col_width, width=col_width))
y += 5

# ── Row 3: Token usage trends (all users overlaid) ──
widgets.append(timeseries_widget(users, "InputTokenCount", "Input Token Trend (Hourly)", y, width=12))
widgets.append(timeseries_widget(users, "OutputTokenCount", "Output Token Trend (Hourly)", y, x=12, width=12))
y += 6

# ── Row 4: Invocation count + latency ──
widgets.append(timeseries_widget(users, "Invocations", "Invocations (Hourly)", y, width=12))
widgets.append(timeseries_widget(users, "InvocationLatency", "Invocation Latency (Avg ms)", y, x=12, width=12, stat="Average"))
y += 6

# ── Row 5: Bar charts — usage comparison ──
widgets.append(bar_chart_widget(users, "Daily Token Usage by User", y, width=12))

# Quota % comparison bar chart — simplified per-user gauges side by side
for i, user in enumerate(users):
    limit = USER_LIMITS.get(user["id"], DEFAULT_MONTHLY_LIMIT)
    widgets.append({
        "type": "metric",
        "x": 12 + (i * (12 // len(users))), "y": y,
        "width": 12 // len(users), "height": 6,
        "properties": {
            "metrics": [
                ["AWS/Bedrock", "InputTokenCount", "InferenceProfileId", user["profile_id"], {"id": "m1", "visible": False}],
                ["AWS/Bedrock", "OutputTokenCount", "InferenceProfileId", user["profile_id"], {"id": "m2", "visible": False}],
                [{"expression": f"((m1 + m2) / {limit}) * 100", "label": f"{user['id']} %", "id": "pct"}],
            ],
            "view": "singleValue",
            "region": Region,
            "title": f"{user['id']} Quota %",
            "period": 2592000,
            "stat": "Sum",
        },
    })
y += 6

# ── Row 6: Summary info ──
summary_md = """## 📋 Data Sources & Trust Model
| Layer | Source | Trust | Latency | Dashboard Widget |
|-------|--------|-------|---------|-----------------|
| Per-user AIP metrics | CloudWatch `AWS/Bedrock` | ✅ High | ~1 min | Rows 1-5 above |
| `requestMetadata` | Bedrock invocation logs → S3 | ✅ High | ~5 min | Athena queries |
| `identity.arn` | CloudWatch Logs Insights | ✅ High | ~5 min | Athena queries |
| OTEL (optional) | Client-reported | ⚠️ Medium | Real-time | Not used here |

**Athena queries**: See `attribution_queries.sql` for per-user cost attribution, group chargebacks, and hourly heatmaps.
"""
widgets.append(text_widget(summary_md, y))

# ═══════════════════════════════════════════════════════════════════════════════
# DEPLOY
# ═══════════════════════════════════════════════════════════════════════════════

dashboard_body = json.dumps({"widgets": widgets})

print("=" * 80)
print(f"📊 Deploying CloudWatch Dashboard: {DASHBOARD_NAME}")
print(f"   Region: {Region}")
print(f"   Users:  {len(users)}")
print(f"   Widgets: {len(widgets)}")
print("=" * 80)

try:
    cloudwatch.put_dashboard(
        DashboardName=DASHBOARD_NAME,
        DashboardBody=dashboard_body,
    )
    console_url = (
        f"https://{Region}.console.aws.amazon.com/cloudwatch/home"
        f"?region={Region}#dashboards/dashboard/{DASHBOARD_NAME}"
    )
    print(f"\n   ✅ Dashboard deployed successfully!")
    print(f"\n   🔗 {console_url}")
    print(f"\n   Dashboard layout:")
    print(f"   ┌─────────────────────────────────────────────────────────┐")
    print(f"   │  Header: User table with profile IDs                   │")
    print(f"   ├───────────────────┬───────────────────┬─────────────────┤")
    for u in users:
        print(f"   │ {u['id']:<17} │", end="")
    print()
    print(f"   │ Monthly Tokens     │ Monthly Tokens     │ Monthly Tokens  │")
    print(f"   │ (sparkline)        │ (sparkline)        │ (sparkline)     │")
    print(f"   ├───────────────────┼───────────────────┼─────────────────┤")
    print(f"   │ Quota % Gauge     │ Quota % Gauge     │ Quota % Gauge   │")
    print(f"   │ ⚠️ 80% / 🔴 95%    │ ⚠️ 80% / 🔴 95%    │ ⚠️ 80% / 🔴 95%  │")
    print(f"   ├─────────────────────────────┬───────────────────────────┤")
    print(f"   │ Input Token Trend (hourly)  │ Output Token Trend        │")
    print(f"   ├─────────────────────────────┼───────────────────────────┤")
    print(f"   │ Invocations (hourly)        │ Latency (avg ms)          │")
    print(f"   ├─────────────────────────────┼───────────────────────────┤")
    print(f"   │ Daily Tokens by User (bar)  │ Monthly Quota % (bar)     │")
    print(f"   ├─────────────────────────────┴───────────────────────────┤")
    print(f"   │ Data Sources & Trust Model table                       │")
    print(f"   └─────────────────────────────────────────────────────────┘")

except Exception as e:
    print(f"\n   ❌ Error: {e}")

# Save dashboard JSON for version control
dashboard_path = os.path.join(SCRIPT_DIR, "dashboard.json")
with open(dashboard_path, "w") as f:
    json.dump({"widgets": widgets}, f, indent=2)
print(f"\n   📁 Dashboard JSON saved: {dashboard_path}")
print("=" * 80)
