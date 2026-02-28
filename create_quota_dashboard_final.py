#!/usr/bin/env python3
"""
Create CloudWatch Dashboard for CCWB Quota Monitoring - Final Version
Correct CloudWatch metric format with proper dimension syntax
"""

import boto3
import json
from datetime import datetime

# Configuration
REGION = "us-west-2"
DASHBOARD_NAME = "CCWB-Quota-Monitoring"
TENANT_A_PROFILE = "5gematyf83m0"  # Marketing
TENANT_B_PROFILE = "yku79b5wumnr"  # Sales

def create_dashboard_json():
    """Generate the dashboard JSON configuration with correct CloudWatch format"""

    dashboard_body = {
        "widgets": [
            # Row 1: Overview Metrics
            {
                "type": "metric",
                "x": 0,
                "y": 0,
                "width": 8,
                "height": 6,
                "properties": {
                    "metrics": [
                        ["AWS/Bedrock", "InputTokenCount", {"stat": "Sum", "label": "Input Tokens"}],
                        [".", "OutputTokenCount", {"stat": "Sum", "label": "Output Tokens"}]
                    ],
                    "view": "timeSeries",
                    "stacked": False,
                    "region": REGION,
                    "title": "Total Token Usage (All Users)",
                    "period": 3600,
                    "yAxis": {
                        "left": {
                            "label": "Tokens",
                            "showUnits": False
                        }
                    }
                }
            },
            {
                "type": "metric",
                "x": 8,
                "y": 0,
                "width": 8,
                "height": 6,
                "properties": {
                    "metrics": [
                        ["AWS/Bedrock", "Invocations", {"stat": "Sum"}]
                    ],
                    "view": "timeSeries",
                    "stacked": False,
                    "region": REGION,
                    "title": "API Call Count",
                    "period": 3600
                }
            },
            {
                "type": "metric",
                "x": 16,
                "y": 0,
                "width": 8,
                "height": 6,
                "properties": {
                    "metrics": [
                        [{"expression": "m1 + m2", "label": "Today's Total", "id": "e1"}],
                        ["AWS/Bedrock", "InputTokenCount", {"id": "m1", "visible": False}],
                        [".", "OutputTokenCount", {"id": "m2", "visible": False}]
                    ],
                    "view": "singleValue",
                    "region": REGION,
                    "title": "Today's Token Usage",
                    "period": 86400
                }
            },

            # Row 2: Per-Tenant Usage - FIXED FORMAT
            {
                "type": "metric",
                "x": 0,
                "y": 6,
                "width": 12,
                "height": 6,
                "properties": {
                    "metrics": [
                        ["AWS/Bedrock", "InputTokenCount", "InferenceProfileId", TENANT_A_PROFILE, {"label": "Tenant A (Marketing) - Input"}],
                        [".", "OutputTokenCount", ".", ".", {"label": "Tenant A (Marketing) - Output"}],
                        [".", "InputTokenCount", ".", TENANT_B_PROFILE, {"label": "Tenant B (Sales) - Input"}],
                        [".", "OutputTokenCount", ".", ".", {"label": "Tenant B (Sales) - Output"}]
                    ],
                    "view": "timeSeries",
                    "stacked": False,
                    "region": REGION,
                    "title": "Token Usage by Tenant",
                    "period": 3600
                }
            },
            {
                "type": "metric",
                "x": 12,
                "y": 6,
                "width": 12,
                "height": 6,
                "properties": {
                    "metrics": [
                        ["AWS/Bedrock", "Invocations", "InferenceProfileId", TENANT_A_PROFILE, {"label": "Tenant A (Marketing)"}],
                        [".", ".", ".", TENANT_B_PROFILE, {"label": "Tenant B (Sales)"}]
                    ],
                    "view": "timeSeries",
                    "stacked": False,
                    "region": REGION,
                    "title": "API Calls by Tenant",
                    "period": 3600
                }
            },

            # Row 3: Quota Usage Gauges
            {
                "type": "metric",
                "x": 0,
                "y": 12,
                "width": 6,
                "height": 6,
                "properties": {
                    "metrics": [
                        [{"expression": "(m1 + m2) / 6000000 * 100", "label": "Daily Usage %", "id": "e1"}],
                        ["AWS/Bedrock", "InputTokenCount", {"id": "m1", "visible": False}],
                        [".", "OutputTokenCount", {"id": "m2", "visible": False}]
                    ],
                    "view": "gauge",
                    "region": REGION,
                    "title": "Daily Quota Usage",
                    "period": 86400,
                    "yAxis": {
                        "left": {
                            "min": 0,
                            "max": 100
                        }
                    }
                }
            },
            {
                "type": "metric",
                "x": 6,
                "y": 12,
                "width": 6,
                "height": 6,
                "properties": {
                    "metrics": [
                        [{"expression": "(m1 + m2) / 180000000 * 100", "label": "Monthly Usage %", "id": "e1"}],
                        ["AWS/Bedrock", "InputTokenCount", {"id": "m1", "visible": False}],
                        [".", "OutputTokenCount", {"id": "m2", "visible": False}]
                    ],
                    "view": "gauge",
                    "region": REGION,
                    "title": "Monthly Quota Usage",
                    "period": 2628000,
                    "yAxis": {
                        "left": {
                            "min": 0,
                            "max": 100
                        }
                    }
                }
            },
            {
                "type": "metric",
                "x": 12,
                "y": 12,
                "width": 6,
                "height": 6,
                "properties": {
                    "metrics": [
                        [{"expression": "(m1a + m2a) / 5000000 * 100", "label": "Tenant A %", "id": "e1"}],
                        [{"expression": "(m1b + m2b) / 3000000 * 100", "label": "Tenant B %", "id": "e2"}],
                        ["AWS/Bedrock", "InputTokenCount", "InferenceProfileId", TENANT_A_PROFILE, {"id": "m1a", "visible": False}],
                        [".", "OutputTokenCount", ".", ".", {"id": "m2a", "visible": False}],
                        [".", "InputTokenCount", ".", TENANT_B_PROFILE, {"id": "m1b", "visible": False}],
                        [".", "OutputTokenCount", ".", ".", {"id": "m2b", "visible": False}]
                    ],
                    "view": "gauge",
                    "region": REGION,
                    "title": "Daily Quota by Tenant",
                    "period": 86400,
                    "yAxis": {
                        "left": {
                            "min": 0,
                            "max": 100
                        }
                    }
                }
            },
            {
                "type": "metric",
                "x": 18,
                "y": 12,
                "width": 6,
                "height": 6,
                "properties": {
                    "metrics": [
                        ["AWS/Bedrock", "InputTokenCount", {"stat": "Sum", "label": "Input Tokens Today"}],
                        [".", "OutputTokenCount", {"stat": "Sum", "label": "Output Tokens Today"}],
                        [".", "Invocations", {"stat": "Sum", "label": "API Calls Today"}]
                    ],
                    "view": "singleValue",
                    "region": REGION,
                    "title": "Today's Metrics",
                    "period": 86400
                }
            },

            # Row 4: Detailed Metrics Table
            {
                "type": "metric",
                "x": 0,
                "y": 18,
                "width": 12,
                "height": 6,
                "properties": {
                    "metrics": [
                        ["AWS/Bedrock", "InputTokenCount", "InferenceProfileId", TENANT_A_PROFILE, {"label": "Tenant A Input"}],
                        [".", "OutputTokenCount", ".", ".", {"label": "Tenant A Output"}],
                        [".", "InputTokenCount", ".", TENANT_B_PROFILE, {"label": "Tenant B Input"}],
                        [".", "OutputTokenCount", ".", ".", {"label": "Tenant B Output"}]
                    ],
                    "view": "table",
                    "region": REGION,
                    "title": "Token Usage Summary (Last 24 Hours)",
                    "period": 86400,
                    "stat": "Sum"
                }
            },
            {
                "type": "metric",
                "x": 12,
                "y": 18,
                "width": 12,
                "height": 6,
                "properties": {
                    "metrics": [
                        [{"expression": "RATE(m1)", "label": "Input Tokens/Min", "id": "e1"}],
                        [{"expression": "RATE(m2)", "label": "Output Tokens/Min", "id": "e2"}],
                        ["AWS/Bedrock", "InputTokenCount", {"id": "m1", "visible": False}],
                        [".", "OutputTokenCount", {"id": "m2", "visible": False}]
                    ],
                    "view": "timeSeries",
                    "stacked": False,
                    "region": REGION,
                    "title": "Token Rate (Tokens per Minute)",
                    "period": 300
                }
            },

            # Row 5: Cost Tracking
            {
                "type": "metric",
                "x": 0,
                "y": 24,
                "width": 8,
                "height": 6,
                "properties": {
                    "metrics": [
                        [{"expression": "(m1 / 1000000) * 3.00", "label": "Input Cost ($3/M tokens)", "id": "e1"}],
                        [{"expression": "(m2 / 1000000) * 15.00", "label": "Output Cost ($15/M tokens)", "id": "e2"}],
                        [{"expression": "e1 + e2", "label": "Total Cost", "id": "e3"}],
                        ["AWS/Bedrock", "InputTokenCount", {"id": "m1", "visible": False}],
                        [".", "OutputTokenCount", {"id": "m2", "visible": False}]
                    ],
                    "view": "timeSeries",
                    "stacked": False,
                    "region": REGION,
                    "title": "Estimated Cost (Claude Sonnet Pricing)",
                    "period": 3600
                }
            },
            {
                "type": "metric",
                "x": 8,
                "y": 24,
                "width": 8,
                "height": 6,
                "properties": {
                    "metrics": [
                        [{"expression": "((m1 + m2) / 1000000) * 18", "label": "Today's Cost", "id": "e1"}],
                        ["AWS/Bedrock", "InputTokenCount", {"id": "m1", "visible": False}],
                        [".", "OutputTokenCount", {"id": "m2", "visible": False}]
                    ],
                    "view": "singleValue",
                    "region": REGION,
                    "title": "Today's Total Cost (Estimated)",
                    "period": 86400
                }
            },
            {
                "type": "metric",
                "x": 16,
                "y": 24,
                "width": 8,
                "height": 6,
                "properties": {
                    "metrics": [
                        [{"expression": "((m1 + m2) / 1000000) * 18", "label": "Month's Cost", "id": "e1"}],
                        ["AWS/Bedrock", "InputTokenCount", {"id": "m1", "visible": False}],
                        [".", "OutputTokenCount", {"id": "m2", "visible": False}]
                    ],
                    "view": "singleValue",
                    "region": REGION,
                    "title": "This Month's Total Cost (Estimated)",
                    "period": 2628000
                }
            },

            # Row 6: Tenant Comparison Bar Chart
            {
                "type": "metric",
                "x": 0,
                "y": 30,
                "width": 24,
                "height": 6,
                "properties": {
                    "metrics": [
                        ["AWS/Bedrock", "InputTokenCount", "InferenceProfileId", TENANT_A_PROFILE, {"stat": "Sum", "label": "Tenant A Input"}],
                        [".", "OutputTokenCount", ".", ".", {"stat": "Sum", "label": "Tenant A Output"}],
                        [".", "InputTokenCount", ".", TENANT_B_PROFILE, {"stat": "Sum", "label": "Tenant B Input"}],
                        [".", "OutputTokenCount", ".", ".", {"stat": "Sum", "label": "Tenant B Output"}]
                    ],
                    "view": "bar",
                    "stacked": True,
                    "region": REGION,
                    "title": "Tenant Token Usage Comparison (Daily)",
                    "period": 86400
                }
            }
        ]
    }

    return json.dumps(dashboard_body)

