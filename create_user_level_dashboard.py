#!/usr/bin/env python3
"""
Enhanced CloudWatch Dashboard for CCWB with TRUE User-Level Metrics
This version includes the missing components for individual user tracking

Requirements for full user-level monitoring:
1. Full CCWB Deployment with authentication flow
2. Custom Metrics published from CCWB Lambda with UserEmail dimension
3. DynamoDB Integration to read from QuotaPolicies and UserQuotaMetrics tables
"""

import boto3
import json
from datetime import datetime, timedelta
from typing import List, Dict, Any

# Configuration
REGION = "us-west-2"
DASHBOARD_NAME = "CCWB-User-Level-Quota-Monitoring"
TENANT_A_PROFILE = "5gematyf83m0"  # Marketing
TENANT_B_PROFILE = "yku79b5wumnr"  # Sales

# DynamoDB Table Names (from CCWB deployment)
QUOTA_POLICIES_TABLE = "QuotaPolicies"
USER_QUOTA_METRICS_TABLE = "UserQuotaMetrics"

# Custom Metric Namespace for User-Level Metrics
CUSTOM_NAMESPACE = "CCWB/UserQuota"

class UserLevelMetricsPublisher:
    """
    This class would be implemented in the CCWB Lambda function
    to publish user-level metrics to CloudWatch
    """

    def __init__(self):
        self.cloudwatch = boto3.client('cloudwatch', region_name=REGION)
        self.dynamodb = boto3.resource('dynamodb', region_name=REGION)

    def publish_user_metrics(self, user_email: str, input_tokens: int, output_tokens: int, tenant_id: str):
        """
        Publish custom metrics with UserEmail dimension
        This would be called from the CCWB Lambda after each Bedrock invocation
        """

        metrics_data = [
            {
                'MetricName': 'UserInputTokens',
                'Value': input_tokens,
                'Unit': 'Count',
                'Dimensions': [
                    {'Name': 'UserEmail', 'Value': user_email},
                    {'Name': 'TenantId', 'Value': tenant_id}
                ]
            },
            {
                'MetricName': 'UserOutputTokens',
                'Value': output_tokens,
                'Unit': 'Count',
                'Dimensions': [
                    {'Name': 'UserEmail', 'Value': user_email},
                    {'Name': 'TenantId', 'Value': tenant_id}
                ]
            },
            {
                'MetricName': 'UserTotalTokens',
                'Value': input_tokens + output_tokens,
                'Unit': 'Count',
                'Dimensions': [
                    {'Name': 'UserEmail', 'Value': user_email},
                    {'Name': 'TenantId', 'Value': tenant_id}
                ]
            }
        ]

        # Publish to CloudWatch
        self.cloudwatch.put_metric_data(
            Namespace=CUSTOM_NAMESPACE,
            MetricData=metrics_data
        )

    def get_user_quota_from_dynamodb(self, user_email: str) -> Dict[str, Any]:
        """
        Retrieve user quota policy from DynamoDB
        """

        table = self.dynamodb.Table(QUOTA_POLICIES_TABLE)

        try:
            response = table.get_item(Key={'UserEmail': user_email})
            if 'Item' in response:
                return {
                    'daily_limit': response['Item'].get('DailyTokenLimit', 100000),
                    'monthly_limit': response['Item'].get('MonthlyTokenLimit', 3000000),
                    'burst_limit': response['Item'].get('BurstTokenLimit', 10000),
                    'team': response['Item'].get('Team', 'default')
                }
        except Exception as e:
            print(f"Error retrieving quota for {user_email}: {e}")

        return {
            'daily_limit': 100000,
            'monthly_limit': 3000000,
            'burst_limit': 10000,
            'team': 'default'
        }

def create_user_level_widgets(users: List[str]) -> List[Dict[str, Any]]:
    """
    Create dashboard widgets for individual user tracking
    """

    widgets = []
    y_position = 0

    # User-Level Token Usage Time Series
    for i, user in enumerate(users):
        x_position = (i % 3) * 8
        if i > 0 and i % 3 == 0:
            y_position += 6

        widgets.append({
            "type": "metric",
            "x": x_position,
            "y": y_position,
            "width": 8,
            "height": 6,
            "properties": {
                "metrics": [
                    [CUSTOM_NAMESPACE, "UserInputTokens",
                     {"UserEmail": user},
                     {"stat": "Sum", "label": f"{user} - Input"}],
                    [".", "UserOutputTokens",
                     {"UserEmail": user},
                     {"stat": "Sum", "label": f"{user} - Output"}],
                    [".", "UserTotalTokens",
                     {"UserEmail": user},
                     {"stat": "Sum", "label": f"{user} - Total"}]
                ],
                "view": "timeSeries",
                "stacked": False,
                "region": REGION,
                "title": f"Token Usage: {user}",
                "period": 3600,
                "yAxis": {
                    "left": {
                        "label": "Tokens",
                        "showUnits": False
                    }
                }
            }
        })

    return widgets

