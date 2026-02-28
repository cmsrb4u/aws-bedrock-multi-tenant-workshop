#!/usr/bin/env python3
"""
Complete CCWB setup using existing DynamoDB tables
Seeds policies and creates Lambda functions for user-level tracking
"""

import boto3
import json
import zipfile
import io
from datetime import datetime

REGION = "us-west-2"

def seed_quota_policies():
    """Seed quota policies into existing DynamoDB table"""

    print("\n📝 Seeding Quota Policies...")

    dynamodb = boto3.resource('dynamodb', region_name=REGION)
    table = dynamodb.Table('QuotaPolicies')

    policies = [
        {
            'policy_type': 'default',
            'identifier': 'default',
            'monthly_token_limit': 225000000,  # 225M
            'daily_token_limit': 8000000,      # 8M
            'enforcement_mode': 'alert',
            'enabled': True,
            'created_at': datetime.now().isoformat()
        },
        {
            'policy_type': 'group',
            'identifier': 'engineering',
            'monthly_token_limit': 400000000,  # 400M
            'daily_token_limit': 15000000,     # 15M
            'enforcement_mode': 'alert',
            'enabled': True,
            'created_at': datetime.now().isoformat()
        },
        {
            'policy_type': 'group',
            'identifier': 'sales',
            'monthly_token_limit': 300000000,  # 300M
            'daily_token_limit': 10000000,     # 10M
            'enforcement_mode': 'block',
            'enabled': True,
            'created_at': datetime.now().isoformat()
        },
        {
            'policy_type': 'group',
            'identifier': 'marketing',
            'monthly_token_limit': 250000000,  # 250M
            'daily_token_limit': 8000000,      # 8M
            'enforcement_mode': 'alert',
            'enabled': True,
            'created_at': datetime.now().isoformat()
        },
        {
            'policy_type': 'group',
            'identifier': 'executive',
            'monthly_token_limit': 1000000000, # 1B
            'daily_token_limit': 50000000,     # 50M
            'enforcement_mode': 'alert',
            'enabled': True,
            'created_at': datetime.now().isoformat()
        },
        # User-specific policies
        {
            'policy_type': 'user',
            'identifier': 'john.doe@company.com',
            'monthly_token_limit': 500000000,  # 500M
            'daily_token_limit': 20000000,     # 20M
            'enforcement_mode': 'alert',
            'enabled': True,
            'created_at': datetime.now().isoformat()
        }
    ]

    for policy in policies:
        try:
            table.put_item(Item=policy)
            print(f"  ✅ {policy['policy_type']:8} | {policy['identifier']:20} | {policy['monthly_token_limit']/1000000:.0f}M monthly")
        except Exception as e:
            print(f"  ⚠️ Error with {policy['identifier']}: {str(e)[:50]}")

    print("\n✅ Quota policies seeded successfully!")

