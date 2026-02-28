#!/usr/bin/env python3
"""
Update CloudWatch Dashboard to show real-time user-level metrics from last 2 days
"""

import boto3
import json
from datetime import datetime, timedelta

REGION = "us-west-2"
DASHBOARD_NAME = "CCWB-UserLevel-QuotaMonitoring"

def create_realtime_dashboard():
    """Create dashboard with real-time metrics from last 2 days"""

    # Calculate time range
    end_time = datetime.utcnow()
    start_time = end_time - timedelta(days=2)

    dashboard_body = {
        "start": f"-P2D",  # Last 2 days
        "periodOverride": "inherit",
        "widgets": [
            # Row 1: Overview - Token Usage Trends
            {
                "type": "metric",
                "x": 0,
                "y": 0,
                "width": 12,
                "height": 6,
                "properties": {
                    "metrics": [
                        ["CCWB/UserQuota", "UserMonthlyTokens", "UserEmail", "john.doe@company.com", {"label": "John Doe", "stat": "Maximum"}],
                        ["...", "jane.smith@company.com", {"label": "Jane Smith", "stat": "Maximum"}],
                        ["...", "unknown@company.com", {"label": "Unknown User", "stat": "Maximum"}]
                    ],
                    "view": "timeSeries",
                    "stacked": False,
                    "region": REGION,
                    "title": "User Token Consumption (Last 2 Days)",
                    "period": 3600,
                    "yAxis": {
                        "left": {
                            "label": "Tokens",
                            "showUnits": False
                        }
                    },
                    "annotations": {
                        "horizontal": [
                            {
                                "label": "John Doe Limit",
                                "value": 500000000,
                                "fill": "below",
                                "color": "#1f77b4"
                            },
                            {
                                "label": "Jane Smith Limit",
                                "value": 300000000,
                                "fill": "below",
                                "color": "#ff7f0e"
                            }
                        ]
                    }
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
                        ["CCWB/UserQuota", "MonthlyUsagePercent", "UserEmail", "john.doe@company.com", {"label": "John Doe", "stat": "Maximum"}],
                        ["...", "jane.smith@company.com", {"label": "Jane Smith", "stat": "Maximum"}],
                        ["...", "unknown@company.com", {"label": "Unknown User", "stat": "Maximum"}]
                    ],
                    "view": "timeSeries",
                    "stacked": False,
                    "region": REGION,
                    "title": "Monthly Quota Usage % (Last 2 Days)",
                    "period": 3600,
                    "yAxis": {
                        "left": {
                            "label": "Percentage",
                            "min": 0,
                            "max": 100
                        }
                    },
                    "annotations": {
                        "horizontal": [
                            {
                                "label": "Warning",
                                "value": 80,
                                "fill": "above",
                                "color": "#ff9900"
                            },
                            {
                                "label": "Critical",
                                "value": 90,
                                "fill": "above",
                                "color": "#ff0000"
                            }
                        ]
                    }
                }
            },

            # Row 2: Daily Usage Tracking
            {
                "type": "metric",
                "x": 0,
                "y": 6,
                "width": 12,
                "height": 6,
                "properties": {
                    "metrics": [
                        ["CCWB/UserQuota", "DailyUsagePercent", "UserEmail", "john.doe@company.com", {"label": "John Doe", "stat": "Maximum"}],
                        ["...", "jane.smith@company.com", {"label": "Jane Smith", "stat": "Maximum"}],
                        ["...", "unknown@company.com", {"label": "Unknown User", "stat": "Maximum"}]
                    ],
                    "view": "timeSeries",
                    "stacked": False,
                    "region": REGION,
                    "title": "Daily Quota Usage % (Last 2 Days)",
                    "period": 3600,
                    "yAxis": {
                        "left": {
                            "label": "Percentage",
                            "min": 0,
                            "max": 100
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
                        ["CCWB/UserQuota", "UserDailyTokens", "UserEmail", "john.doe@company.com", {"label": "John Doe", "stat": "Maximum"}],
                        ["...", "jane.smith@company.com", {"label": "Jane Smith", "stat": "Maximum"}],
                        ["...", "unknown@company.com", {"label": "Unknown User", "stat": "Maximum"}]
                    ],
                    "view": "timeSeries",
                    "stacked": False,
                    "region": REGION,
                    "title": "Daily Token Usage (Last 2 Days)",
                    "period": 3600,
                    "yAxis": {
                        "left": {
                            "label": "Tokens",
                            "showUnits": False
                        }
                    }
                }
            },

            # Row 3: Current Status Gauges
            {
                "type": "metric",
                "x": 0,
                "y": 12,
                "width": 6,
                "height": 6,
                "properties": {
                    "metrics": [
                        ["CCWB/UserQuota", "MonthlyUsagePercent", "UserEmail", "john.doe@company.com", {"label": "John Doe", "stat": "Maximum"}]
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
                        ["CCWB/UserQuota", "MonthlyUsagePercent", "UserEmail", "jane.smith@company.com", {"label": "Jane Smith", "stat": "Maximum"}]
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
                        ["CCWB/UserQuota", "DailyUsagePercent", "UserEmail", "john.doe@company.com", {"label": "John Doe", "stat": "Maximum"}]
                    ],
                    "view": "gauge",
                    "region": REGION,
                    "title": "John Doe - Daily Quota",
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
                        ["CCWB/UserQuota", "DailyUsagePercent", "UserEmail", "jane.smith@company.com", {"label": "Jane Smith", "stat": "Maximum"}]
                    ],
                    "view": "gauge",
                    "region": REGION,
                    "title": "Jane Smith - Daily Quota",
                    "period": 86400,
                    "yAxis": {
                        "left": {
                            "min": 0,
                            "max": 100
                        }
                    }
                }
            },

            # Row 4: User Comparison Table
            {
                "type": "metric",
                "x": 0,
                "y": 18,
                "width": 12,
                "height": 6,
                "properties": {
                    "metrics": [
                        ["CCWB/UserQuota", "UserMonthlyTokens", "UserEmail", "john.doe@company.com", {"stat": "Maximum", "label": "John Doe"}],
                        ["...", "jane.smith@company.com", {"stat": "Maximum", "label": "Jane Smith"}],
                        ["...", "unknown@company.com", {"stat": "Maximum", "label": "Unknown User"}]
                    ],
                    "view": "table",
                    "region": REGION,
                    "title": "Token Usage Ranking (Last 2 Days)",
                    "period": 172800  # 2 days
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
                        ["CCWB/UserQuota", "MonthlyUsagePercent", "UserEmail", "john.doe@company.com", {"stat": "Maximum", "label": "John Doe"}],
                        ["...", "jane.smith@company.com", {"stat": "Maximum", "label": "Jane Smith"}],
                        ["...", "unknown@company.com", {"stat": "Maximum", "label": "Unknown User"}]
                    ],
                    "view": "table",
                    "region": REGION,
                    "title": "Quota Usage % (Last 2 Days)",
                    "period": 172800
                }
            },

            # Row 5: Real-Time Status
            {
                "type": "metric",
                "x": 0,
                "y": 24,
                "width": 8,
                "height": 6,
                "properties": {
                    "metrics": [
                        ["CCWB/UserQuota", "UserMonthlyTokens", "UserEmail", "john.doe@company.com", {"stat": "Maximum", "label": "John Doe (500M limit)"}],
                        ["...", "jane.smith@company.com", {"stat": "Maximum", "label": "Jane Smith (300M limit)"}],
                        ["...", "unknown@company.com", {"stat": "Maximum", "label": "Unknown (225M limit)"}]
                    ],
                    "view": "singleValue",
                    "region": REGION,
                    "title": "Current Monthly Token Usage",
                    "period": 300
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
                        ["CCWB/UserQuota", "UserDailyTokens", "UserEmail", "john.doe@company.com", {"stat": "Maximum", "label": "John Doe (20M limit)"}],
                        ["...", "jane.smith@company.com", {"stat": "Maximum", "label": "Jane Smith (10M limit)"}],
                        ["...", "unknown@company.com", {"stat": "Maximum", "label": "Unknown (8M limit)"}]
                    ],
                    "view": "singleValue",
                    "region": REGION,
                    "title": "Current Daily Token Usage",
                    "period": 300
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
                        [{"expression": "METRICS()", "label": "Total Active Users", "id": "e1"}]
                    ],
                    "view": "singleValue",
                    "region": REGION,
                    "title": "System Status",
                    "period": 300,
                    "stat": "SampleCount"
                }
            }
        ]
    }

    return json.dumps(dashboard_body)