def create_user_quota_gauges(users: List[str]) -> List[Dict[str, Any]]:
    """
    Create quota usage gauge widgets for each user
    """

    widgets = []
    publisher = UserLevelMetricsPublisher()

    for i, user in enumerate(users):
        # Get user's quota from DynamoDB
        quota_info = publisher.get_user_quota_from_dynamodb(user)
        daily_limit = quota_info['daily_limit']

        x_position = (i % 4) * 6
        y_position = 36 + (i // 4) * 6

        widgets.append({
            "type": "metric",
            "x": x_position,
            "y": y_position,
            "width": 6,
            "height": 6,
            "properties": {
                "metrics": [
                    [{"expression": f"(m1) / {daily_limit} * 100",
                      "label": f"{user.split('@')[0]} Daily %",
                      "id": "e1"}],
                    [CUSTOM_NAMESPACE, "UserTotalTokens",
                     {"UserEmail": user},
                     {"id": "m1", "visible": False, "stat": "Sum", "period": 86400}]
                ],
                "view": "gauge",
                "region": REGION,
                "title": f"{user.split('@')[0]} Daily Quota",
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
        })

    return widgets

def create_user_comparison_table(users: List[str]) -> Dict[str, Any]:
    """
    Create a table widget comparing all users
    """

    metrics = []
    for user in users:
        metrics.extend([
            [CUSTOM_NAMESPACE, "UserInputTokens",
             {"UserEmail": user},
             {"stat": "Sum", "label": f"{user} - Input"}],
            [".", "UserOutputTokens",
             {"UserEmail": user},
             {"stat": "Sum", "label": f"{user} - Output"}],
            [".", "UserTotalTokens",
             {"UserEmail": user},
             {"stat": "Sum", "label": f"{user} - Total"}]
        ])

    return {
        "type": "metric",
        "x": 0,
        "y": 48,
        "width": 24,
        "height": 6,
        "properties": {
            "metrics": metrics,
            "view": "table",
            "region": REGION,
            "title": "User Token Usage Comparison (Last 24 Hours)",
            "period": 86400,
            "stat": "Sum"
        }
    }

def create_user_level_alarms(users: List[str]):
    """
    Create CloudWatch alarms for each user's quota thresholds
    """

    cloudwatch = boto3.client('cloudwatch', region_name=REGION)
    publisher = UserLevelMetricsPublisher()

    for user in users:
        quota_info = publisher.get_user_quota_from_dynamodb(user)
        daily_limit = quota_info['daily_limit']

        # 80% Warning Alarm
        alarm_name = f"User-{user.replace('@', '-').replace('.', '-')}-DailyQuota-Warning"

        try:
            cloudwatch.put_metric_alarm(
                AlarmName=alarm_name,
                ComparisonOperator='GreaterThanThreshold',
                EvaluationPeriods=1,
                MetricName='UserTotalTokens',
                Namespace=CUSTOM_NAMESPACE,
                Period=86400,
                Statistic='Sum',
                Threshold=daily_limit * 0.8,
                ActionsEnabled=True,
                AlarmDescription=f'Alert when {user} exceeds 80% of daily quota',
                Dimensions=[
                    {'Name': 'UserEmail', 'Value': user}
                ]
            )
            print(f"✅ Created alarm: {alarm_name}")
        except Exception as e:
            print(f"⚠️ Could not create alarm {alarm_name}: {e}")

def create_enhanced_dashboard_json(users: List[str]) -> str:
    """
    Generate the enhanced dashboard JSON with user-level metrics
    """

    # Start with base widgets
    dashboard_body = {
        "widgets": [
            # Row 1: Overview with User Breakdown
            {
                "type": "metric",
                "x": 0,
                "y": 0,
                "width": 12,
                "height": 6,
                "properties": {
                    "metrics": [
                        ["AWS/Bedrock", "InputTokenCount", {"stat": "Sum", "label": "Total Input (All Users)"}],
                        [".", "OutputTokenCount", {"stat": "Sum", "label": "Total Output (All Users)"}]
                    ] + [
                        [CUSTOM_NAMESPACE, "UserTotalTokens",
                         {"UserEmail": user},
                         {"stat": "Sum", "label": f"{user.split('@')[0]}"}]
                        for user in users
                    ],
                    "view": "timeSeries",
                    "stacked": True,
                    "region": REGION,
                    "title": "Token Usage by User (Stacked)",
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
                "x": 12,
                "y": 0,
                "width": 12,
                "height": 6,
                "properties": {
                    "metrics": [
                        [CUSTOM_NAMESPACE, "UserTotalTokens",
                         {"UserEmail": user},
                         {"stat": "Sum", "label": user.split('@')[0]}]
                        for user in users
                    ],
                    "view": "pie",
                    "region": REGION,
                    "title": "Token Distribution by User (Today)",
                    "period": 86400,
                    "stat": "Sum"
                }
            },

            # Row 2: User Leaderboard
            {
                "type": "metric",
                "x": 0,
                "y": 6,
                "width": 8,
                "height": 6,
                "properties": {
                    "metrics": [
                        [CUSTOM_NAMESPACE, "UserTotalTokens",
                         {"UserEmail": user},
                         {"stat": "Sum", "label": user}]
                        for user in users
                    ],
                    "view": "barChart",
                    "region": REGION,
                    "title": "Top Users by Token Usage (Today)",
                    "period": 86400,
                    "stat": "Sum"
                }
            },
            {
                "type": "metric",
                "x": 8,
                "y": 6,
                "width": 8,
                "height": 6,
                "properties": {
                    "metrics": [
                        [{"expression": f"RATE(m{i})",
                          "label": f"{user.split('@')[0]} Rate",
                          "id": f"e{i}"}]
                        for i, user in enumerate(users, 1)
                    ] + [
                        [CUSTOM_NAMESPACE, "UserTotalTokens",
                         {"UserEmail": user},
                         {"id": f"m{i}", "visible": False}]
                        for i, user in enumerate(users, 1)
                    ],
                    "view": "timeSeries",
                    "stacked": False,
                    "region": REGION,
                    "title": "Token Rate by User (Tokens/Min)",
                    "period": 300,
                    "stat": "Sum"
                }
            },
            {
                "type": "metric",
                "x": 16,
                "y": 6,
                "width": 8,
                "height": 6,
                "properties": {
                    "metrics": [
                        [{"expression": f"((m{i}) / 1000000) * 3.00 + ((m{i+len(users)}) / 1000000) * 15.00",
                          "label": f"{user.split('@')[0]} Cost",
                          "id": f"e{i}"}]
                        for i, user in enumerate(users, 1)
                    ] + [
                        [CUSTOM_NAMESPACE, "UserInputTokens",
                         {"UserEmail": user},
                         {"id": f"m{i}", "visible": False, "stat": "Sum", "period": 86400}]
                        for i, user in enumerate(users, 1)
                    ] + [
                        [CUSTOM_NAMESPACE, "UserOutputTokens",
                         {"UserEmail": user},
                         {"id": f"m{i+len(users)}", "visible": False, "stat": "Sum", "period": 86400}]
                        for i, user in enumerate(users, 1)
                    ],
                    "view": "singleValue",
                    "region": REGION,
                    "title": "Today's Cost by User",
                    "period": 86400,
                    "stat": "Sum"
                }
            }
        ]
    }

    # Add individual user widgets
    user_widgets = create_user_level_widgets(users)
    for widget in user_widgets:
        widget["y"] += 12  # Offset for existing widgets
    dashboard_body["widgets"].extend(user_widgets)

    # Add user quota gauges
    quota_gauges = create_user_quota_gauges(users)
    dashboard_body["widgets"].extend(quota_gauges)

    # Add comparison table
    comparison_table = create_user_comparison_table(users)
    dashboard_body["widgets"].append(comparison_table)

    # Add team comparison widget
    dashboard_body["widgets"].append({
        "type": "metric",
        "x": 0,
        "y": 54,
        "width": 24,
        "height": 6,
        "properties": {
            "metrics": [
                [CUSTOM_NAMESPACE, "UserTotalTokens",
                 {"TenantId": TENANT_A_PROFILE},
                 {"stat": "Sum", "label": "Marketing Team Total"}],
                ["...",
                 {"TenantId": TENANT_B_PROFILE},
                 {"stat": "Sum", "label": "Sales Team Total"}]
            ],
            "view": "timeSeries",
            "stacked": False,
            "region": REGION,
            "title": "Team Token Usage Comparison",
            "period": 3600,
            "stat": "Sum"
        }
    })

    return json.dumps(dashboard_body)

def setup_lambda_function_for_metrics():
    """
    Sample Lambda function code that would be deployed in CCWB
    to capture and publish user-level metrics
    """

    lambda_code = '''
import json
import boto3
from datetime import datetime

cloudwatch = boto3.client('cloudwatch')
dynamodb = boto3.resource('dynamodb')

def lambda_handler(event, context):
    """
    This Lambda would be triggered by the CCWB API Gateway
    after authenticating the user and before calling Bedrock
    """

    # Extract user info from authenticated request
    user_email = event['requestContext']['authorizer']['claims']['email']
    tenant_id = event['requestContext']['authorizer']['claims']['custom:tenant_id']

    # After Bedrock invocation, get token usage
    bedrock_response = invoke_bedrock(event['body'])
    input_tokens = bedrock_response['usage']['input_tokens']
    output_tokens = bedrock_response['usage']['output_tokens']

    # Publish custom metrics with user dimension
    metric_data = [
        {
            'MetricName': 'UserInputTokens',
            'Value': input_tokens,
            'Unit': 'Count',
            'Timestamp': datetime.utcnow(),
            'Dimensions': [
                {'Name': 'UserEmail', 'Value': user_email},
                {'Name': 'TenantId', 'Value': tenant_id}
            ]
        },
        {
            'MetricName': 'UserOutputTokens',
            'Value': output_tokens,
            'Unit': 'Count',
            'Timestamp': datetime.utcnow(),
            'Dimensions': [
                {'Name': 'UserEmail', 'Value': user_email},
                {'Name': 'TenantId', 'Value': tenant_id}
            ]
        }
    ]

    cloudwatch.put_metric_data(
        Namespace='CCWB/UserQuota',
        MetricData=metric_data
    )

    # Update DynamoDB with usage
    table = dynamodb.Table('UserQuotaMetrics')
    table.update_item(
        Key={'UserEmail': user_email, 'Date': datetime.utcnow().strftime('%Y-%m-%d')},
        UpdateExpression='ADD InputTokens :input, OutputTokens :output',
        ExpressionAttributeValues={
            ':input': input_tokens,
            ':output': output_tokens
        }
    )

    return bedrock_response
'''

    print("\n📝 Lambda Function Code for User-Level Metrics:")
    print("=" * 60)
    print(lambda_code)
    print("=" * 60)

    return lambda_code

def create_dynamodb_tables():
    """
    Create the required DynamoDB tables for user quota tracking
    """

    dynamodb = boto3.client('dynamodb', region_name=REGION)

    tables_config = [
        {
            'TableName': QUOTA_POLICIES_TABLE,
            'KeySchema': [
                {'AttributeName': 'UserEmail', 'KeyType': 'HASH'}
            ],
            'AttributeDefinitions': [
                {'AttributeName': 'UserEmail', 'AttributeType': 'S'}
            ],
            'BillingMode': 'PAY_PER_REQUEST'
        },
        {
            'TableName': USER_QUOTA_METRICS_TABLE,
            'KeySchema': [
                {'AttributeName': 'UserEmail', 'KeyType': 'HASH'},
                {'AttributeName': 'Date', 'KeyType': 'RANGE'}
            ],
            'AttributeDefinitions': [
                {'AttributeName': 'UserEmail', 'AttributeType': 'S'},
                {'AttributeName': 'Date', 'AttributeType': 'S'}
            ],
            'BillingMode': 'PAY_PER_REQUEST'
        }
    ]

    for table_config in tables_config:
        try:
            response = dynamodb.create_table(**table_config)
            print(f"✅ Created DynamoDB table: {table_config['TableName']}")
        except dynamodb.exceptions.ResourceInUseException:
            print(f"⚠️ Table {table_config['TableName']} already exists")
        except Exception as e:
            print(f"❌ Error creating table {table_config['TableName']}: {e}")

def main():
    print("\n" + "="*80)
    print("🎯 ENHANCED CCWB USER-LEVEL QUOTA MONITORING DASHBOARD")
    print("="*80)

    # Define users to track
    users = [
        "john@company.com",
        "alice@marketing.com",
        "bob@sales.com",
        "sarah@engineering.com"
    ]

    print("\n📋 REQUIREMENTS FOR TRUE USER-LEVEL METRICS:")
    print("-" * 60)
    print("✅ 1. Full CCWB Deployment with Authentication")
    print("   • API Gateway with Cognito/OAuth authentication")
    print("   • User email extraction from JWT tokens")
    print("   • Tenant ID mapping for users")

    print("\n✅ 2. Custom Metrics Publisher (Lambda Function)")
    print("   • Intercepts Bedrock API calls")
    print("   • Publishes metrics with UserEmail dimension")
    print("   • Updates DynamoDB with usage data")

    print("\n✅ 3. DynamoDB Tables for Quota Management")
    print("   • QuotaPolicies table - stores per-user limits")
    print("   • UserQuotaMetrics table - tracks daily usage")

    print("\n🔧 SETUP STEPS:")
    print("-" * 60)

    # Step 1: Show Lambda code needed
    print("\n1️⃣ Deploy Lambda Function for Metrics Collection:")
    setup_lambda_function_for_metrics()

    # Step 2: Create DynamoDB tables
    print("\n2️⃣ Creating DynamoDB Tables...")
    create_dynamodb_tables()

    # Step 3: Create CloudWatch alarms
    print("\n3️⃣ Creating User-Level CloudWatch Alarms...")
    create_user_level_alarms(users)

    # Step 4: Create the dashboard
    print("\n4️⃣ Creating Enhanced Dashboard...")

    client = boto3.client('cloudwatch', region_name=REGION)
    dashboard_body = create_enhanced_dashboard_json(users)

    try:
        response = client.put_dashboard(
            DashboardName=DASHBOARD_NAME,
            DashboardBody=dashboard_body
        )

        if response['ResponseMetadata']['HTTPStatusCode'] == 200:
            print(f"✅ Dashboard '{DASHBOARD_NAME}' created successfully!")
            print(f"\n📊 View your dashboard at:")
            print(f"https://console.aws.amazon.com/cloudwatch/home?region={REGION}#dashboards:name={DASHBOARD_NAME}")
        else:
            print(f"❌ Failed to create dashboard: {response}")

    except Exception as e:
        print(f"❌ Error creating dashboard: {str(e)}")

    print("\n📊 ENHANCED DASHBOARD FEATURES:")
    print("-" * 60)
    print("✅ Individual User Token Usage (john@company.com, alice@marketing.com, etc.)")
    print("✅ User-Level Quota Gauges (% of daily limit per user)")
    print("✅ Token Distribution Pie Chart")
    print("✅ User Leaderboard (top consumers)")
    print("✅ Per-User Rate Limiting Metrics")
    print("✅ Cost Attribution by User")
    print("✅ Team Comparison Views")
    print("✅ User Comparison Table")

    print("\n⚠️ CURRENT LIMITATIONS WITHOUT FULL CCWB:")
    print("-" * 60)
    print("• Metrics shown are simulated - need actual Lambda deployment")
    print("• User authentication not enforced - need API Gateway + Cognito")
    print("• DynamoDB tables empty - need actual usage data")
    print("• Custom namespace metrics not being published - need Lambda integration")

    print("\n🚀 TO IMPLEMENT FULLY:")
    print("-" * 60)
    print("1. Deploy full CCWB stack with authentication")
    print("2. Modify CCWB Lambda to publish custom metrics")
    print("3. Configure API Gateway to extract user email from JWT")
    print("4. Set up DynamoDB streams for real-time updates")
    print("5. Create SNS topics for quota alerts")
    print("6. Implement quota enforcement in Lambda")

    print("\n💡 ALTERNATIVE: USE CLOUDWATCH LOGS INSIGHTS")
    print("-" * 60)
    print("If CCWB Lambda logs user email with each request, you can:")
    print("1. Parse CloudWatch Logs with Insights queries")
    print("2. Create metric filters to extract user-level data")
    print("3. Generate metrics from log patterns")
    print("Example query:")
    print("""
    fields @timestamp, userEmail, inputTokens, outputTokens
    | filter @message like /userEmail/
    | stats sum(inputTokens) as totalInput,
           sum(outputTokens) as totalOutput
           by userEmail
    """)

if __name__ == "__main__":
    main()