def create_lambda_functions():
    """Create Lambda functions for quota checking and metrics recording"""

    print("\n🔧 Creating Lambda Functions...")

    lambda_client = boto3.client('lambda', region_name=REGION)
    iam_client = boto3.client('iam')

    # Create IAM role for Lambda
    trust_policy = {
        "Version": "2012-10-17",
        "Statement": [{
            "Effect": "Allow",
            "Principal": {"Service": "lambda.amazonaws.com"},
            "Action": "sts:AssumeRole"
        }]
    }

    try:
        # Create or update role
        role_name = "CCWB-QuotaLambdaRole"
        try:
            iam_client.create_role(
                RoleName=role_name,
                AssumeRolePolicyDocument=json.dumps(trust_policy),
                Description="Role for CCWB quota Lambda functions"
            )
            print(f"  ✅ Created IAM role: {role_name}")
        except iam_client.exceptions.EntityAlreadyExistsException:
            print(f"  ⚠️ IAM role already exists: {role_name}")

        # Attach policies
        iam_client.attach_role_policy(
            RoleName=role_name,
            PolicyArn='arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole'
        )

        # Create inline policy for DynamoDB access
        dynamodb_policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Action": [
                        "dynamodb:GetItem",
                        "dynamodb:PutItem",
                        "dynamodb:UpdateItem",
                        "dynamodb:Query"
                    ],
                    "Resource": [
                        f"arn:aws:dynamodb:{REGION}:899950533801:table/QuotaPolicies",
                        f"arn:aws:dynamodb:{REGION}:899950533801:table/UserQuotaMetrics"
                    ]
                },
                {
                    "Effect": "Allow",
                    "Action": "cloudwatch:PutMetricData",
                    "Resource": "*"
                }
            ]
        }

        iam_client.put_role_policy(
            RoleName=role_name,
            PolicyName='DynamoDBAndCloudWatchAccess',
            PolicyDocument=json.dumps(dynamodb_policy)
        )

        # Wait for role to be available
        import time
        time.sleep(10)

        role_arn = f"arn:aws:iam::899950533801:role/{role_name}"

        # Lambda function code for quota checking
        quota_check_code = '''
import json
import boto3
import os
from datetime import datetime
from decimal import Decimal

dynamodb = boto3.resource('dynamodb')
cloudwatch = boto3.client('cloudwatch')

def lambda_handler(event, context):
    # Extract user from event
    user_email = event.get('user_email', 'test@company.com')
    groups = event.get('groups', ['engineering'])

    # Get effective quota policy
    policy = get_effective_policy(user_email, groups)

    # Get current usage
    usage = get_current_usage(user_email)

    # Check quota
    monthly_exceeded = usage['monthly'] > policy.get('monthly_token_limit', float('inf'))
    daily_exceeded = usage['daily'] > policy.get('daily_token_limit', float('inf'))

    # Publish metrics
    publish_metrics(user_email, usage, policy)

    # Prepare response
    response = {
        'allowed': not ((monthly_exceeded or daily_exceeded) and policy.get('enforcement_mode') == 'block'),
        'usage': usage,
        'limits': {
            'monthly': policy.get('monthly_token_limit'),
            'daily': policy.get('daily_token_limit')
        },
        'enforcement_mode': policy.get('enforcement_mode')
    }

    return {
        'statusCode': 200 if response['allowed'] else 429,
        'body': json.dumps(response)
    }

def get_effective_policy(user_email, groups):
    policies_table = dynamodb.Table('QuotaPolicies')

    # Check user-specific policy
    response = policies_table.get_item(
        Key={'policy_type': 'user', 'identifier': user_email}
    )
    if 'Item' in response and response['Item'].get('enabled'):
        return response['Item']

    # Check group policies
    for group in groups:
        response = policies_table.get_item(
            Key={'policy_type': 'group', 'identifier': group}
        )
        if 'Item' in response and response['Item'].get('enabled'):
            return response['Item']

    # Return default policy
    response = policies_table.get_item(
        Key={'policy_type': 'default', 'identifier': 'default'}
    )
    return response.get('Item', {
        'monthly_token_limit': 225000000,
        'daily_token_limit': 8000000,
        'enforcement_mode': 'alert'
    })

def get_current_usage(user_email):
    metrics_table = dynamodb.Table('UserQuotaMetrics')

    now = datetime.now()
    month_key = now.strftime('%Y-%m')
    day_key = now.strftime('%Y-%m-%d')

    # Get monthly usage
    monthly_response = metrics_table.get_item(
        Key={'user_email': user_email, 'metric_period': f'monthly_{month_key}'}
    )
    monthly_usage = int(monthly_response.get('Item', {}).get('tokens_used', 0))

    # Get daily usage
    daily_response = metrics_table.get_item(
        Key={'user_email': user_email, 'metric_period': f'daily_{day_key}'}
    )
    daily_usage = int(daily_response.get('Item', {}).get('tokens_used', 0))

    return {'monthly': monthly_usage, 'daily': daily_usage}

def publish_metrics(user_email, usage, policy):
    # Publish custom CloudWatch metrics
    try:
        monthly_limit = policy.get('monthly_token_limit', 1)
        daily_limit = policy.get('daily_token_limit', 1)

        cloudwatch.put_metric_data(
            Namespace='CCWB/UserQuota',
            MetricData=[
                {
                    'MetricName': 'MonthlyUsagePercent',
                    'Value': (usage['monthly'] / monthly_limit) * 100 if monthly_limit > 0 else 0,
                    'Unit': 'Percent',
                    'Dimensions': [{'Name': 'UserEmail', 'Value': user_email}]
                },
                {
                    'MetricName': 'DailyUsagePercent',
                    'Value': (usage['daily'] / daily_limit) * 100 if daily_limit > 0 else 0,
                    'Unit': 'Percent',
                    'Dimensions': [{'Name': 'UserEmail', 'Value': user_email}]
                }
            ]
        )
    except Exception as e:
        print(f"Error publishing metrics: {str(e)}")
'''

        # Create quota check function
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            zip_file.writestr('lambda_function.py', quota_check_code)

        try:
            lambda_client.create_function(
                FunctionName='CCWB-QuotaCheck',
                Runtime='python3.12',
                Role=role_arn,
                Handler='lambda_function.lambda_handler',
                Code={'ZipFile': zip_buffer.getvalue()},
                Description='CCWB Quota Check Function',
                Timeout=30,
                MemorySize=256
            )
            print("  ✅ Created CCWB-QuotaCheck function")
        except lambda_client.exceptions.ResourceConflictException:
            # Update existing function
            lambda_client.update_function_code(
                FunctionName='CCWB-QuotaCheck',
                ZipFile=zip_buffer.getvalue()
            )
            print("  ✅ Updated CCWB-QuotaCheck function")

    except Exception as e:
        print(f"  ❌ Error creating Lambda functions: {str(e)}")

