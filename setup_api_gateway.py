#!/usr/bin/env python3
"""
Set up API Gateway with Cognito Authorizer for CCWB User-Level Tracking
"""

import boto3
import json
from datetime import datetime

REGION = "us-west-2"

def create_api_gateway_template():
    """Create CloudFormation template for API Gateway"""

    template = {
        "AWSTemplateFormatVersion": "2010-09-09",
        "Description": "CCWB API Gateway with Cognito Authorizer for User-Level Tracking",

        "Parameters": {
            "CognitoUserPoolId": {
                "Type": "String",
                "Default": "us-west-2_qsKNoAXWR",
                "Description": "Cognito User Pool ID"
            },
            "QuotaCheckFunctionArn": {
                "Type": "String",
                "Description": "ARN of the Quota Check Lambda function"
            }
        },

        "Resources": {
            # Cognito User Pool Client
            "CognitoUserPoolClient": {
                "Type": "AWS::Cognito::UserPoolClient",
                "Properties": {
                    "ClientName": "CCWB-UserTracking-Client",
                    "UserPoolId": {"Ref": "CognitoUserPoolId"},
                    "GenerateSecret": False,
                    "ExplicitAuthFlows": [
                        "ALLOW_USER_PASSWORD_AUTH",
                        "ALLOW_REFRESH_TOKEN_AUTH"
                    ],
                    "SupportedIdentityProviders": ["COGNITO"],
                    "AllowedOAuthFlows": ["code", "implicit"],
                    "AllowedOAuthScopes": ["openid", "email", "profile"],
                    "CallbackURLs": ["http://localhost:3000/callback"],
                    "LogoutURLs": ["http://localhost:3000/logout"]
                }
            },

            # API Gateway REST API
            "CCWBApiGateway": {
                "Type": "AWS::ApiGateway::RestApi",
                "Properties": {
                    "Name": "CCWB-UserTracking-API",
                    "Description": "API Gateway for CCWB with user-level quota tracking",
                    "EndpointConfiguration": {
                        "Types": ["REGIONAL"]
                    }
                }
            },

            # Cognito Authorizer
            "CognitoAuthorizer": {
                "Type": "AWS::ApiGateway::Authorizer",
                "Properties": {
                    "Name": "CCWB-CognitoAuthorizer",
                    "Type": "COGNITO_USER_POOLS",
                    "IdentitySource": "method.request.header.Authorization",
                    "RestApiId": {"Ref": "CCWBApiGateway"},
                    "ProviderARNs": [
                        {"Fn::Sub": "arn:aws:cognito-idp:${AWS::Region}:${AWS::AccountId}:userpool/${CognitoUserPoolId}"}
                    ]
                }
            },

            # /bedrock resource
            "BedrockResource": {
                "Type": "AWS::ApiGateway::Resource",
                "Properties": {
                    "RestApiId": {"Ref": "CCWBApiGateway"},
                    "ParentId": {"Fn::GetAtt": ["CCWBApiGateway", "RootResourceId"]},
                    "PathPart": "bedrock"
                }
            },

            # /bedrock/invoke resource
            "InvokeResource": {
                "Type": "AWS::ApiGateway::Resource",
                "Properties": {
                    "RestApiId": {"Ref": "CCWBApiGateway"},
                    "ParentId": {"Ref": "BedrockResource"},
                    "PathPart": "invoke"
                }
            },

            # POST method for /bedrock/invoke
            "InvokeMethod": {
                "Type": "AWS::ApiGateway::Method",
                "Properties": {
                    "RestApiId": {"Ref": "CCWBApiGateway"},
                    "ResourceId": {"Ref": "InvokeResource"},
                    "HttpMethod": "POST",
                    "AuthorizationType": "COGNITO_USER_POOLS",
                    "AuthorizerId": {"Ref": "CognitoAuthorizer"},
                    "Integration": {
                        "Type": "AWS_PROXY",
                        "IntegrationHttpMethod": "POST",
                        "Uri": {
                            "Fn::Sub": "arn:aws:apigateway:${AWS::Region}:lambda:path/2015-03-31/functions/${QuotaCheckFunctionArn}/invocations"
                        }
                    },
                    "MethodResponses": [
                        {
                            "StatusCode": "200",
                            "ResponseModels": {
                                "application/json": "Empty"
                            }
                        },
                        {
                            "StatusCode": "429",
                            "ResponseModels": {
                                "application/json": "Error"
                            }
                        }
                    ]
                }
            },

            # Lambda permission for API Gateway
            "ApiGatewayInvokePermission": {
                "Type": "AWS::Lambda::Permission",
                "Properties": {
                    "FunctionName": {"Ref": "QuotaCheckFunctionArn"},
                    "Action": "lambda:InvokeFunction",
                    "Principal": "apigateway.amazonaws.com",
                    "SourceArn": {
                        "Fn::Sub": "arn:aws:execute-api:${AWS::Region}:${AWS::AccountId}:${CCWBApiGateway}/*/*"
                    }
                }
            },

            # API Deployment
            "ApiDeployment": {
                "Type": "AWS::ApiGateway::Deployment",
                "DependsOn": ["InvokeMethod"],
                "Properties": {
                    "RestApiId": {"Ref": "CCWBApiGateway"},
                    "StageName": "prod",
                    "StageDescription": {
                        "ThrottlingBurstLimit": 100,
                        "ThrottlingRateLimit": 50,
                        "MetricsEnabled": True,
                        "LoggingLevel": "INFO",
                        "DataTraceEnabled": True
                    }
                }
            },

            # Usage Plan
            "UsagePlan": {
                "Type": "AWS::ApiGateway::UsagePlan",
                "DependsOn": ["ApiDeployment"],
                "Properties": {
                    "UsagePlanName": "CCWB-UserTracking-UsagePlan",
                    "Description": "Usage plan with throttling for CCWB API",
                    "ApiStages": [
                        {
                            "ApiId": {"Ref": "CCWBApiGateway"},
                            "Stage": "prod"
                        }
                    ],
                    "Throttle": {
                        "BurstLimit": 100,
                        "RateLimit": 50
                    }
                }
            }
        },

        "Outputs": {
            "ApiGatewayUrl": {
                "Description": "API Gateway Invoke URL",
                "Value": {
                    "Fn::Sub": "https://${CCWBApiGateway}.execute-api.${AWS::Region}.amazonaws.com/prod"
                },
                "Export": {"Name": "CCWB-ApiGatewayUrl"}
            },
            "UserPoolClientId": {
                "Description": "Cognito User Pool Client ID",
                "Value": {"Ref": "CognitoUserPoolClient"},
                "Export": {"Name": "CCWB-UserPoolClientId"}
            }
        }
    }

    return json.dumps(template, indent=2)

