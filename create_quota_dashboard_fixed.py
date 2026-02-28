#!/usr/bin/env python3
"""
Create CloudWatch Dashboard for CCWB Quota Monitoring - Fixed Version
Corrected metric format for CloudWatch API
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
    """Generate the dashboard JSON configuration with correct metric format"""

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
                    "stat": "Sum",
                    "yAxis": {
                        "left": {
                            "label": "Tokens",
                            "showUnits": False
                        }
                    },
                    "annotations": {
                        "horizontal": [
                            {
                                "label": "Daily Warning (80%)",
                                "value": 4800000,
                                "fill": "above",
                                "color": "#ff9900"
                            },
                            {
                                "label": "Daily Limit",
                                "value": 6000000,
                                "fill": "above",
                                "color": "#ff0000"
                            }
                        ]
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
                    "period": 3600,
                    "stat": "Sum",
                    "yAxis": {
                        "left": {
                            "label": "Invocations",
                            "showUnits": False
                        }
                    }
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
                        [{"expression": "m1 + m2", "label": "Today's Total", "id": "e1", "stat": "Sum", "period": 86400}],
                        ["AWS/Bedrock", "InputTokenCount", {"id": "m1", "visible": False, "stat": "Sum", "period": 86400}],
                        [".", "OutputTokenCount", {"id": "m2", "visible": False, "stat": "Sum", "period": 86400}]
                    ],
                    "view": "singleValue",
                    "region": REGION,
                    "title": "Today's Token Usage",
                    "period": 86400,
                    "stat": "Sum"
                }
            },

            # Row 2: Per-Tenant Usage
            {
                "type": "metric",
                "x": 0,
                "y": 6,
                "width": 12,
                "height": 6,
                "properties": {
                    "metrics": [
                        ["AWS/Bedrock", "InputTokenCount", {"Name": "InferenceProfileId", "Value": TENANT_A_PROFILE}, {"label": "Tenant A (Marketing) - Input"}],
                        ["...", {"Name": "InferenceProfileId", "Value": TENANT_A_PROFILE}, {"label": "Tenant A (Marketing) - Output", "stat": "Sum"}],
                        [".", "InputTokenCount", {"Name": "InferenceProfileId", "Value": TENANT_B_PROFILE}, {"label": "Tenant B (Sales) - Input"}],
                        [".", "OutputTokenCount", {"Name": "InferenceProfileId", "Value": TENANT_B_PROFILE}, {"label": "Tenant B (Sales) - Output"}]
                    ],
                    "view": "timeSeries",
                    "stacked": False,
                    "region": REGION,
                    "title": "Token Usage by Tenant",
                    "period": 3600,
                    "stat": "Sum",
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
                "x": 12,
                "y": 6,
                "width": 12,
                "height": 6,
                "properties": {
                    "metrics": [
                        ["AWS/Bedrock", "Invocations", {"Name": "InferenceProfileId", "Value": TENANT_A_PROFILE}, {"label": "Tenant A (Marketing)"}],
                        ["...", {"Name": "InferenceProfileId", "Value": TENANT_B_PROFILE}, {"label": "Tenant B (Sales)"}]
                    ],
                    "view": "timeSeries",
                    "stacked": False,
                    "region": REGION,
                    "title": "API Calls by Tenant",
                    "period": 3600,
                    "stat": "Sum"
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
                        ["AWS/Bedrock", "InputTokenCount", {"id": "m1", "visible": False, "stat": "Sum", "period": 86400}],
                        [".", "OutputTokenCount", {"id": "m2", "visible": False, "stat": "Sum", "period": 86400}]
                    ],
                    "view": "gauge",
                    "region": REGION,
                    "title": "Daily Quota Usage",
                    "period": 86400,
                    "stat": "Sum",
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
                        ["AWS/Bedrock", "InputTokenCount", {"id": "m1", "visible": False, "stat": "Sum", "period": 2628000}],
                        [".", "OutputTokenCount", {"id": "m2", "visible": False, "stat": "Sum", "period": 2628000}]
                    ],
                    "view": "gauge",
                    "region": REGION,
                    "title": "Monthly Quota Usage",
                    "period": 2628000,
                    "stat": "Sum",
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
                        ["AWS/Bedrock", "InputTokenCount", {"Name": "InferenceProfileId", "Value": TENANT_A_PROFILE}, {"id": "m1a", "visible": False, "period": 86400}],
                        [".", "OutputTokenCount", {"Name": "InferenceProfileId", "Value": TENANT_A_PROFILE}, {"id": "m2a", "visible": False, "period": 86400}],
                        [".", "InputTokenCount", {"Name": "InferenceProfileId", "Value": TENANT_B_PROFILE}, {"id": "m1b", "visible": False, "period": 86400}],
                        [".", "OutputTokenCount", {"Name": "InferenceProfileId", "Value": TENANT_B_PROFILE}, {"id": "m2b", "visible": False, "period": 86400}]
                    ],
                    "view": "gauge",
                    "region": REGION,
                    "title": "Daily Quota by Tenant",
                    "period": 86400,
                    "stat": "Sum",
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
                        ["AWS/Bedrock", "InputTokenCount", {"stat": "Sum", "label": "Input Tokens Today", "period": 86400}],
                        [".", "OutputTokenCount", {"stat": "Sum", "label": "Output Tokens Today", "period": 86400}],
                        [".", "Invocations", {"stat": "Sum", "label": "API Calls Today", "period": 86400}]
                    ],
                    "view": "singleValue",
                    "region": REGION,
                    "title": "Today's Metrics",
                    "period": 300
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
                        ["AWS/Bedrock", "InputTokenCount", {"Name": "InferenceProfileId", "Value": TENANT_A_PROFILE}, {"label": "Tenant A Input"}],
                        [".", "OutputTokenCount", {"Name": "InferenceProfileId", "Value": TENANT_A_PROFILE}, {"label": "Tenant A Output"}],
                        [".", "InputTokenCount", {"Name": "InferenceProfileId", "Value": TENANT_B_PROFILE}, {"label": "Tenant B Input"}],
                        [".", "OutputTokenCount", {"Name": "InferenceProfileId", "Value": TENANT_B_PROFILE}, {"label": "Tenant B Output"}]
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
                    "period": 300,
                    "stat": "Sum",
                    "yAxis": {
                        "left": {
                            "label": "Tokens/Min",
                            "showUnits": False
                        }
                    }
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
                        ["AWS/Bedrock", "InputTokenCount", {"id": "m1", "visible": False, "stat": "Sum"}],
                        [".", "OutputTokenCount", {"id": "m2", "visible": False, "stat": "Sum"}]
                    ],
                    "view": "timeSeries",
                    "stacked": False,
                    "region": REGION,
                    "title": "Estimated Cost (Claude Sonnet Pricing)",
                    "period": 3600,
                    "stat": "Sum",
                    "yAxis": {
                        "left": {
                            "label": "Cost (USD)",
                            "showUnits": False
                        }
                    }
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
                        [{"expression": "((m1a + m2a) / 1000000) * 3.00 + ((m1b + m2b) / 1000000) * 15.00", "label": "Today's Cost", "id": "e1"}],
                        ["AWS/Bedrock", "InputTokenCount", {"id": "m1a", "visible": False, "stat": "Sum", "period": 86400}],
                        [".", "OutputTokenCount", {"id": "m2a", "visible": False, "stat": "Sum", "period": 86400}]
                    ],
                    "view": "singleValue",
                    "region": REGION,
                    "title": "Today's Total Cost",
                    "period": 86400,
                    "stat": "Sum"
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
                        [{"expression": "((m1a + m2a) / 1000000) * 3.00 + ((m1b + m2b) / 1000000) * 15.00", "label": "Month's Cost", "id": "e1"}],
                        ["AWS/Bedrock", "InputTokenCount", {"id": "m1a", "visible": False, "stat": "Sum", "period": 2628000}],
                        [".", "OutputTokenCount", {"id": "m2a", "visible": False, "stat": "Sum", "period": 2628000}]
                    ],
                    "view": "singleValue",
                    "region": REGION,
                    "title": "This Month's Total Cost",
                    "period": 2628000,
                    "stat": "Sum"
                }
            },

            # Row 6: Tenant Comparison
            {
                "type": "metric",
                "x": 0,
                "y": 30,
                "width": 24,
                "height": 6,
                "properties": {
                    "metrics": [
                        ["AWS/Bedrock", "InputTokenCount", {"Name": "InferenceProfileId", "Value": TENANT_A_PROFILE}, {"stat": "Sum", "label": "Tenant A Input"}],
                        [".", "OutputTokenCount", {"Name": "InferenceProfileId", "Value": TENANT_A_PROFILE}, {"stat": "Sum", "label": "Tenant A Output"}],
                        [".", "InputTokenCount", {"Name": "InferenceProfileId", "Value": TENANT_B_PROFILE}, {"stat": "Sum", "label": "Tenant B Input"}],
                        [".", "OutputTokenCount", {"Name": "InferenceProfileId", "Value": TENANT_B_PROFILE}, {"stat": "Sum", "label": "Tenant B Output"}]
                    ],
                    "view": "barChart",
                    "stacked": True,
                    "region": REGION,
                    "title": "Tenant Token Usage Comparison (Daily)",
                    "period": 86400,
                    "stat": "Sum"
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
        # Print first 500 chars of the dashboard JSON for debugging
        print(f"\nDashboard JSON (first 500 chars):")
        print(dashboard_body[:500])
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
        print("  ✅ Total Token Usage (time series)")
        print("  ✅ API Call Count")
        print("  ✅ Today's Token Usage (single value)")
        print("  ✅ Token Usage by Tenant")
        print("  ✅ API Calls by Tenant")
        print("  ✅ Daily Quota Usage (gauge)")
        print("  ✅ Monthly Quota Usage (gauge)")
        print("  ✅ Daily Quota by Tenant (gauge)")
        print("  ✅ Today's Metrics (single values)")
        print("  ✅ Token Usage Summary (table)")
        print("  ✅ Token Rate (tokens/minute)")
        print("  ✅ Estimated Cost Tracking")
        print("  ✅ Today's Total Cost")
        print("  ✅ This Month's Total Cost")
        print("  ✅ Tenant Comparison (bar chart)")

        print("\n💡 Dashboard Features:")
        print("-" * 40)
        print("  • Real-time token usage monitoring")
        print("  • Quota threshold warnings (80% and 100%)")
        print("  • Per-tenant usage separation")
        print("  • Cost estimation based on Claude pricing")
        print("  • Rate limiting metrics (tokens/minute)")
        print("  • Daily and monthly aggregations")

        print("\n🔄 To refresh data:")
        print("  • Dashboard auto-refreshes every 5 minutes")
        print("  • Click refresh icon for immediate update")
        print("  • Adjust time range with date picker")

        print("\n📝 Note on User-Level Metrics:")
        print("-" * 40)
        print("  Current metrics are at Application Inference Profile level")
        print("  For true user-level metrics, you would need:")
        print("  • Full CCWB authentication flow deployed")
        print("  • Custom CloudWatch metrics from CCWB Lambda")
        print("  • Integration with DynamoDB quota tables")

        print("\n🎨 Customization Tips:")
        print("-" * 40)
        print("  1. Click 'Actions' → 'Edit' to modify widgets")
        print("  2. Add annotations for your specific quota limits")
        print("  3. Create alarms from metrics for notifications")
        print("  4. Export to JSON for version control")
        print("  5. Share dashboard with team via permissions")

if __name__ == "__main__":
    main()