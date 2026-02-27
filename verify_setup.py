"""
Quick verification script to check Application Inference Profile setup
"""

import boto3
import json
from lab_helpers.config import Region

# Load tenant profile configuration
with open('/workshop/tenant_profiles.json', 'r') as f:
    profile_config = json.load(f)

bedrock = boto3.client('bedrock', region_name=Region)

print("=" * 80)
print("✅ Application Inference Profiles - Setup Verification")
print("=" * 80)

print("\n📋 Profile Configuration:")
print(f"   Region: {Region}")

for tenant_name, key in [("Tenant A", "tenant_a_profile_arn"), ("Tenant B", "tenant_b_profile_arn")]:
    arn = profile_config[key]
    profile_id = arn.split('/')[-1]

    print(f"\n{tenant_name}:")
    print(f"   ARN: {arn}")
    print(f"   Profile ID: {profile_id}")

    # Get profile details
    try:
        profile_details = bedrock.get_inference_profile(
            inferenceProfileIdentifier=profile_id
        )
        print(f"   Status: {profile_details['status']}")
        print(f"   Type: {profile_details['type']}")

        # Get tags
        tags_response = bedrock.list_tags_for_resource(resourceARN=arn)
        print(f"   Tags:")
        for tag in tags_response['tags']:
            print(f"      - {tag['key']}: {tag['value']}")

    except Exception as e:
        print(f"   Error: {e}")

print("\n" + "=" * 80)
print("🎯 Testing Instructions:")
print("=" * 80)
print("""
To test the Application Inference Profiles:

1. **Run inference calls** (already done if you ran test_tenant_profiles.py)

2. **Wait 3-5 minutes** for CloudWatch metrics to propagate

3. **Check metrics in AWS Console**:
   - Go to CloudWatch Console
   - Navigate to Metrics > All metrics
   - Select "AWS/Bedrock" namespace
   - Look for dimension "InferenceProfileId"
   - You should see separate metrics for:
     * 5gematyf83m0 (Tenant A - Marketing)
     * yku79b5wumnr (Tenant B - Sales)

4. **Check Cost Allocation**:
   - Go to AWS Cost Explorer
   - Filter by tags:
     * tenant=tenant_a (Marketing)
     * tenant=tenant_b (Sales)
   - View costs separately per tenant

5. **Re-run metrics script** after waiting:
   python /workshop/test_tenant_profiles.py
""")

print("\n" + "=" * 80)
print("🔑 Key Differences from System Profile:")
print("=" * 80)
print("""
❌ BEFORE (System Profile):
   - All tenants use: us.anthropic.claude-sonnet-4-6
   - Metrics aggregated together
   - No cost separation
   - No per-tenant limits

✅ AFTER (Application Inference Profiles):
   - Tenant A uses: 5gematyf83m0
   - Tenant B uses: yku79b5wumnr
   - Separate CloudWatch metrics
   - Tag-based cost allocation
   - Can set per-tenant quotas
""")

print("=" * 80)
