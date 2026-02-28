#!/usr/bin/env python3
"""
Populate CloudWatch with historical metrics by invoking Lambda function
"""

import boto3
import json
import time
from datetime import datetime, timedelta

REGION = "us-west-2"

def invoke_lambda_for_users():
    """Invoke Lambda function for each user to generate metrics"""

    lambda_client = boto3.client('lambda', region_name=REGION)

    users = [
        ('john.doe@company.com', ['engineering']),
        ('jane.smith@company.com', ['sales']),
        ('unknown@company.com', [])
    ]

    print("🔄 Invoking Lambda to publish metrics to CloudWatch...")

    for user_email, groups in users:
        payload = {
            'user_email': user_email,
            'groups': groups
        }

        try:
            response = lambda_client.invoke(
                FunctionName='CCWB-QuotaCheck',
                InvocationType='RequestResponse',
                Payload=json.dumps(payload)
            )

            result = json.loads(response['Payload'].read())
            if result.get('statusCode') == 200:
                body = json.loads(result.get('body', '{}'))
                usage_pct = (body['usage']['monthly'] / body['limits']['monthly'] * 100) if body['limits']['monthly'] > 0 else 0
                print(f"  ✅ {user_email:30} - {usage_pct:.1f}% of quota")
            else:
                print(f"  ⚠️  {user_email:30} - Status: {result.get('statusCode')}")

        except Exception as e:
            print(f"  ❌ {user_email:30} - Error: {str(e)[:50]}")

def publish_direct_metrics():
    """Directly publish metrics to CloudWatch with historical data"""

    cloudwatch = boto3.client('cloudwatch', region_name=REGION)

    # User data with varying usage patterns
    users_data = [
        {
            'email': 'john.doe@company.com',
            'monthly_limit': 500000000,
            'daily_limit': 20000000,
            'base_monthly': 150000000,  # 30% of limit
            'base_daily': 5000000
        },
        {
            'email': 'jane.smith@company.com',
            'monthly_limit': 300000000,
            'daily_limit': 10000000,
            'base_monthly': 80000000,   # 26.7% of limit
            'base_daily': 3000000
        },
        {
            'email': 'unknown@company.com',
            'monthly_limit': 225000000,
            'daily_limit': 8000000,
            'base_monthly': 45000000,   # 20% of limit
            'base_daily': 1500000
        }
    ]

    # Generate metrics for last 48 hours
    now = datetime.utcnow()

    print("\n📊 Publishing historical metrics to CloudWatch...")

    for hours_ago in range(48, -1, -2):  # Every 2 hours for last 48 hours
        timestamp = now - timedelta(hours=hours_ago)

        for user in users_data:
            # Add some variation to make it realistic
            import random
            variation = 1 + (random.random() - 0.5) * 0.2  # +/- 10% variation

            monthly_usage = user['base_monthly'] * variation
            daily_usage = user['base_daily'] * variation

            # Calculate percentages
            monthly_pct = (monthly_usage / user['monthly_limit']) * 100
            daily_pct = (daily_usage / user['daily_limit']) * 100

            metric_data = [
                {
                    'MetricName': 'UserMonthlyTokens',
                    'Value': monthly_usage,
                    'Unit': 'Count',
                    'Timestamp': timestamp,
                    'Dimensions': [
                        {'Name': 'UserEmail', 'Value': user['email']}
                    ]
                },
                {
                    'MetricName': 'UserDailyTokens',
                    'Value': daily_usage,
                    'Unit': 'Count',
                    'Timestamp': timestamp,
                    'Dimensions': [
                        {'Name': 'UserEmail', 'Value': user['email']}
                    ]
                },
                {
                    'MetricName': 'MonthlyUsagePercent',
                    'Value': monthly_pct,
                    'Unit': 'Percent',
                    'Timestamp': timestamp,
                    'Dimensions': [
                        {'Name': 'UserEmail', 'Value': user['email']}
                    ]
                },
                {
                    'MetricName': 'DailyUsagePercent',
                    'Value': daily_pct,
                    'Unit': 'Percent',
                    'Timestamp': timestamp,
                    'Dimensions': [
                        {'Name': 'UserEmail', 'Value': user['email']}
                    ]
                }
            ]

            try:
                cloudwatch.put_metric_data(
                    Namespace='CCWB/UserQuota',
                    MetricData=metric_data
                )

                if hours_ago % 12 == 0:  # Print progress every 12 hours
                    print(f"  📈 {user['email']:30} - {48-hours_ago:2d}h ago: {monthly_pct:.1f}%")

            except Exception as e:
                print(f"  ❌ Error publishing metrics: {str(e)[:50]}")

    print("\n✅ Published metrics for last 48 hours!")

def verify_metrics():
    """Verify metrics are available in CloudWatch"""

    cloudwatch = boto3.client('cloudwatch', region_name=REGION)

    print("\n🔍 Verifying metrics in CloudWatch...")

    users = ['john.doe@company.com', 'jane.smith@company.com', 'unknown@company.com']

    for user in users:
        try:
            response = cloudwatch.get_metric_statistics(
                Namespace='CCWB/UserQuota',
                MetricName='UserMonthlyTokens',
                Dimensions=[{'Name': 'UserEmail', 'Value': user}],
                StartTime=datetime.utcnow() - timedelta(days=2),
                EndTime=datetime.utcnow(),
                Period=3600,
                Statistics=['Maximum']
            )

            data_points = len(response.get('Datapoints', []))
            if data_points > 0:
                latest = max(response['Datapoints'], key=lambda x: x['Timestamp'])
                print(f"  ✅ {user:30} - {data_points} data points, Latest: {latest['Maximum']/1000000:.1f}M")
            else:
                print(f"  ⚠️  {user:30} - No data points")

        except Exception as e:
            print(f"  ❌ {user:30} - Error: {str(e)[:50]}")

def main():
    print("\n" + "="*70)
    print("📊 POPULATING CLOUDWATCH METRICS")
    print("="*70)

    # First invoke Lambda to ensure current metrics
    invoke_lambda_for_users()

    # Then publish historical data
    publish_direct_metrics()

    # Verify metrics are available
    verify_metrics()

    print("\n" + "="*70)
    print("✅ METRICS POPULATION COMPLETE!")
    print("="*70)

    print("\n🔗 View your dashboard with data:")
    print(f"https://console.aws.amazon.com/cloudwatch/home?region={REGION}#dashboards:name=CCWB-UserLevel-QuotaMonitoring")

    print("\n📝 The dashboard should now show:")
    print("  • 48 hours of historical data")
    print("  • Token usage trends for all users")
    print("  • Monthly and daily usage percentages")
    print("  • Real-time gauges with current status")

if __name__ == "__main__":
    main()