def create_dashboard():
    """Create the CloudWatch dashboard"""

    client = boto3.client('cloudwatch', region_name=REGION)

    dashboard_body = create_dashboard_json()

    try:
        response = client.put_dashboard(
            DashboardName=DASHBOARD_NAME,
            DashboardBody=dashboard_body
        )

        if response['ResponseMetadata']['HTTPStatusCode'] == 200:
            print(f"✅ Dashboard '{DASHBOARD_NAME}' created successfully!")
            print(f"\n📊 View your dashboard at:")
            print(f"https://console.aws.amazon.com/cloudwatch/home?region={REGION}#dashboards:name={DASHBOARD_NAME}")

            # Also create a direct link
            print(f"\n🔗 Direct link:")
            print(f"https://{REGION}.console.aws.amazon.com/cloudwatch/home?region={REGION}#dashboards:name={DASHBOARD_NAME}")

            return True
        else:
            print(f"❌ Failed to create dashboard: {response}")
            return False

    except Exception as e:
        print(f"❌ Error creating dashboard: {str(e)}")
        return False

def list_existing_dashboards():
    """List all existing CloudWatch dashboards"""

    client = boto3.client('cloudwatch', region_name=REGION)

    try:
        response = client.list_dashboards()

        if response['DashboardEntries']:
            print("\n📋 Existing Dashboards:")
            print("-" * 40)
            for dashboard in response['DashboardEntries']:
                print(f"  • {dashboard['DashboardName']}")
                if 'LastModified' in dashboard:
                    modified = dashboard['LastModified'].strftime('%Y-%m-%d %H:%M:%S')
                    print(f"    Last modified: {modified}")
        else:
            print("\n📋 No existing dashboards found")

    except Exception as e:
        print(f"❌ Error listing dashboards: {str(e)}")

