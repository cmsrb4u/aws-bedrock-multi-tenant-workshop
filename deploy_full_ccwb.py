#!/usr/bin/env python3
"""
Full CCWB Deployment Script with User-Level Tracking
Creates all necessary infrastructure for enterprise CCWB deployment
"""

import boto3
import json
import time
import subprocess
from datetime import datetime

# Configuration
REGION = "us-west-2"
ACCOUNT_ID = "899950533801"
STACK_PREFIX = "CCWB-UserLevel"

def create_quota_infrastructure_template():
    """Create CloudFormation template for quota infrastructure"""

    template = {
        "AWSTemplateFormatVersion": "2010-09-09",
        "Description": "CCWB User-Level Quota Infrastructure - DynamoDB Tables and Lambda Functions",

        "Resources": {
            # DynamoDB Table for Quota Policies
            "QuotaPoliciesTable": {
                "Type": "AWS::DynamoDB::Table",
                "Properties": {
                    "TableName": "QuotaPolicies",
                    "BillingMode": "PAY_PER_REQUEST",
                    "AttributeDefinitions": [
                        {"AttributeName": "policy_type", "AttributeType": "S"},
                        {"AttributeName": "identifier", "AttributeType": "S"}
                    ],
                    "KeySchema": [
                        {"AttributeName": "policy_type", "KeyType": "HASH"},
                        {"AttributeName": "identifier", "KeyType": "RANGE"}
                    ],
                    "Tags": [
                        {"Key": "Service", "Value": "CCWB"},
                        {"Key": "Component", "Value": "QuotaManagement"}
                    ]
                }
            },

            # DynamoDB Table for User Quota Metrics
            "UserQuotaMetricsTable": {
                "Type": "AWS::DynamoDB::Table",
                "Properties": {
                    "TableName": "UserQuotaMetrics",
                    "BillingMode": "PAY_PER_REQUEST",
                    "AttributeDefinitions": [
                        {"AttributeName": "user_email", "AttributeType": "S"},
                        {"AttributeName": "metric_period", "AttributeType": "S"}
                    ],
                    "KeySchema": [
                        {"AttributeName": "user_email", "KeyType": "HASH"},
                        {"AttributeName": "metric_period", "KeyType": "RANGE"}
                    ],
                    "TimeToLiveSpecification": {
                        "AttributeName": "ttl",
                        "Enabled": True
                    },
                    "Tags": [
                        {"Key": "Service", "Value": "CCWB"},
                        {"Key": "Component", "Value": "UserMetrics"}
                    ]
                }
            },

            # IAM Role for Lambda Functions
            "QuotaLambdaRole": {
                "Type": "AWS::IAM::Role",
                "Properties": {
                    "RoleName": "CCWB-QuotaLambdaRole",
                    "AssumeRolePolicyDocument": {
                        "Version": "2012-10-17",
                        "Statement": [{
                            "Effect": "Allow",
                            "Principal": {"Service": "lambda.amazonaws.com"},
                            "Action": "sts:AssumeRole"
                        }]
                    },
                    "ManagedPolicyArns": [
                        "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
                    ],
                    "Policies": [{
                        "PolicyName": "QuotaAccessPolicy",
                        "PolicyDocument": {
                            "Version": "2012-10-17",
                            "Statement": [
                                {
                                    "Effect": "Allow",
                                    "Action": [
                                        "dynamodb:GetItem",
                                        "dynamodb:PutItem",
                                        "dynamodb:UpdateItem",
                                        "dynamodb:Query",
                                        "dynamodb:Scan"
                                    ],
                                    "Resource": [
                                        {"Fn::GetAtt": ["QuotaPoliciesTable", "Arn"]},
                                        {"Fn::GetAtt": ["UserQuotaMetricsTable", "Arn"]}
                                    ]
                                },
                                {
                                    "Effect": "Allow",
                                    "Action": [
                                        "cloudwatch:PutMetricData"
                                    ],
                                    "Resource": "*"
                                },
                                {
                                    "Effect": "Allow",
                                    "Action": [
                                        "cognito-idp:AdminGetUser",
                                        "cognito-idp:ListUsersInGroup"
                                    ],
                                    "Resource": "*"
                                }
                            ]
                        }
                    }]
                }
            },

            # Lambda Function for Quota Checking
            "QuotaCheckFunction": {
                "Type": "AWS::Lambda::Function",
                "Properties": {
                    "FunctionName": "CCWB-QuotaCheck",
                    "Runtime": "python3.12",
                    "Handler": "index.lambda_handler",
                    "Role": {"Fn::GetAtt": ["QuotaLambdaRole", "Arn"]},
                    "Timeout": 30,
                    "Environment": {
                        "Variables": {
                            "QUOTA_POLICIES_TABLE": {"Ref": "QuotaPoliciesTable"},
                            "USER_METRICS_TABLE": {"Ref": "UserQuotaMetricsTable"}
                        }
                    },
                    "Code": {
                        "ZipFile": """
import json
import boto3
import os
from datetime import datetime, timedelta
from decimal import Decimal

dynamodb = boto3.resource('dynamodb')
cloudwatch = boto3.client('cloudwatch')

def lambda_handler(event, context):
    # Extract user from JWT claims
    user_email = event.get('requestContext', {}).get('authorizer', {}).get('claims', {}).get('email')
    if not user_email:
        return {'statusCode': 401, 'body': json.dumps({'error': 'User not authenticated'})}

    # Get user's groups from claims
    groups = event.get('requestContext', {}).get('authorizer', {}).get('claims', {}).get('cognito:groups', '').split(',')

    # Get effective quota policy (user > group > default)
    policy = get_effective_policy(user_email, groups)

    # Get current usage
    usage = get_current_usage(user_email)

    # Check quota
    monthly_exceeded = usage['monthly'] > policy.get('monthly_token_limit', float('inf'))
    daily_exceeded = usage['daily'] > policy.get('daily_token_limit', float('inf'))

    # Publish metrics
    publish_metrics(user_email, usage, policy)

    # Enforce quota
    if (monthly_exceeded or daily_exceeded) and policy.get('enforcement_mode') == 'block':
        return {
            'statusCode': 429,
            'body': json.dumps({
                'error': 'Quota exceeded',
                'monthly_usage': usage['monthly'],
                'monthly_limit': policy.get('monthly_token_limit'),
                'daily_usage': usage['daily'],
                'daily_limit': policy.get('daily_token_limit')
            })
        }

    # Allow request but log warning if needed
    if monthly_exceeded or daily_exceeded:
        print(f"WARNING: User {user_email} exceeded quota but enforcement is 'alert'")

    return {
        'statusCode': 200,
        'body': json.dumps({
            'allowed': True,
            'usage': usage,
            'limits': {
                'monthly': policy.get('monthly_token_limit'),
                'daily': policy.get('daily_token_limit')
            }
        })
    }

def get_effective_policy(user_email, groups):
    policies_table = dynamodb.Table(os.environ['QUOTA_POLICIES_TABLE'])

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
    metrics_table = dynamodb.Table(os.environ['USER_METRICS_TABLE'])

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
    cloudwatch.put_metric_data(
        Namespace='CCWB/UserQuota',
        MetricData=[
            {
                'MetricName': 'MonthlyUsagePercent',
                'Value': (usage['monthly'] / policy.get('monthly_token_limit', 1)) * 100,
                'Unit': 'Percent',
                'Dimensions': [{'Name': 'UserEmail', 'Value': user_email}]
            },
            {
                'MetricName': 'DailyUsagePercent',
                'Value': (usage['daily'] / policy.get('daily_token_limit', 1)) * 100,
                'Unit': 'Percent',
                'Dimensions': [{'Name': 'UserEmail', 'Value': user_email}]
            }
        ]
    )
"""
                    }
                }
            },

            # Lambda Function for Metrics Recording
            "MetricsRecorderFunction": {
                "Type": "AWS::Lambda::Function",
                "Properties": {
                    "FunctionName": "CCWB-MetricsRecorder",
                    "Runtime": "python3.12",
                    "Handler": "index.lambda_handler",
                    "Role": {"Fn::GetAtt": ["QuotaLambdaRole", "Arn"]},
                    "Timeout": 30,
                    "Environment": {
                        "Variables": {
                            "USER_METRICS_TABLE": {"Ref": "UserQuotaMetricsTable"}
                        }
                    },
                    "Code": {
                        "ZipFile": """
import json
import boto3
import os
from datetime import datetime, timedelta
from decimal import Decimal

dynamodb = boto3.resource('dynamodb')
cloudwatch = boto3.client('cloudwatch')

def lambda_handler(event, context):
    # Parse Bedrock response to extract token usage
    user_email = event.get('user_email')
    input_tokens = event.get('input_tokens', 0)
    output_tokens = event.get('output_tokens', 0)
    total_tokens = input_tokens + output_tokens

    if not user_email:
        return {'statusCode': 400, 'body': json.dumps({'error': 'User email required'})}

    # Update usage metrics
    metrics_table = dynamodb.Table(os.environ['USER_METRICS_TABLE'])

    now = datetime.now()
    month_key = now.strftime('%Y-%m')
    day_key = now.strftime('%Y-%m-%d')

    # Update monthly usage
    metrics_table.update_item(
        Key={'user_email': user_email, 'metric_period': f'monthly_{month_key}'},
        UpdateExpression='ADD tokens_used :val SET last_updated = :now, ttl = :ttl',
        ExpressionAttributeValues={
            ':val': Decimal(total_tokens),
            ':now': now.isoformat(),
            ':ttl': int((now + timedelta(days=90)).timestamp())
        }
    )

    # Update daily usage
    metrics_table.update_item(
        Key={'user_email': user_email, 'metric_period': f'daily_{day_key}'},
        UpdateExpression='ADD tokens_used :val SET last_updated = :now, ttl = :ttl',
        ExpressionAttributeValues={
            ':val': Decimal(total_tokens),
            ':now': now.isoformat(),
            ':ttl': int((now + timedelta(days=7)).timestamp())
        }
    )

    # Publish CloudWatch metrics
    cloudwatch.put_metric_data(
        Namespace='CCWB/UserQuota',
        MetricData=[
            {
                'MetricName': 'UserInputTokens',
                'Value': input_tokens,
                'Unit': 'Count',
                'Dimensions': [{'Name': 'UserEmail', 'Value': user_email}]
            },
            {
                'MetricName': 'UserOutputTokens',
                'Value': output_tokens,
                'Unit': 'Count',
                'Dimensions': [{'Name': 'UserEmail', 'Value': user_email}]
            }
        ]
    )

    return {
        'statusCode': 200,
        'body': json.dumps({
            'recorded': True,
            'user': user_email,
            'tokens': total_tokens
        })
    }
"""
                    }
                }
            }
        },

        "Outputs": {
            "QuotaPoliciesTableArn": {
                "Description": "ARN of QuotaPolicies DynamoDB table",
                "Value": {"Fn::GetAtt": ["QuotaPoliciesTable", "Arn"]},
                "Export": {"Name": "CCWB-QuotaPoliciesTableArn"}
            },
            "UserQuotaMetricsTableArn": {
                "Description": "ARN of UserQuotaMetrics DynamoDB table",
                "Value": {"Fn::GetAtt": ["UserQuotaMetricsTable", "Arn"]},
                "Export": {"Name": "CCWB-UserQuotaMetricsTableArn"}
            },
            "QuotaCheckFunctionArn": {
                "Description": "ARN of Quota Check Lambda function",
                "Value": {"Fn::GetAtt": ["QuotaCheckFunction", "Arn"]},
                "Export": {"Name": "CCWB-QuotaCheckFunctionArn"}
            },
            "MetricsRecorderFunctionArn": {
                "Description": "ARN of Metrics Recorder Lambda function",
                "Value": {"Fn::GetAtt": ["MetricsRecorderFunction", "Arn"]},
                "Export": {"Name": "CCWB-MetricsRecorderFunctionArn"}
            }
        }
    }

    return json.dumps(template, indent=2)

