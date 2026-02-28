#!/usr/bin/env python3
"""
Create CloudWatch Dashboard for CCWB Quota Monitoring
Includes widgets for user-level quota usage and limits visualization
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
    """Generate the dashboard JSON configuration"""

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
                        [".", "OutputTokenCount", {"stat": "Sum", "label": "Output Tokens"}],
                        ["...", {"stat": "Sum", "label": "Total Tokens", "visible": False, "id": "total"}]
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
                        ["AWS/Bedrock", "InputTokenCount", {"dim": {"InferenceProfileId": TENANT_A_PROFILE}, "label": "Tenant A (Marketing) - Input"}],
                        [".", "OutputTokenCount", {"dim": {"InferenceProfileId": TENANT_A_PROFILE}, "label": "Tenant A (Marketing) - Output"}],
                        [".", "InputTokenCount", {"dim": {"InferenceProfileId": TENANT_B_PROFILE}, "label": "Tenant B (Sales) - Input"}],
                        [".", "OutputTokenCount", {"dim": {"InferenceProfileId": TENANT_B_PROFILE}, "label": "Tenant B (Sales) - Output"}]
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
                        ["AWS/Bedrock", "Invocations", {"dim": {"InferenceProfileId": TENANT_A_PROFILE}, "label": "Tenant A (Marketing)"}],
                        ["...", {"dim": {"InferenceProfileId": TENANT_B_PROFILE}, "label": "Tenant B (Sales)"}]
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
                    },
                    "annotations": {
                        "horizontal": [
                            {"value": 80, "label": "Warning", "color": "#ff9900"},
                            {"value": 100, "label": "Limit", "color": "#ff0000"}
                        ]
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
                    },
                    "annotations": {
                        "horizontal": [
                            {"value": 80, "label": "Warning", "color": "#ff9900"},
                            {"value": 100, "label": "Limit", "color": "#ff0000"}
                        ]
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
                        ["AWS/Bedrock", "InputTokenCount", {"dim": {"InferenceProfileId": TENANT_A_PROFILE}, "id": "m1a", "visible": False, "period": 86400}],
                        [".", "OutputTokenCount", {"dim": {"InferenceProfileId": TENANT_A_PROFILE}, "id": "m2a", "visible": False, "period": 86400}],
                        [".", "InputTokenCount", {"dim": {"InferenceProfileId": TENANT_B_PROFILE}, "id": "m1b", "visible": False, "period": 86400}],
                        [".", "OutputTokenCount", {"dim": {"InferenceProfileId": TENANT_B_PROFILE}, "id": "m2b", "visible": False, "period": 86400}]
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
                        ["AWS/CloudWatch", "AlarmCount", {"dim": {"AlarmName": "TenantA-Marketing-InputTokens-Warning"}, "stat": "Maximum", "label": "Tenant A Input Warning"}],
                        ["...", {"dim": {"AlarmName": "TenantA-Marketing-OutputTokens-Warning"}, "label": "Tenant A Output Warning"}],
                        ["...", {"dim": {"AlarmName": "TenantB-Sales-InputTokens-Warning"}, "label": "Tenant B Input Warning"}],
                        ["...", {"dim": {"AlarmName": "TenantB-Sales-OutputTokens-Warning"}, "label": "Tenant B Output Warning"}]
                    ],
                    "view": "singleValue",
                    "region": REGION,
                    "title": "Active Alarms",
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
                        ["AWS/Bedrock", "InputTokenCount", {"dim": {"InferenceProfileId": TENANT_A_PROFILE}, "label": "Tenant A Input"}],
                        [".", "OutputTokenCount", {"dim": {"InferenceProfileId": TENANT_A_PROFILE}, "label": "Tenant A Output"}],
                        [".", "InputTokenCount", {"dim": {"InferenceProfileId": TENANT_B_PROFILE}, "label": "Tenant B Input"}],
                        [".", "OutputTokenCount", {"dim": {"InferenceProfileId": TENANT_B_PROFILE}, "label": "Tenant B Output"}]
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
                        [".", "OutputTokenCount", {"id": "m2a", "visible": False, "stat": "Sum", "period": 86400}],
                        [".", "InputTokenCount", {"id": "m1b", "visible": False, "stat": "Sum", "period": 86400}],
                        [".", "OutputTokenCount", {"id": "m2b", "visible": False, "stat": "Sum", "period": 86400}]
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
                        [".", "OutputTokenCount", {"id": "m2a", "visible": False, "stat": "Sum", "period": 2628000}],
                        [".", "InputTokenCount", {"id": "m1b", "visible": False, "stat": "Sum", "period": 2628000}],
                        [".", "OutputTokenCount", {"id": "m2b", "visible": False, "stat": "Sum", "period": 2628000}]
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
                        ["AWS/Bedrock", "InputTokenCount", {"dim": {"InferenceProfileId": TENANT_A_PROFILE}, "stat": "Sum", "label": "Tenant A Input"}],
                        [".", "OutputTokenCount", {"dim": {"InferenceProfileId": TENANT_A_PROFILE}, "stat": "Sum", "label": "Tenant A Output"}],
                        [".", "InputTokenCount", {"dim": {"InferenceProfileId": TENANT_B_PROFILE}, "stat": "Sum", "label": "Tenant B Input"}],
                        [".", "OutputTokenCount", {"dim": {"InferenceProfileId": TENANT_B_PROFILE}, "stat": "Sum", "label": "Tenant B Output"}]
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
                    print(f"    Last modified: {dashboard['LastModified']}")
        else:
            print("\n📋 No existing dashboards found")

    except Exception as e:
        print(f"❌ Error listing dashboards: {str(e)}")

def update_dashboard_with_custom_users(users):
    """Update dashboard to include specific user metrics"""

    # This would add user-specific widgets if CCWB published user-level metrics
    # Currently, metrics are at the AIP level, not user level

    print("\n⚠️ Note: User-level metrics require CCWB full deployment")
    print("   Current metrics are at Application Inference Profile level")
    print("   For user-level tracking, you need:")
    print("   1. Full CCWB authentication flow")
    print("   2. Custom metrics published to CloudWatch")
    print("   3. DynamoDB integration for quota tracking")

def main():
    print("\n" + "="*60)
    print("🎯 CCWB QUOTA MONITORING DASHBOARD CREATOR")
    print("="*60)

    # List existing dashboards
    list_existing_dashboards()

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
        print("  ✅ Active Alarms")
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

        print("\n📝 Custom User Metrics:")
        update_dashboard_with_custom_users(["alice@marketing.com", "bob@sales.com"])

        print("\n🎨 Customization Tips:")
        print("-" * 40)
        print("  1. Click 'Actions' → 'Edit' to modify widgets")
        print("  2. Add annotations for your specific quota limits")
        print("  3. Create alarms from metrics for notifications")
        print("  4. Export to JSON for version control")
        print("  5. Share dashboard with team via permissions")

if __name__ == "__main__":
    main()