def setup_cognito_groups():
    """Set up Cognito User Pool groups"""

    print("\n📝 Setting up Cognito User Pool groups...")

    cognito = boto3.client('cognito-idp', region_name=REGION)
    user_pool_id = "us-west-2_qsKNoAXWR"

    groups = [
        {
            'GroupName': 'engineering',
            'Description': 'Engineering Team - 400M monthly / 15M daily quota',
            'Precedence': 10
        },
        {
            'GroupName': 'sales',
            'Description': 'Sales Team - 300M monthly / 10M daily quota',
            'Precedence': 20
        },
        {
            'GroupName': 'marketing',
            'Description': 'Marketing Team - 250M monthly / 8M daily quota',
            'Precedence': 30
        },
        {
            'GroupName': 'executive',
            'Description': 'Executive Team - 1B monthly / 50M daily quota',
            'Precedence': 1
        }
    ]

    for group in groups:
        try:
            cognito.create_group(
                GroupName=group['GroupName'],
                UserPoolId=user_pool_id,
                Description=group['Description'],
                Precedence=group['Precedence']
            )
            print(f"  ✅ Created group: {group['GroupName']}")
        except cognito.exceptions.GroupExistsException:
            print(f"  ⚠️ Group already exists: {group['GroupName']}")
        except Exception as e:
            print(f"  ❌ Error creating group: {str(e)}")

