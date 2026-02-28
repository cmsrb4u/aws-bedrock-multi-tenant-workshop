#!/usr/bin/env python3
"""
Create CloudWatch Dashboard for User-Level Quota Monitoring
Shows per-user token usage, quota percentages, and enforcement status
"""

import boto3
import json

REGION = "us-west-2"
DASHBOARD_NAME = "CCWB-UserLevel-QuotaMonitoring"

def create_user_dashboard():
    """Create dashboard JSON for user-level metrics"""

    dashboard_body = {
        "widgets": [
            # Row 1: User Overview
            {
                "type": "metric",
                "x": 0,
                "y": 0,
                "width": 12,
                "height": 6,
                "properties": {
                    "metrics": [
                        ["CCWB/UserQuota", "UserInputTokens", {"stat": "Sum", "label": "Input Tokens"}],
                        [".", "UserOutputTokens", {"stat": "Sum", "label": "Output Tokens"}]
                    ],
                    "view": "timeSeries",
                    "stacked": False,
                    "region": REGION,
                    "title": "User Token Usage (All Users)",
                    "period": 300
                }
            },
            {
                "type": "metric",
                "x": 12,
                "y": 0,
                "width": 12,
                "height": 6,
                "properties": {
                    "metrics": [
                        ["CCWB/UserQuota", "MonthlyUsagePercent", {"stat": "Average"}],
                        [".", "DailyUsagePercent", {"stat": "Average"}]
                    ],
                    "view": "timeSeries",
                    "stacked": False,
                    "region": REGION,
                    "title": "Average Quota Usage % (All Users)",
                    "period": 300
                }
            },

            # Row 2: Per-User Token Usage
            {
                "type": "metric",
                "x": 0,
                "y": 6,
                "width": 24,
                "height": 6,
                "properties": {
                    "metrics": [
                        ["CCWB/UserQuota", "UserInputTokens", "UserEmail", "john.doe@company.com", {"label": "John Doe - Input"}],
                        [".", "UserOutputTokens", ".", ".", {"label": "John Doe - Output"}],
                        [".", "UserInputTokens", ".", "jane.smith@company.com", {"label": "Jane Smith - Input"}],
                        [".", "UserOutputTokens", ".", ".", {"label": "Jane Smith - Output"}],
                        [".", "UserInputTokens", ".", "bob.marketing@company.com", {"label": "Bob Marketing - Input"}],
                        [".", "UserOutputTokens", ".", ".", {"label": "Bob Marketing - Output"}],
                        [".", "UserInputTokens", ".", "alice.exec@company.com", {"label": "Alice Exec - Input"}],
                        [".", "UserOutputTokens", ".", ".", {"label": "Alice Exec - Output"}]
                    ],
                    "view": "timeSeries",
                    "stacked": False,
                    "region": REGION,
                    "title": "Token Usage by User",
                    "period": 300
                }
            },

            # Row 3: User Quota Status Gauges
            {
                "type": "metric",
                "x": 0,
                "y": 12,
                "width": 6,
                "height": 6,
                "properties": {
                    "metrics": [
                        ["CCWB/UserQuota", "MonthlyUsagePercent", "UserEmail", "john.doe@company.com", {"label": "John Doe (Eng)"}]
                    ],
                    "view": "gauge",
                    "region": REGION,
                    "title": "John Doe - Monthly Quota",
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
                        ["CCWB/UserQuota", "MonthlyUsagePercent", "UserEmail", "jane.smith@company.com", {"label": "Jane Smith (Sales)"}]
                    ],
                    "view": "gauge",
                    "region": REGION,
                    "title": "Jane Smith - Monthly Quota",
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
                "x": 12,
                "y": 12,
                "width": 6,
                "height": 6,
                "properties": {
                    "metrics": [
                        ["CCWB/UserQuota", "MonthlyUsagePercent", "UserEmail", "bob.marketing@company.com", {"label": "Bob (Marketing)"}]
                    ],
                    "view": "gauge",
                    "region": REGION,
                    "title": "Bob Marketing - Monthly Quota",
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
                        ["CCWB/UserQuota", "MonthlyUsagePercent", "UserEmail", "alice.exec@company.com", {"label": "Alice (Exec)"}]
                    ],
                    "view": "gauge",
                    "region": REGION,
                    "title": "Alice Exec - Monthly Quota",
                    "period": 86400,
                    "yAxis": {
                        "left": {
                            "min": 0,
                            "max": 100
                        }
                    }
                }
            },

            # Row 4: User Ranking Table
            {
                "type": "metric",
                "x": 0,
                "y": 18,
                "width": 12,
                "height": 6,
                "properties": {
                    "metrics": [
                        ["CCWB/UserQuota", "UserInputTokens", "UserEmail", "john.doe@company.com", {"stat": "Sum", "label": "John Doe"}],
                        ["...", "jane.smith@company.com", {"stat": "Sum", "label": "Jane Smith"}],
                        ["...", "bob.marketing@company.com", {"stat": "Sum", "label": "Bob Marketing"}],
                        ["...", "alice.exec@company.com", {"stat": "Sum", "label": "Alice Exec"}]
                    ],
                    "view": "table",
                    "region": REGION,
                    "title": "User Token Usage Ranking (Last 24 Hours)",
                    "period": 86400
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
                        ["CCWB/UserQuota", "DailyUsagePercent", "UserEmail", "john.doe@company.com", {"stat": "Maximum", "label": "John Doe"}],
                        ["...", "jane.smith@company.com", {"stat": "Maximum", "label": "Jane Smith"}],
                        ["...", "bob.marketing@company.com", {"stat": "Maximum", "label": "Bob Marketing"}],
                        ["...", "alice.exec@company.com", {"stat": "Maximum", "label": "Alice Exec"}]
                    ],
                    "view": "table",
                    "region": REGION,
                    "title": "Daily Quota Usage % (Peak)",
                    "period": 86400
                }
            },

            # Row 5: Group Aggregations
            {
                "type": "metric",
                "x": 0,
                "y": 24,
                "width": 24,
                "height": 6,
                "properties": {
                    "metrics": [
                        [{"expression": "SUM(METRICS('UserInputTokens'))", "label": "Total Input Tokens", "id": "e1"}],
                        [{"expression": "SUM(METRICS('UserOutputTokens'))", "label": "Total Output Tokens", "id": "e2"}],
                        [{"expression": "e1 + e2", "label": "Total All Tokens", "id": "e3"}]
                    ],
                    "view": "singleValue",
                    "region": REGION,
                    "title": "Organization-Wide Token Usage (Today)",
                    "period": 86400
                }
            }
        ]
    }

    return json.dumps(dashboard_body)

def deploy_dashboard():
    """Deploy the user-level dashboard"""

    client = boto3.client('cloudwatch', region_name=REGION)

    dashboard_body = create_user_dashboard()

    try:
        response = client.put_dashboard(
            DashboardName=DASHBOARD_NAME,
            DashboardBody=dashboard_body
        )

        if response['ResponseMetadata']['HTTPStatusCode'] == 200:
            print(f"✅ User-level dashboard created successfully!")
            print(f"\n📊 View at:")
            print(f"https://console.aws.amazon.com/cloudwatch/home?region={REGION}#dashboards:name={DASHBOARD_NAME}")
            return True

    except Exception as e:
        print(f"❌ Error creating dashboard: {str(e)}")
        return False

def main():
    print("\n" + "="*70)
    print("CREATING USER-LEVEL CLOUDWATCH DASHBOARD")
    print("="*70)

    print("\nThis dashboard will show:")
    print("  • Per-user token usage")
    print("  • Individual quota percentages")
    print("  • User ranking by usage")
    print("  • Group aggregations")

    if deploy_dashboard():
        print("\n✅ Dashboard deployed successfully!")

    print("\n" + "="*70)

if __name__ == "__main__":
    main()