def update_dashboard():
    """Update the CloudWatch dashboard with real-time metrics"""

    client = boto3.client('cloudwatch', region_name=REGION)

    dashboard_body = create_realtime_dashboard()

    try:
        response = client.put_dashboard(
            DashboardName=DASHBOARD_NAME,
            DashboardBody=dashboard_body
        )

        if response['ResponseMetadata']['HTTPStatusCode'] == 200:
            print("✅ Dashboard updated with real-time metrics!")
            return True
    except Exception as e:
        print(f"❌ Error updating dashboard: {str(e)}")
        return False

def display_metrics_summary():
    """Display current metrics summary"""

    cloudwatch = boto3.client('cloudwatch', region_name=REGION)

    print("\n" + "="*70)
    print("📊 REAL-TIME USER METRICS SUMMARY")
    print("="*70)

    users = [
        ("john.doe@company.com", 500, 20, "Engineering"),
        ("jane.smith@company.com", 300, 10, "Sales"),
        ("unknown@company.com", 225, 8, "Default")
    ]

    for user, monthly_limit, daily_limit, group in users:
        print(f"\n👤 {user} ({group})")
        print("-" * 40)

        # Get latest metrics
        try:
            response = cloudwatch.get_metric_statistics(
                Namespace='CCWB/UserQuota',
                MetricName='UserMonthlyTokens',
                Dimensions=[{'Name': 'UserEmail', 'Value': user}],
                StartTime=datetime.utcnow() - timedelta(hours=1),
                EndTime=datetime.utcnow(),
                Period=3600,
                Statistics=['Maximum']
            )

            if response['Datapoints']:
                tokens = response['Datapoints'][0]['Maximum']
                percent = (tokens / (monthly_limit * 1000000)) * 100
                status = "🔴 OVER" if percent > 100 else "🟡 WARNING" if percent > 80 else "🟢 OK"
                print(f"  Monthly: {tokens/1000000:.1f}M / {monthly_limit}M ({percent:.1f}%) {status}")
            else:
                print(f"  Monthly: No recent data")

        except Exception as e:
            print(f"  Error: {str(e)[:50]}")

def main():
    print("\n" + "="*70)
    print("📊 UPDATING DASHBOARD WITH REAL-TIME METRICS")
    print("="*70)

    print("\n🔄 Updating dashboard to show last 2 days of data...")

    if update_dashboard():
        print(f"\n✅ Dashboard successfully updated!")
        print(f"\n🔗 View your real-time dashboard:")
        print(f"https://console.aws.amazon.com/cloudwatch/home?region={REGION}#dashboards:name={DASHBOARD_NAME}")

        # Display current metrics
        display_metrics_summary()

        print("\n📈 Dashboard Features:")
        print("  • Real-time token usage trends (2-day view)")
        print("  • Monthly and daily quota percentages")
        print("  • User comparison and ranking")
        print("  • Visual gauges showing current status")
        print("  • Threshold warnings at 80% and 90%")

        print("\n⏱️ The dashboard auto-refreshes every 5 minutes")
        print("   Click the refresh button for immediate updates")

if __name__ == "__main__":
    main()