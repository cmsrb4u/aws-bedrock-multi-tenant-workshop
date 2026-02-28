#!/usr/bin/env python3
"""
Fix CloudWatch Dashboard to use actual available metrics
Removes InferenceProfileId dimensions and uses aggregated metrics
"""

import boto3
import json

REGION = "us-west-2"
DASHBOARD_NAME = "CCWB-Quota-Monitoring"

def create_fixed_dashboard():
    """Create dashboard with correct metric format"""

    dashboard_body = {
        "widgets": [
            # Row 1: Overview Metrics - WORKING
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
                        [{"expression": "m1 + m2", "label": "Total Tokens", "id": "e1"}],
                        ["AWS/Bedrock", "InputTokenCount", {"id": "m1", "visible": False}],
                        [".", "OutputTokenCount", {"id": "m2", "visible": False}]
                    ],
                    "view": "timeSeries",
                    "stacked": False,
                    "region": REGION,
                    "title": "Total Token Usage",
                    "period": 300,
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
                        ["AWS/Bedrock", "Invocations", {"stat": "Sum", "label": "API Calls"}]
                    ],
                    "view": "timeSeries",
                    "stacked": False,
                    "region": REGION,
                    "title": "API Call Count",
                    "period": 300
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
                        [{"expression": "m1 + m2", "label": "Total Tokens Today", "id": "e1", "stat": "Sum"}],
                        ["AWS/Bedrock", "InputTokenCount", {"id": "m1", "visible": False, "stat": "Sum"}],
                        [".", "OutputTokenCount", {"id": "m2", "visible": False, "stat": "Sum"}]
                    ],
                    "view": "singleValue",
                    "region": REGION,
                    "title": "Today's Total Usage",
                    "period": 86400
                }
            },

            # Row 2: Token Distribution
            {
                "type": "metric",
                "x": 0,
                "y": 6,
                "width": 12,
                "height": 6,
                "properties": {
                    "metrics": [
                        ["AWS/Bedrock", "InputTokenCount", {"stat": "Sum", "label": "Input Tokens", "color": "#1f77b4"}],
                        [".", "OutputTokenCount", {"stat": "Sum", "label": "Output Tokens", "color": "#ff7f0e"}]
                    ],
                    "view": "timeSeries",
                    "stacked": True,
                    "region": REGION,
                    "title": "Token Usage Distribution (Stacked)",
                    "period": 300
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
                        ["AWS/Bedrock", "Invocations", "ModelId", "us.anthropic.claude-sonnet-4-6", {"label": "Claude Sonnet 4.6"}],
                        ["...", "global.anthropic.claude-sonnet-4-5-20250929-v1:0", {"label": "Claude Sonnet 4.5"}],
                        ["...", {"stat": "Sum", "label": "All Models (Total)"}]
                    ],
                    "view": "timeSeries",
                    "stacked": False,
                    "region": REGION,
                    "title": "API Calls by Model",
                    "period": 300,
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
                        ["AWS/Bedrock", "InputTokenCount", {"id": "m1", "visible": False, "stat": "Sum"}],
                        [".", "OutputTokenCount", {"id": "m2", "visible": False, "stat": "Sum"}]
                    ],
                    "view": "gauge",
                    "region": REGION,
                    "title": "Daily Quota Usage (6M tokens)",
                    "period": 86400,
                    "yAxis": {
                        "left": {
                            "min": 0,
                            "max": 100
                        }
                    },
                    "annotations": {
                        "horizontal": [
                            {"value": 80, "label": "Warning"},
                            {"value": 100, "label": "Limit"}
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
                        ["AWS/Bedrock", "InputTokenCount", {"id": "m1", "visible": False, "stat": "Sum"}],
                        [".", "OutputTokenCount", {"id": "m2", "visible": False, "stat": "Sum"}]
                    ],
                    "view": "gauge",
                    "region": REGION,
                    "title": "Monthly Quota Usage (180M tokens)",
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
                        ["AWS/Bedrock", "InputTokenCount", {"stat": "Sum", "label": "Input Tokens"}],
                        [".", "OutputTokenCount", {"stat": "Sum", "label": "Output Tokens"}],
                        [".", "Invocations", {"stat": "Sum", "label": "API Calls"}]
                    ],
                    "view": "singleValue",
                    "region": REGION,
                    "title": "Last Hour Metrics",
                    "period": 3600
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
                        [{"expression": "RATE(m1+m2)", "label": "Tokens/Minute", "id": "e1"}],
                        ["AWS/Bedrock", "InputTokenCount", {"id": "m1", "visible": False}],
                        [".", "OutputTokenCount", {"id": "m2", "visible": False}]
                    ],
                    "view": "singleValue",
                    "region": REGION,
                    "title": "Current Token Rate",
                    "period": 300
                }
            },

            # Row 4: Detailed Metrics
            {
                "type": "metric",
                "x": 0,
                "y": 18,
                "width": 12,
                "height": 6,
                "properties": {
                    "metrics": [
                        ["AWS/Bedrock", "InputTokenCount", {"stat": "Sum", "label": "Input"}],
                        [".", "OutputTokenCount", {"stat": "Sum", "label": "Output"}],
                        [".", "Invocations", {"stat": "Sum", "label": "Calls"}],
                        [{"expression": "m1/m3", "label": "Avg Input/Call", "id": "e1"}],
                        [{"expression": "m2/m3", "label": "Avg Output/Call", "id": "e2"}],
                        ["AWS/Bedrock", "InputTokenCount", {"id": "m1", "visible": False}],
                        [".", "OutputTokenCount", {"id": "m2", "visible": False}],
                        [".", "Invocations", {"id": "m3", "visible": False}]
                    ],
                    "view": "table",
                    "region": REGION,
                    "title": "Usage Summary (Last 24 Hours)",
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
                        [{"expression": "RATE(m1)", "label": "Input Tokens/Min", "id": "e1", "color": "#1f77b4"}],
                        [{"expression": "RATE(m2)", "label": "Output Tokens/Min", "id": "e2", "color": "#ff7f0e"}],
                        [{"expression": "RATE(m1+m2)", "label": "Total Tokens/Min", "id": "e3", "color": "#2ca02c"}],
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
                        [{"expression": "(m1 / 1000000) * 3.00", "label": "Input Cost ($3/M)", "id": "e1", "color": "#1f77b4"}],
                        [{"expression": "(m2 / 1000000) * 15.00", "label": "Output Cost ($15/M)", "id": "e2", "color": "#ff7f0e"}],
                        [{"expression": "e1 + e2", "label": "Total Cost", "id": "e3", "color": "#2ca02c"}],
                        ["AWS/Bedrock", "InputTokenCount", {"id": "m1", "visible": False}],
                        [".", "OutputTokenCount", {"id": "m2", "visible": False}]
                    ],
                    "view": "timeSeries",
                    "stacked": False,
                    "region": REGION,
                    "title": "Estimated Cost (Claude Sonnet Pricing)",
                    "period": 3600,
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
                        [{"expression": "((m1 / 1000000) * 3) + ((m2 / 1000000) * 15)", "label": "Today's Cost", "id": "e1", "stat": "Sum"}],
                        ["AWS/Bedrock", "InputTokenCount", {"id": "m1", "visible": False, "stat": "Sum"}],
                        [".", "OutputTokenCount", {"id": "m2", "visible": False, "stat": "Sum"}]
                    ],
                    "view": "singleValue",
                    "region": REGION,
                    "title": "Today's Total Cost ($)",
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
                        [{"expression": "((m1 / 1000000) * 3) + ((m2 / 1000000) * 15)", "label": "This Month", "id": "e1", "stat": "Sum"}],
                        ["AWS/Bedrock", "InputTokenCount", {"id": "m1", "visible": False, "stat": "Sum"}],
                        [".", "OutputTokenCount", {"id": "m2", "visible": False, "stat": "Sum"}]
                    ],
                    "view": "singleValue",
                    "region": REGION,
                    "title": "Month-to-Date Cost ($)",
                    "period": 2628000
                }
            },

            # Row 6: Invocation Analysis
            {
                "type": "metric",
                "x": 0,
                "y": 30,
                "width": 24,
                "height": 6,
                "properties": {
                    "metrics": [
                        ["AWS/Bedrock", "InputTokenCount", {"stat": "Average", "label": "Avg Input Tokens per Call"}],
                        [".", "OutputTokenCount", {"stat": "Average", "label": "Avg Output Tokens per Call"}]
                    ],
                    "view": "bar",
                    "stacked": False,
                    "region": REGION,
                    "title": "Average Tokens per Invocation (Hourly)",
                    "period": 3600
                }
            }
        ]
    }

    return json.dumps(dashboard_body)

