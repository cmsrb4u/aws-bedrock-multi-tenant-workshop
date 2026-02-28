#!/usr/bin/env python3
"""
Update CloudWatch Dashboard to match official CCWB monitoring layout
Based on AWS Solutions Library guidance
"""

import boto3
import json
from datetime import datetime, timedelta

REGION = "us-west-2"
DASHBOARD_NAME = "CCWB-UserLevel-QuotaMonitoring"

def create_official_dashboard():
    """Create dashboard matching official CCWB monitoring layout"""

    dashboard_body = {
        "start": "-P2D",  # Last 2 days
        "periodOverride": "inherit",
        "widgets": [
            # Row 1: Header Numbers (Current Usage)
            {
                "type": "metric",
                "x": 0,
                "y": 0,
                "width": 6,
                "height": 4,
                "properties": {
                    "metrics": [
                        ["CCWB/UserQuota", "UserMonthlyTokens", "UserEmail", "john.doe@company.com", {"stat": "Maximum", "label": "John Doe"}]
                    ],
                    "view": "singleValue",
                    "region": REGION,
                    "title": "John Doe - Monthly Tokens",
                    "period": 300,
                    "sparkline": True,
                    "setPeriodToTimeRange": True
                }
            },
            {
                "type": "metric",
                "x": 6,
                "y": 0,
                "width": 6,
                "height": 4,
                "properties": {
                    "metrics": [
                        ["CCWB/UserQuota", "UserMonthlyTokens", "UserEmail", "jane.smith@company.com", {"stat": "Maximum", "label": "Jane Smith"}]
                    ],
                    "view": "singleValue",
                    "region": REGION,
                    "title": "Jane Smith - Monthly Tokens",
                    "period": 300,
                    "sparkline": True,
                    "setPeriodToTimeRange": True
                }
            },
            {
                "type": "metric",
                "x": 12,
                "y": 0,
                "width": 6,
                "height": 4,
                "properties": {
                    "metrics": [
                        ["CCWB/UserQuota", "UserMonthlyTokens", "UserEmail", "unknown@company.com", {"stat": "Maximum", "label": "Unknown User"}]
                    ],
                    "view": "singleValue",
                    "region": REGION,
                    "title": "Unknown User - Monthly Tokens",
                    "period": 300,
                    "sparkline": True,
                    "setPeriodToTimeRange": True
                }
            },
            {
                "type": "metric",
                "x": 18,
                "y": 0,
                "width": 6,
                "height": 4,
                "properties": {
                    "metrics": [
                        [{"expression": "SUM(METRICS())", "label": "Total Tokens", "id": "total"}],
                        ["CCWB/UserQuota", "UserMonthlyTokens", "UserEmail", "john.doe@company.com", {"stat": "Maximum", "visible": False, "id": "m1"}],
                        ["...", "jane.smith@company.com", {"stat": "Maximum", "visible": False, "id": "m2"}],
                        ["...", "unknown@company.com", {"stat": "Maximum", "visible": False, "id": "m3"}]
                    ],
                    "view": "singleValue",
                    "region": REGION,
                    "title": "Total Monthly Tokens (All Users)",
                    "period": 300,
                    "sparkline": True,
                    "setPeriodToTimeRange": True
                }
            },

            # Row 2: Usage Percentage Gauges
            {
                "type": "metric",
                "x": 0,
                "y": 4,
                "width": 6,
                "height": 6,
                "properties": {
                    "metrics": [
                        ["CCWB/UserQuota", "MonthlyUsagePercent", "UserEmail", "john.doe@company.com", {"stat": "Maximum"}]
                    ],
                    "view": "gauge",
                    "region": REGION,
                    "title": "John Doe - Monthly Quota %",
                    "period": 300,
                    "yAxis": {
                        "left": {
                            "min": 0,
                            "max": 100
                        }
                    },
                    "annotations": {
                        "horizontal": [
                            {"value": 80, "label": "Warning", "color": "#ff9900"},
                            {"value": 95, "label": "Critical", "color": "#d13212"}
                        ]
                    },
                    "setPeriodToTimeRange": True
                }
            },
            {
                "type": "metric",
                "x": 6,
                "y": 4,
                "width": 6,
                "height": 6,
                "properties": {
                    "metrics": [
                        ["CCWB/UserQuota", "MonthlyUsagePercent", "UserEmail", "jane.smith@company.com", {"stat": "Maximum"}]
                    ],
                    "view": "gauge",
                    "region": REGION,
                    "title": "Jane Smith - Monthly Quota %",
                    "period": 300,
                    "yAxis": {
                        "left": {
                            "min": 0,
                            "max": 100
                        }
                    },
                    "annotations": {
                        "horizontal": [
                            {"value": 80, "label": "Warning", "color": "#ff9900"},
                            {"value": 95, "label": "Critical", "color": "#d13212"}
                        ]
                    },
                    "setPeriodToTimeRange": True
                }
            },
            {
                "type": "metric",
                "x": 12,
                "y": 4,
                "width": 6,
                "height": 6,
                "properties": {
                    "metrics": [
                        ["CCWB/UserQuota", "MonthlyUsagePercent", "UserEmail", "unknown@company.com", {"stat": "Maximum"}]
                    ],
                    "view": "gauge",
                    "region": REGION,
                    "title": "Unknown User - Monthly Quota %",
                    "period": 300,
                    "yAxis": {
                        "left": {
                            "min": 0,
                            "max": 100
                        }
                    },
                    "annotations": {
                        "horizontal": [
                            {"value": 80, "label": "Warning", "color": "#ff9900"},
                            {"value": 95, "label": "Critical", "color": "#d13212"}
                        ]
                    },
                    "setPeriodToTimeRange": True
                }
            },
            {
                "type": "metric",
                "x": 18,
                "y": 4,
                "width": 6,
                "height": 6,
                "properties": {
                    "metrics": [
                        ["CCWB/UserQuota", "DailyUsagePercent", "UserEmail", "john.doe@company.com", {"stat": "Maximum", "label": "John Doe"}],
                        ["...", "jane.smith@company.com", {"stat": "Maximum", "label": "Jane Smith"}],
                        ["...", "unknown@company.com", {"stat": "Maximum", "label": "Unknown"}]
                    ],
                    "view": "bar",
                    "region": REGION,
                    "title": "Daily Quota Usage % (Current)",
                    "period": 300,
                    "yAxis": {
                        "left": {
                            "min": 0,
                            "max": 100
                        }
                    },
                    "setPeriodToTimeRange": True,
                    "stat": "Maximum"
                }
            },

            # Row 3: Time Series - Token Usage Trends
            {
                "type": "metric",
                "x": 0,
                "y": 10,
                "width": 12,
                "height": 6,
                "properties": {
                    "metrics": [
                        ["CCWB/UserQuota", "UserMonthlyTokens", "UserEmail", "john.doe@company.com", {"label": "John Doe"}],
                        ["...", "jane.smith@company.com", {"label": "Jane Smith"}],
                        ["...", "unknown@company.com", {"label": "Unknown User"}]
                    ],
                    "view": "timeSeries",
                    "stacked": False,
                    "region": REGION,
                    "title": "Monthly Token Usage Trend",
                    "period": 3600,
                    "yAxis": {
                        "left": {
                            "label": "Tokens",
                            "showUnits": False
                        }
                    },
                    "stat": "Maximum",
                    "setPeriodToTimeRange": True,
                    "annotations": {
                        "horizontal": [
                            {
                                "label": "John Doe Limit (500M)",
                                "value": 500000000,
                                "color": "#2ca02c"
                            },
                            {
                                "label": "Jane Smith Limit (300M)",
                                "value": 300000000,
                                "color": "#ff7f0e"
                            },
                            {
                                "label": "Unknown Limit (225M)",
                                "value": 225000000,
                                "color": "#d62728"
                            }
                        ]
                    }
                }
            },
            {
                "type": "metric",
                "x": 12,
                "y": 10,
                "width": 12,
                "height": 6,
                "properties": {
                    "metrics": [
                        ["CCWB/UserQuota", "MonthlyUsagePercent", "UserEmail", "john.doe@company.com", {"label": "John Doe"}],
                        ["...", "jane.smith@company.com", {"label": "Jane Smith"}],
                        ["...", "unknown@company.com", {"label": "Unknown User"}]
                    ],
                    "view": "timeSeries",
                    "stacked": False,
                    "region": REGION,
                    "title": "Monthly Quota Usage % Trend",
                    "period": 3600,
                    "yAxis": {
                        "left": {
                            "label": "Percentage",
                            "min": 0,
                            "max": 100
                        }
                    },
                    "stat": "Maximum",
                    "setPeriodToTimeRange": True,
                    "annotations": {
                        "horizontal": [
                            {
                                "label": "Warning Threshold",
                                "value": 80,
                                "color": "#ff9900"
                            },
                            {
                                "label": "Critical Threshold",
                                "value": 95,
                                "color": "#d13212"
                            }
                        ]
                    }
                }
            },

            # Row 4: Daily Usage Tracking
            {
                "type": "metric",
                "x": 0,
                "y": 16,
                "width": 12,
                "height": 6,
                "properties": {
                    "metrics": [
                        ["CCWB/UserQuota", "UserDailyTokens", "UserEmail", "john.doe@company.com", {"label": "John Doe"}],
                        ["...", "jane.smith@company.com", {"label": "Jane Smith"}],
                        ["...", "unknown@company.com", {"label": "Unknown User"}]
                    ],
                    "view": "timeSeries",
                    "stacked": False,
                    "region": REGION,
                    "title": "Daily Token Usage Trend",
                    "period": 3600,
                    "yAxis": {
                        "left": {
                            "label": "Tokens",
                            "showUnits": False
                        }
                    },
                    "stat": "Maximum",
                    "setPeriodToTimeRange": True,
                    "annotations": {
                        "horizontal": [
                            {
                                "label": "John Doe Daily Limit (20M)",
                                "value": 20000000,
                                "color": "#2ca02c"
                            },
                            {
                                "label": "Jane Smith Daily Limit (10M)",
                                "value": 10000000,
                                "color": "#ff7f0e"
                            },
                            {
                                "label": "Unknown Daily Limit (8M)",
                                "value": 8000000,
                                "color": "#d62728"
                            }
                        ]
                    }
                }
            },
            {
                "type": "metric",
                "x": 12,
                "y": 16,
                "width": 12,
                "height": 6,
                "properties": {
                    "metrics": [
                        ["CCWB/UserQuota", "DailyUsagePercent", "UserEmail", "john.doe@company.com", {"label": "John Doe"}],
                        ["...", "jane.smith@company.com", {"label": "Jane Smith"}],
                        ["...", "unknown@company.com", {"label": "Unknown User"}]
                    ],
                    "view": "timeSeries",
                    "stacked": False,
                    "region": REGION,
                    "title": "Daily Quota Usage % Trend",
                    "period": 3600,
                    "yAxis": {
                        "left": {
                            "label": "Percentage",
                            "min": 0,
                            "max": 100
                        }
                    },
                    "stat": "Maximum",
                    "setPeriodToTimeRange": True,
                    "annotations": {
                        "horizontal": [
                            {
                                "label": "Warning",
                                "value": 80,
                                "color": "#ff9900"
                            },
                            {
                                "label": "Critical",
                                "value": 95,
                                "color": "#d13212"
                            }
                        ]
                    }
                }
            },

            # Row 5: User Comparison and Statistics
            {
                "type": "metric",
                "x": 0,
                "y": 22,
                "width": 12,
                "height": 6,
                "properties": {
                    "metrics": [
                        ["CCWB/UserQuota", "UserMonthlyTokens", "UserEmail", "john.doe@company.com", {"stat": "Maximum", "label": "John Doe (Limit: 500M)"}],
                        ["...", "jane.smith@company.com", {"stat": "Maximum", "label": "Jane Smith (Limit: 300M)"}],
                        ["...", "unknown@company.com", {"stat": "Maximum", "label": "Unknown (Limit: 225M)"}]
                    ],
                    "view": "bar",
                    "region": REGION,
                    "title": "Current Monthly Token Usage by User",
                    "period": 86400,
                    "yAxis": {
                        "left": {
                            "label": "Tokens",
                            "showUnits": False
                        }
                    },
                    "setPeriodToTimeRange": True,
                    "stat": "Maximum"
                }
            },
            {
                "type": "metric",
                "x": 12,
                "y": 22,
                "width": 12,
                "height": 6,
                "properties": {
                    "metrics": [
                        ["CCWB/UserQuota", "MonthlyUsagePercent", "UserEmail", "john.doe@company.com", {"stat": "Maximum", "label": "John Doe"}],
                        ["...", "jane.smith@company.com", {"stat": "Maximum", "label": "Jane Smith"}],
                        ["...", "unknown@company.com", {"stat": "Maximum", "label": "Unknown"}],
                        ["...", {"stat": "Average", "label": "Average All Users", "color": "#9467bd"}]
                    ],
                    "view": "bar",
                    "region": REGION,
                    "title": "Monthly Quota Usage % by User",
                    "period": 86400,
                    "yAxis": {
                        "left": {
                            "label": "Percentage",
                            "min": 0,
                            "max": 100
                        }
                    },
                    "setPeriodToTimeRange": True,
                    "annotations": {
                        "horizontal": [
                            {
                                "label": "Warning",
                                "value": 80,
                                "color": "#ff9900",
                                "fill": "above"
                            }
                        ]
                    }
                }
            },

            # Row 6: Statistics Table
            {
                "type": "metric",
                "x": 0,
                "y": 28,
                "width": 24,
                "height": 4,
                "properties": {
                    "metrics": [
                        ["CCWB/UserQuota", "UserMonthlyTokens", "UserEmail", "john.doe@company.com", {"stat": "Maximum", "label": "John Doe - Tokens"}],
                        [".", "MonthlyUsagePercent", ".", ".", {"stat": "Maximum", "label": "John Doe - Usage %"}],
                        [".", "UserMonthlyTokens", ".", "jane.smith@company.com", {"stat": "Maximum", "label": "Jane Smith - Tokens"}],
                        [".", "MonthlyUsagePercent", ".", ".", {"stat": "Maximum", "label": "Jane Smith - Usage %"}],
                        [".", "UserMonthlyTokens", ".", "unknown@company.com", {"stat": "Maximum", "label": "Unknown - Tokens"}],
                        [".", "MonthlyUsagePercent", ".", ".", {"stat": "Maximum", "label": "Unknown - Usage %"}]
                    ],
                    "view": "table",
                    "region": REGION,
                    "title": "User Quota Summary Table",
                    "period": 86400,
                    "setPeriodToTimeRange": True
                }
            }
        ]
    }

    return json.dumps(dashboard_body)