def delete_dashboard(dashboard_name):
    """Delete an existing dashboard"""

    client = boto3.client('cloudwatch', region_name=REGION)

    try:
        response = client.delete_dashboards(
            DashboardNames=[dashboard_name]
        )
        print(f"✅ Deleted dashboard: {dashboard_name}")
        return True
    except Exception as e:
        print(f"❌ Error deleting dashboard: {str(e)}")
        return False

def main():
    print("\n" + "="*60)
    print("🎯 CCWB QUOTA MONITORING DASHBOARD CREATOR")
    print("="*60)

    # List existing dashboards
    list_existing_dashboards()

    # Check if dashboard already exists
    client = boto3.client('cloudwatch', region_name=REGION)
    try:
        existing = client.list_dashboards(DashboardNamePrefix=DASHBOARD_NAME)
        if existing['DashboardEntries']:
            print(f"\n⚠️ Dashboard '{DASHBOARD_NAME}' already exists.")
            response = input("Do you want to replace it? (y/n): ")
            if response.lower() != 'y':
                print("Dashboard creation cancelled.")
                return
            else:
                delete_dashboard(DASHBOARD_NAME)
    except:
        pass

    # Create the dashboard
    print(f"\n🔧 Creating dashboard '{DASHBOARD_NAME}'...")
    success = create_dashboard()

    if success:
        print("\n📊 Dashboard Widgets Created:")
        print("-" * 40)
        print("  Row 1: Overview")
        print("  ✅ Total Token Usage (time series)")
        print("  ✅ API Call Count (time series)")
        print("  ✅ Today's Token Usage (single value)")
        print()
        print("  Row 2: Per-Tenant Metrics")
        print("  ✅ Token Usage by Tenant (time series)")
        print("  ✅ API Calls by Tenant (time series)")
        print()
        print("  Row 3: Quota Gauges")
        print("  ✅ Daily Quota Usage % (gauge)")
        print("  ✅ Monthly Quota Usage % (gauge)")
        print("  ✅ Daily Quota by Tenant % (gauge)")
        print("  ✅ Today's Metrics (single values)")
        print()
        print("  Row 4: Detailed Analysis")
        print("  ✅ Token Usage Summary Table")
        print("  ✅ Token Rate (tokens/minute)")
        print()
        print("  Row 5: Cost Tracking")
        print("  ✅ Estimated Cost Over Time")
        print("  ✅ Today's Total Cost")
        print("  ✅ This Month's Total Cost")
        print()
        print("  Row 6: Comparisons")
        print("  ✅ Tenant Usage Comparison (bar chart)")

        print("\n💡 How to Use the Dashboard:")
        print("-" * 40)
        print("  1. Monitor real-time token usage across tenants")
        print("  2. Track against daily/monthly quota limits")
        print("  3. View cost estimates based on usage")
        print("  4. Identify usage patterns and spikes")
        print("  5. Compare tenant consumption")

        print("\n📝 Note on User-Level Metrics:")
        print("-" * 40)
        print("  • Current metrics are at tenant/AIP level")
        print("  • For user-level metrics, deploy full CCWB with:")
        print("    - Authentication flow (Cognito/OIDC)")
        print("    - DynamoDB quota tables")
        print("    - Custom CloudWatch metrics from Lambda")

        print("\n🎨 Next Steps:")
        print("-" * 40)
        print("  1. Make API calls to generate data")
        print("  2. Set up CloudWatch alarms for thresholds")
        print("  3. Export dashboard JSON for backup")
        print("  4. Share with team via IAM permissions")
        print("  5. Customize widgets for your limits")

if __name__ == "__main__":
    main()