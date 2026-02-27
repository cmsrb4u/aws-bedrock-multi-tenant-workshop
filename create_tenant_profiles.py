"""
Lab: Create Application Inference Profiles for Multi-Tenant Architecture

This script creates separate Application Inference Profiles (AIPs) for:
- Tenant A (Marketing Department)
- Tenant B (Sales Department)

Each AIP will have its own tags for cost tracking and usage monitoring.
"""

import boto3
import json
from lab_helpers.config import Region, ModelId, tenant_a_tags, tenant_b_tags

# Initialize Bedrock client
bedrock_client = boto3.client('bedrock', region_name=Region)

print("=" * 80)
print("🏗️  Creating Application Inference Profiles for Multi-Tenant Setup")
print("=" * 80)

# Define tenant profile configurations
tenants = {
    "tenant_a": {
        "profile_name": "aip-tenant-a-marketing",
        "tags": tenant_a_tags,
        "description": "Application Inference Profile for Tenant A (Marketing)"
    },
    "tenant_b": {
        "profile_name": "aip-tenant-b-sales",
        "tags": tenant_b_tags,
        "description": "Application Inference Profile for Tenant B (Sales)"
    }
}

# Get the system inference profile ARN to copy from
print(f"\n📋 Source Model Configuration:")
print(f"   System Inference Profile: {ModelId.DEFAULT}")

# We need to get the full ARN of the system inference profile
# List inference profiles to find the ARN
try:
    response = bedrock_client.list_inference_profiles()
    system_profile_arn = None

    for profile in response['inferenceProfileSummaries']:
        if profile['inferenceProfileId'] == ModelId.DEFAULT:
            system_profile_arn = profile['inferenceProfileArn']
            print(f"   System Profile ARN: {system_profile_arn}")
            break

    if not system_profile_arn:
        print(f"❌ Could not find system profile ARN for {ModelId.DEFAULT}")
        exit(1)

except Exception as e:
    print(f"❌ Error listing inference profiles: {e}")
    exit(1)

print("\n" + "=" * 80)

# Create Application Inference Profiles for each tenant
created_profiles = {}

for tenant_id, config in tenants.items():
    print(f"\n🏢 Creating profile for {tenant_id.upper().replace('_', ' ')}...")
    print(f"   Profile Name: {config['profile_name']}")
    print(f"   Tags: {config['tags']}")

    try:
        response = bedrock_client.create_inference_profile(
            inferenceProfileName=config['profile_name'],
            modelSource={
                'copyFrom': system_profile_arn
            },
            tags=config['tags']
        )

        profile_arn = response['inferenceProfileArn']
        status = response['status']

        created_profiles[tenant_id] = {
            'profile_name': config['profile_name'],
            'profile_arn': profile_arn,
            'status': status
        }

        print(f"   ✅ Profile created successfully!")
        print(f"   ARN: {profile_arn}")
        print(f"   Status: {status}")

    except bedrock_client.exceptions.ResourceNotFoundException as e:
        print(f"   ❌ Error: Model not found - {e}")
    except bedrock_client.exceptions.ValidationException as e:
        print(f"   ❌ Validation error - {e}")
    except Exception as e:
        # Check if profile already exists
        if "already exists" in str(e).lower() or "ConflictException" in str(e):
            print(f"   ⚠️  Profile already exists, fetching existing profile...")
            try:
                # Get the existing profile
                existing_response = bedrock_client.get_inference_profile(
                    inferenceProfileIdentifier=config['profile_name']
                )
                profile_arn = existing_response['inferenceProfileArn']
                status = existing_response['status']

                created_profiles[tenant_id] = {
                    'profile_name': config['profile_name'],
                    'profile_arn': profile_arn,
                    'status': status
                }

                print(f"   ✅ Using existing profile")
                print(f"   ARN: {profile_arn}")
                print(f"   Status: {status}")
            except Exception as fetch_error:
                print(f"   ❌ Error fetching existing profile: {fetch_error}")
        else:
            print(f"   ❌ Error creating profile: {e}")

print("\n" + "=" * 80)
print("📊 Summary of Created Application Inference Profiles")
print("=" * 80)

for tenant_id, profile_info in created_profiles.items():
    print(f"\n{tenant_id.upper().replace('_', ' ')}:")
    print(f"   Name: {profile_info['profile_name']}")
    print(f"   ARN: {profile_info['profile_arn']}")
    print(f"   Status: {profile_info['status']}")

# Save profile information to a file for later use
profile_config = {
    'tenant_a_profile_arn': created_profiles.get('tenant_a', {}).get('profile_arn', ''),
    'tenant_b_profile_arn': created_profiles.get('tenant_b', {}).get('profile_arn', ''),
    'system_profile_arn': system_profile_arn,
    'region': Region
}

with open('/workshop/tenant_profiles.json', 'w') as f:
    json.dump(profile_config, f, indent=2)

print("\n" + "=" * 80)
print("✅ Setup Complete!")
print("   Profile configuration saved to: /workshop/tenant_profiles.json")
print("=" * 80)

print("\n💡 Next Steps:")
print("   1. Use these profile ARNs for tenant-specific inference calls")
print("   2. Monitor usage per tenant in CloudWatch")
print("   3. Track costs using AWS Cost Explorer with profile tags")