def create_test_users():
    """Create test users in Cognito"""

    print("\n👤 Creating test users...")

    cognito = boto3.client('cognito-idp', region_name=REGION)
    user_pool_id = "us-west-2_qsKNoAXWR"

    users = [
        {
            'Username': 'john.doe@company.com',
            'Email': 'john.doe@company.com',
            'Group': 'engineering',
            'Password': 'TempPassword123!'
        },
        {
            'Username': 'jane.smith@company.com',
            'Email': 'jane.smith@company.com',
            'Group': 'sales',
            'Password': 'TempPassword123!'
        },
        {
            'Username': 'bob.marketing@company.com',
            'Email': 'bob.marketing@company.com',
            'Group': 'marketing',
            'Password': 'TempPassword123!'
        },
        {
            'Username': 'alice.exec@company.com',
            'Email': 'alice.exec@company.com',
            'Group': 'executive',
            'Password': 'TempPassword123!'
        }
    ]

    for user in users:
        try:
            # Create user
            cognito.admin_create_user(
                UserPoolId=user_pool_id,
                Username=user['Username'],
                UserAttributes=[
                    {'Name': 'email', 'Value': user['Email']},
                    {'Name': 'email_verified', 'Value': 'true'}
                ],
                TemporaryPassword=user['Password'],
                MessageAction='SUPPRESS'
            )

            # Set permanent password
            cognito.admin_set_user_password(
                UserPoolId=user_pool_id,
                Username=user['Username'],
                Password=user['Password'],
                Permanent=True
            )

            # Add to group
            cognito.admin_add_user_to_group(
                UserPoolId=user_pool_id,
                Username=user['Username'],
                GroupName=user['Group']
            )

            print(f"  ✅ Created user: {user['Username']} in group {user['Group']}")

        except cognito.exceptions.UsernameExistsException:
            print(f"  ⚠️ User already exists: {user['Username']}")
        except Exception as e:
            print(f"  ❌ Error creating user: {str(e)}")

def deploy_api_gateway():
    """Deploy API Gateway stack"""

    print("\n🔧 Deploying API Gateway...")

    cf_client = boto3.client('cloudformation', region_name=REGION)

    # Get QuotaCheck function ARN from previous stack
    try:
        stack_info = cf_client.describe_stacks(StackName='CCWB-UserLevel-Infrastructure')
        outputs = stack_info['Stacks'][0].get('Outputs', [])

        quota_check_arn = None
        for output in outputs:
            if output['OutputKey'] == 'QuotaCheckFunctionArn':
                quota_check_arn = output['OutputValue']
                break

        if not quota_check_arn:
            print("❌ Could not find QuotaCheck function ARN")
            return False

        # Create template
        template_body = create_api_gateway_template()

        # Save template
        with open('/workshop/ccwb-api-gateway.yaml', 'w') as f:
            f.write(template_body)

        print("📝 Template saved to: ccwb-api-gateway.yaml")

        # Deploy stack
        stack_name = "CCWB-UserLevel-APIGateway"

        response = cf_client.create_stack(
            StackName=stack_name,
            TemplateBody=template_body,
            Parameters=[
                {
                    'ParameterKey': 'QuotaCheckFunctionArn',
                    'ParameterValue': quota_check_arn
                }
            ],
            Capabilities=['CAPABILITY_IAM']
        )

        print(f"✅ API Gateway stack creation initiated")

        # Wait for completion
        waiter = cf_client.get_waiter('stack_create_complete')
        waiter.wait(StackName=stack_name)

        print("✅ API Gateway deployed successfully!")

        return True

    except Exception as e:
        print(f"❌ Error deploying API Gateway: {str(e)}")
        return False

def main():
    print("\n" + "="*70)
    print("API GATEWAY & COGNITO SETUP FOR USER-LEVEL TRACKING")
    print("="*70)

    print("\nThis will:")
    print("  • Create API Gateway with Cognito Authorizer")
    print("  • Set up Cognito User Pool groups")
    print("  • Create test users with different quota levels")
    print("  • Configure throttling and usage plans")

    # Set up Cognito groups
    setup_cognito_groups()

    # Create test users
    create_test_users()

    # Deploy API Gateway
    deploy_api_gateway()

    print("\n" + "="*70)
    print("✅ API GATEWAY SETUP COMPLETE!")
    print("="*70)

if __name__ == "__main__":
    main()