def simulate_user_metrics():
    """Simulate some user metrics for testing"""

    print("\n📊 Simulating User Metrics...")

    dynamodb = boto3.resource('dynamodb', region_name=REGION)
    table = dynamodb.Table('UserQuotaMetrics')

    now = datetime.now()
    month_key = now.strftime('%Y-%m')
    day_key = now.strftime('%Y-%m-%d')

    test_users = [
        ('john.doe@company.com', 150000000, 5000000),    # 150M monthly, 5M daily
        ('jane.smith@company.com', 80000000, 3000000),   # 80M monthly, 3M daily
        ('bob.marketing@company.com', 50000000, 2000000), # 50M monthly, 2M daily
        ('alice.exec@company.com', 200000000, 10000000)  # 200M monthly, 10M daily
    ]

    for user_email, monthly_tokens, daily_tokens in test_users:
        # Add monthly usage
        table.put_item(Item={
            'user_email': user_email,
            'metric_period': f'monthly_{month_key}',
            'tokens_used': monthly_tokens,
            'last_updated': now.isoformat(),
            'ttl': int((now.timestamp() + 7776000))  # 90 days
        })

        # Add daily usage
        table.put_item(Item={
            'user_email': user_email,
            'metric_period': f'daily_{day_key}',
            'tokens_used': daily_tokens,
            'last_updated': now.isoformat(),
            'ttl': int((now.timestamp() + 604800))  # 7 days
        })

        print(f"  ✅ {user_email:30} | Monthly: {monthly_tokens/1000000:.0f}M | Daily: {daily_tokens/1000000:.0f}M")

def test_quota_check():
    """Test the quota check function"""

    print("\n🧪 Testing Quota Check Function...")

    lambda_client = boto3.client('lambda', region_name=REGION)

    test_cases = [
        {
            'user_email': 'john.doe@company.com',
            'groups': ['engineering']
        },
        {
            'user_email': 'jane.smith@company.com',
            'groups': ['sales']
        },
        {
            'user_email': 'unknown@company.com',
            'groups': []
        }
    ]

    for test in test_cases:
        try:
            response = lambda_client.invoke(
                FunctionName='CCWB-QuotaCheck',
                InvocationType='RequestResponse',
                Payload=json.dumps(test)
            )

            result = json.loads(response['Payload'].read())
            body = json.loads(result.get('body', '{}'))

            status = "✅ ALLOWED" if body.get('allowed') else "❌ BLOCKED"
            monthly_usage = body.get('usage', {}).get('monthly', 0)
            monthly_limit = body.get('limits', {}).get('monthly', 0)
            percent = (monthly_usage / monthly_limit * 100) if monthly_limit > 0 else 0

            print(f"  {test['user_email']:30} | {status} | {percent:.1f}% of quota")

        except Exception as e:
            print(f"  ❌ Error testing {test['user_email']}: {str(e)[:50]}")

def main():
    print("\n" + "="*70)
    print("COMPLETING CCWB SETUP WITH USER-LEVEL TRACKING")
    print("="*70)

    # Seed quota policies
    seed_quota_policies()

    # Create Lambda functions
    create_lambda_functions()

    # Simulate user metrics
    simulate_user_metrics()

    # Test quota checking
    test_quota_check()

    # Deploy user-level dashboard
    print("\n📊 Deploying User-Level Dashboard...")
    import subprocess
    subprocess.run(['python3', 'deploy_user_level_dashboard.py'])

    print("\n" + "="*70)
    print("✅ CCWB SETUP COMPLETE!")
    print("="*70)

    print("\n📋 What's Now Available:")
    print("  • QuotaPolicies table with 6 policies")
    print("  • UserQuotaMetrics table with simulated data")
    print("  • CCWB-QuotaCheck Lambda function")
    print("  • User-level CloudWatch dashboard")

    print("\n🔗 Resources:")
    print(f"  • User Dashboard: https://console.aws.amazon.com/cloudwatch/home?region={REGION}#dashboards:name=CCWB-UserLevel-QuotaMonitoring")
    print(f"  • Quota Dashboard: https://console.aws.amazon.com/cloudwatch/home?region={REGION}#dashboards:name=CCWB-Quota-Monitoring")
    print(f"  • DynamoDB Tables: https://console.aws.amazon.com/dynamodb/home?region={REGION}#tables:")

    print("\n📝 Test Commands:")
    print("  • Check policies: aws dynamodb scan --table-name QuotaPolicies --region us-west-2")
    print("  • Check metrics: aws dynamodb scan --table-name UserQuotaMetrics --region us-west-2")
    print("  • Test quota: aws lambda invoke --function-name CCWB-QuotaCheck --payload '{\"user_email\":\"john.doe@company.com\"}' response.json")

if __name__ == "__main__":
    main()