def update_dashboard():
    """Update the CloudWatch dashboard with fixed metrics"""

    client = boto3.client('cloudwatch', region_name=REGION)

    print("\n🔧 Fixing dashboard with correct metrics...")

    dashboard_body = create_fixed_dashboard()

    try:
        response = client.put_dashboard(
            DashboardName=DASHBOARD_NAME,
            DashboardBody=dashboard_body
        )

        if response['ResponseMetadata']['HTTPStatusCode'] == 200:
            print("✅ Dashboard fixed successfully!")
            print(f"\n📊 View your updated dashboard:")
            print(f"https://console.aws.amazon.com/cloudwatch/home?region={REGION}#dashboards:name={DASHBOARD_NAME}")
            return True

    except Exception as e:
        print(f"❌ Error updating dashboard: {str(e)}")
        return False

def main():
    print("\n" + "="*60)
    print("🔧 FIXING CLOUDWATCH DASHBOARD")
    print("="*60)

    print("\n📝 Changes being made:")
    print("  • Removing InferenceProfileId dimensions (not available)")
    print("  • Using aggregated metrics (no dimensions)")
    print("  • Adding ModelId dimension where available")
    print("  • Fixing metric expressions and calculations")

    success = update_dashboard()

    if success:
        print("\n✅ Dashboard is now using the correct metrics!")
        print("\n📈 What you'll see:")
        print("  • Real-time token usage (input/output)")
        print("  • API call counts")
        print("  • Daily/monthly quota percentages")
        print("  • Cost estimates")
        print("  • Token rate (tokens/minute)")
        print("  • Average tokens per invocation")

        print("\n⏱️ Refresh the dashboard to see your data!")

    print("\n" + "="*60)

if __name__ == "__main__":
    main()