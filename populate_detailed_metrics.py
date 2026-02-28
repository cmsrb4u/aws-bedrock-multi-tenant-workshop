#!/usr/bin/env python3
"""
Populate CloudWatch with detailed historical metrics for better dashboard visualization
"""

import boto3
import json
import random
from datetime import datetime, timedelta

REGION = "us-west-2"

def publish_detailed_metrics():
    """Publish detailed metrics with hourly granularity"""

    cloudwatch = boto3.client('cloudwatch', region_name=REGION)

    # User configurations with realistic usage patterns
    users_data = [
        {
            'email': 'john.doe@company.com',
            'monthly_limit': 500000000,  # 500M
            'daily_limit': 20000000,     # 20M
            'base_monthly': 150000000,   # 30% baseline
            'base_daily': 5000000,       # 25% of daily
            'pattern': 'steady'          # Steady usage
        },
        {
            'email': 'jane.smith@company.com',
            'monthly_limit': 300000000,  # 300M
            'daily_limit': 10000000,     # 10M
            'base_monthly': 80000000,    # 26.7% baseline
            'base_daily': 3000000,       # 30% of daily
            'pattern': 'growing'         # Growing usage
        },
        {
            'email': 'unknown@company.com',
            'monthly_limit': 225000000,  # 225M
            'daily_limit': 8000000,      # 8M
            'base_monthly': 45000000,    # 20% baseline
            'base_daily': 1500000,       # 18.75% of daily
            'pattern': 'variable'        # Variable usage
        }
    ]

    now = datetime.utcnow()
    print("📊 Publishing detailed metrics to CloudWatch...")
    print(f"   Time range: {(now - timedelta(days=2)).strftime('%Y-%m-%d %H:%M')} to {now.strftime('%Y-%m-%d %H:%M')}")
    print()

    # Generate metrics for every hour in the last 48 hours
    for hours_ago in range(48, -1, -1):
        timestamp = now - timedelta(hours=hours_ago)
        hour_of_day = timestamp.hour

        for user in users_data:
            # Apply usage patterns
            if user['pattern'] == 'steady':
                # Steady usage with small variations
                variation = 1 + (random.random() - 0.5) * 0.1  # ±5%

            elif user['pattern'] == 'growing':
                # Growing usage over time
                growth_factor = 1 + (48 - hours_ago) * 0.005  # 0.5% growth per hour
                variation = growth_factor * (1 + (random.random() - 0.5) * 0.15)  # ±7.5%

            else:  # variable
                # Variable usage with work hours pattern
                if 9 <= hour_of_day <= 17:  # Business hours
                    variation = 1.2 + (random.random() - 0.5) * 0.3  # Higher during work
                else:
                    variation = 0.8 + (random.random() - 0.5) * 0.2  # Lower after hours

            # Calculate token usage
            monthly_usage = user['base_monthly'] * variation
            daily_usage = user['base_daily'] * variation

            # Ensure values don't exceed limits
            monthly_usage = min(monthly_usage, user['monthly_limit'] * 0.95)  # Cap at 95%
            daily_usage = min(daily_usage, user['daily_limit'] * 0.95)

            # Calculate percentages
            monthly_pct = (monthly_usage / user['monthly_limit']) * 100
            daily_pct = (daily_usage / user['daily_limit']) * 100

            # Prepare metric data
            metric_data = [
                {
                    'MetricName': 'UserMonthlyTokens',
                    'Value': monthly_usage,
                    'Unit': 'Count',
                    'Timestamp': timestamp,
                    'Dimensions': [{'Name': 'UserEmail', 'Value': user['email']}]
                },
                {
                    'MetricName': 'UserDailyTokens',
                    'Value': daily_usage,
                    'Unit': 'Count',
                    'Timestamp': timestamp,
                    'Dimensions': [{'Name': 'UserEmail', 'Value': user['email']}]
                },
                {
                    'MetricName': 'MonthlyUsagePercent',
                    'Value': monthly_pct,
                    'Unit': 'Percent',
                    'Timestamp': timestamp,
                    'Dimensions': [{'Name': 'UserEmail', 'Value': user['email']}]
                },
                {
                    'MetricName': 'DailyUsagePercent',
                    'Value': daily_pct,
                    'Unit': 'Percent',
                    'Timestamp': timestamp,
                    'Dimensions': [{'Name': 'UserEmail', 'Value': user['email']}]
                }
            ]

            try:
                cloudwatch.put_metric_data(
                    Namespace='CCWB/UserQuota',
                    MetricData=metric_data
                )

                # Print progress every 6 hours
                if hours_ago % 6 == 0:
                    print(f"  📈 {user['email']:30} | {timestamp.strftime('%m/%d %H:%M')} | "
                          f"Monthly: {monthly_pct:5.1f}% | Daily: {daily_pct:5.1f}%")

            except Exception as e:
                print(f"  ❌ Error: {str(e)[:50]}")

    print("\n✅ Published 49 data points per metric for each user!")

def verify_detailed_metrics():
    """Verify the detailed metrics are available"""

    cloudwatch = boto3.client('cloudwatch', region_name=REGION)

    print("\n🔍 Verifying detailed metrics...")

    users = ['john.doe@company.com', 'jane.smith@company.com', 'unknown@company.com']

    for user in users:
        try:
            # Check UserMonthlyTokens metric
            response = cloudwatch.get_metric_statistics(
                Namespace='CCWB/UserQuota',
                MetricName='UserMonthlyTokens',
                Dimensions=[{'Name': 'UserEmail', 'Value': user}],
                StartTime=datetime.utcnow() - timedelta(days=2),
                EndTime=datetime.utcnow(),
                Period=3600,  # 1 hour
                Statistics=['Maximum', 'Average']
            )

            data_points = len(response.get('Datapoints', []))

            if data_points > 0:
                avg_value = sum(dp['Average'] for dp in response['Datapoints']) / data_points
                max_value = max(dp['Maximum'] for dp in response['Datapoints'])
                min_value = min(dp['Maximum'] for dp in response['Datapoints'])

                print(f"  ✅ {user:30}")
                print(f"     Data points: {data_points}")
                print(f"     Range: {min_value/1000000:.1f}M - {max_value/1000000:.1f}M tokens")
                print(f"     Average: {avg_value/1000000:.1f}M tokens")
            else:
                print(f"  ⚠️  {user:30} - No data points found")

        except Exception as e:
            print(f"  ❌ {user:30} - Error: {str(e)[:50]}")

def main():
    print("\n" + "="*70)
    print("📊 POPULATING DETAILED CLOUDWATCH METRICS")
    print("="*70)

    # Publish detailed metrics
    publish_detailed_metrics()

    # Verify metrics
    verify_detailed_metrics()

    print("\n" + "="*70)
    print("✅ DETAILED METRICS POPULATION COMPLETE!")
    print("="*70)

    print("\n📊 What's now available:")
    print("  • 49 hourly data points per user (last 48 hours)")
    print("  • Realistic usage patterns:")
    print("    - John Doe: Steady usage around 30%")
    print("    - Jane Smith: Growing usage trend")
    print("    - Unknown: Variable with business hours pattern")

    print("\n🔗 View your dashboard with detailed data:")
    print(f"https://console.aws.amazon.com/cloudwatch/home?region={REGION}#dashboards:name=CCWB-UserLevel-QuotaMonitoring")

    print("\n💡 Dashboard features now visible:")
    print("  • Sparklines showing 48-hour trends")
    print("  • Smooth time series graphs")
    print("  • Accurate gauge readings")
    print("  • Meaningful bar chart comparisons")

if __name__ == "__main__":
    main()