def deploy_infrastructure():
    """Deploy the CloudFormation stack"""

    print("\n" + "="*70)
    print("🚀 DEPLOYING FULL CCWB WITH USER-LEVEL TRACKING")
    print("="*70)

    # Create CloudFormation client
    cf_client = boto3.client('cloudformation', region_name=REGION)

    # Generate template
    template_body = create_quota_infrastructure_template()

    # Save template to file
    with open('/workshop/ccwb-quota-infrastructure.yaml', 'w') as f:
        f.write(template_body)

    print("\n📝 CloudFormation template saved to: ccwb-quota-infrastructure.yaml")

    stack_name = f"{STACK_PREFIX}-Infrastructure"

    try:
        print(f"\n🔧 Creating stack: {stack_name}")

        response = cf_client.create_stack(
            StackName=stack_name,
            TemplateBody=template_body,
            Capabilities=['CAPABILITY_NAMED_IAM'],
            Tags=[
                {'Key': 'Service', 'Value': 'CCWB'},
                {'Key': 'Environment', 'Value': 'Workshop'}
            ]
        )

        stack_id = response['StackId']
        print(f"✅ Stack creation initiated: {stack_id}")

        # Wait for stack creation
        print("\n⏳ Waiting for stack creation to complete...")
        waiter = cf_client.get_waiter('stack_create_complete')
        waiter.wait(
            StackName=stack_name,
            WaiterConfig={'Delay': 10, 'MaxAttempts': 60}
        )

        print("✅ Stack created successfully!")

        # Get outputs
        stack_info = cf_client.describe_stacks(StackName=stack_name)
        outputs = stack_info['Stacks'][0].get('Outputs', [])

        print("\n📊 Stack Outputs:")
        for output in outputs:
            print(f"  • {output['OutputKey']}: {output['OutputValue']}")

        return True

    except Exception as e:
        print(f"❌ Error deploying stack: {str(e)}")
        return False