def update_dashboard():
    """Update the CloudWatch dashboard"""

    client = boto3.client('cloudwatch', region_name=REGION)

    dashboard_body = create_official_dashboard()

    try:
        response = client.put_dashboard(
            DashboardName=DASHBOARD_NAME,
            DashboardBody=dashboard_body
        )

        if response['ResponseMetadata']['HTTPStatusCode'] == 200:
            print("✅ Dashboard updated with official CCWB layout!")
            return True
    except Exception as e:
        print(f"❌ Error updating dashboard: {str(e)}")
        return False

def main():
    print("\n" + "="*70)
    print("📊 UPDATING DASHBOARD TO OFFICIAL CCWB LAYOUT")
    print("="*70)

    if update_dashboard():
        print(f"\n✅ Dashboard successfully updated!")
        print(f"\n🔗 View your updated dashboard:")
        print(f"https://console.aws.amazon.com/cloudwatch/home?region={REGION}#dashboards:name={DASHBOARD_NAME}")

        print("\n📋 Dashboard now includes:")
        print("  Row 1: Single Value widgets with sparklines (4 widgets)")
        print("  Row 2: Gauge widgets for quota % + Daily usage bar chart")
        print("  Row 3: Time series for monthly token & percentage trends")
        print("  Row 4: Time series for daily token & percentage trends")
        print("  Row 5: Bar charts comparing users")
        print("  Row 6: Summary table with all user statistics")

        print("\n🎯 Features:")
        print("  • Sparklines on number widgets for quick trend visualization")
        print("  • Warning (80%) and Critical (95%) thresholds")
        print("  • User quota limits shown as annotations")
        print("  • Average usage calculations across users")
        print("  • 2-day default time range with auto-refresh")

if __name__ == "__main__":
    main()