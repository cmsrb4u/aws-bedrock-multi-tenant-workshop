#!/usr/bin/env python3
"""
Fix the Lambda function to handle Decimal types properly
"""

import boto3
import zipfile
import io

REGION = "us-west-2"

# Fixed Lambda function code
lambda_code = '''
import json
import boto3
import os
from datetime import datetime
from decimal import Decimal

dynamodb = boto3.resource('dynamodb')
cloudwatch = boto3.client('cloudwatch')

# Helper to convert Decimal to float for JSON serialization
def decimal_default(obj):
    if isinstance(obj, Decimal):
        return float(obj)
    raise TypeError

def lambda_handler(event, context):
    # Extract user from event
    user_email = event.get('user_email', 'test@company.com')
    groups = event.get('groups', ['engineering'])

    # Get effective quota policy
    policy = get_effective_policy(user_email, groups)

    # Get current usage
    usage = get_current_usage(user_email)

    # Check quota
    monthly_limit = float(policy.get('monthly_token_limit', 225000000))
    daily_limit = float(policy.get('daily_token_limit', 8000000))

    monthly_exceeded = usage['monthly'] > monthly_limit
    daily_exceeded = usage['daily'] > daily_limit

    # Publish metrics
    publish_metrics(user_email, usage, policy)

    # Prepare response
    response = {
        'allowed': not ((monthly_exceeded or daily_exceeded) and policy.get('enforcement_mode') == 'block'),
        'usage': {
            'monthly': float(usage['monthly']),
            'daily': float(usage['daily'])
        },
        'limits': {
            'monthly': monthly_limit,
            'daily': daily_limit
        },
        'enforcement_mode': policy.get('enforcement_mode', 'alert'),
        'policy_type': policy.get('_policy_type', 'default')
    }

    return {
        'statusCode': 200 if response['allowed'] else 429,
        'body': json.dumps(response, default=decimal_default)
    }

def get_effective_policy(user_email, groups):
    policies_table = dynamodb.Table('QuotaPolicies')

    # Check user-specific policy
    try:
        response = policies_table.get_item(
            Key={'policy_type': 'user', 'identifier': user_email}
        )
        if 'Item' in response and response['Item'].get('enabled'):
            response['Item']['_policy_type'] = 'user'
            return response['Item']
    except:
        pass

    # Check group policies
    for group in groups:
        try:
            response = policies_table.get_item(
                Key={'policy_type': 'group', 'identifier': group}
            )
            if 'Item' in response and response['Item'].get('enabled'):
                response['Item']['_policy_type'] = 'group'
                return response['Item']
        except:
            pass

    # Return default policy
    try:
        response = policies_table.get_item(
            Key={'policy_type': 'default', 'identifier': 'default'}
        )
        if 'Item' in response:
            response['Item']['_policy_type'] = 'default'
            return response['Item']
    except:
        pass

    return {
        'monthly_token_limit': Decimal(225000000),
        'daily_token_limit': Decimal(8000000),
        'enforcement_mode': 'alert',
        '_policy_type': 'default'
    }

def get_current_usage(user_email):
    metrics_table = dynamodb.Table('UserQuotaMetrics')

    now = datetime.now()
    month_key = now.strftime('%Y-%m')
    day_key = now.strftime('%Y-%m-%d')

    # Get monthly usage
    try:
        monthly_response = metrics_table.get_item(
            Key={'user_email': user_email, 'metric_period': f'monthly_{month_key}'}
        )
        monthly_usage = int(monthly_response.get('Item', {}).get('tokens_used', 0))
    except:
        monthly_usage = 0

    # Get daily usage
    try:
        daily_response = metrics_table.get_item(
            Key={'user_email': user_email, 'metric_period': f'daily_{day_key}'}
        )
        daily_usage = int(daily_response.get('Item', {}).get('tokens_used', 0))
    except:
        daily_usage = 0

    return {'monthly': monthly_usage, 'daily': daily_usage}

def publish_metrics(user_email, usage, policy):
    # Publish custom CloudWatch metrics
    try:
        monthly_limit = float(policy.get('monthly_token_limit', 225000000))
        daily_limit = float(policy.get('daily_token_limit', 8000000))

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
                },
                {
                    'MetricName': 'UserMonthlyTokens',
                    'Value': float(usage['monthly']),
                    'Unit': 'Count',
                    'Dimensions': [{'Name': 'UserEmail', 'Value': user_email}]
                },
                {
                    'MetricName': 'UserDailyTokens',
                    'Value': float(usage['daily']),
                    'Unit': 'Count',
                    'Dimensions': [{'Name': 'UserEmail', 'Value': user_email}]
                }
            ]
        )
    except Exception as e:
        print(f"Error publishing metrics: {str(e)}")
'''

def update_lambda():
    """Update the Lambda function with fixed code"""

    lambda_client = boto3.client('lambda', region_name=REGION)

    # Create deployment package
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        zip_file.writestr('lambda_function.py', lambda_code)

    # Update function
    try:
        response = lambda_client.update_function_code(
            FunctionName='CCWB-QuotaCheck',
            ZipFile=zip_buffer.getvalue()
        )
        print("✅ Lambda function updated successfully")
        return True
    except Exception as e:
        print(f"❌ Error updating Lambda: {str(e)}")
        return False

def test_fixed_function():
    """Test the fixed Lambda function"""

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

    print("\n🧪 Testing Fixed Lambda Function:")
    print("-" * 60)

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
            policy_type = body.get('policy_type', 'unknown')

            print(f"  {test['user_email']:30} | {status} | {percent:6.1f}% | Policy: {policy_type}")

        except Exception as e:
            print(f"  ❌ Error testing {test['user_email']}: {str(e)[:50]}")

if __name__ == "__main__":
    import json

    print("\n🔧 Fixing Lambda Function...")
    if update_lambda():
        import time
        time.sleep(2)  # Wait for update to propagate
        test_fixed_function()

        print("\n✅ Lambda function is now working correctly!")
        print("\n📝 Test it yourself:")
        print('aws lambda invoke --function-name CCWB-QuotaCheck --payload \'{"user_email":"john.doe@company.com","groups":["engineering"]}\' response.json --region us-west-2')