def seed_initial_policies():
    """Seed initial quota policies into DynamoDB"""

    print("\n📝 Seeding initial quota policies...")

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
            'identifier': 'executive',
            'monthly_token_limit': 1000000000, # 1B
            'daily_token_limit': 50000000,     # 50M
            'enforcement_mode': 'alert',
            'enabled': True,
            'created_at': datetime.now().isoformat()
        }
    ]

    for policy in policies:
        try:
            table.put_item(Item=policy)
            print(f"  ✅ Created policy: {policy['policy_type']}:{policy['identifier']}")
        except Exception as e:
            print(f"  ❌ Error creating policy: {str(e)}")

    print("\n✅ Initial policies seeded successfully!")

def main():
    print("\n" + "="*70)
    print("FULL CCWB DEPLOYMENT WITH USER-LEVEL TRACKING")
    print("="*70)

    print("\nThis will deploy:")
    print("  • 2 DynamoDB tables (QuotaPolicies, UserQuotaMetrics)")
    print("  • 2 Lambda functions (QuotaCheck, MetricsRecorder)")
    print("  • IAM roles and policies")
    print("  • Custom CloudWatch metrics namespace")

    response = input("\nProceed with deployment? (y/n): ")

    if response.lower() != 'y':
        print("Deployment cancelled.")
        return

    # Deploy infrastructure
    if deploy_infrastructure():
        # Wait a bit for resources to be available
        time.sleep(10)

        # Seed initial policies
        seed_initial_policies()

        print("\n" + "="*70)
        print("✅ DEPLOYMENT COMPLETE!")
        print("="*70)

        print("\nNext Steps:")
        print("1. Configure Cognito User Pool with groups")
        print("2. Set up API Gateway with Lambda integration")
        print("3. Create user-level CloudWatch dashboard")
        print("4. Test quota enforcement with sample users")

        print("\nUseful Commands:")
        print("  • View policies: aws dynamodb scan --table-name QuotaPolicies")
        print("  • Check metrics: aws dynamodb scan --table-name UserQuotaMetrics")
        print("  • Test Lambda: aws lambda invoke --function-name CCWB-QuotaCheck")

if __name__ == "__main__":
    main()