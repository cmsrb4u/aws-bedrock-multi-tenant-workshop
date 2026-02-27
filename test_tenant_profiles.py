"""
Lab: Testing Application Inference Profiles with Multi-Tenant Workloads

This script demonstrates:
1. Making inference calls using tenant-specific Application Inference Profiles
2. Showing that each tenant's usage is tracked separately
3. Fetching CloudWatch metrics for each tenant independently
4. Visualizing the separation
"""

import boto3
import json
import time
import datetime
from datetime import timedelta
import matplotlib.pyplot as plt
from lab_helpers.config import Region

# Load tenant profile configuration
with open('/workshop/tenant_profiles.json', 'r') as f:
    profile_config = json.load(f)

# Initialize Bedrock runtime client
bedrock_runtime = boto3.client('bedrock-runtime', region_name=Region)

print("=" * 80)
print("🧪 Testing Application Inference Profiles - Multi-Tenant Separation")
print("=" * 80)

# Define the same prompts as before
TENANT_PROMPTS = {
    "tenant_a": {
        "prompt": "Generate a brief marketing campaign for a B2B SaaS DevOps automation platform targeting CTOs.",
        "profile_arn": profile_config['tenant_a_profile_arn'],
        "name": "Tenant A (Marketing)"
    },
    "tenant_b": {
        "prompt": "Generate a brief marketing campaign for a B2C sustainable fashion collection targeting millennials.",
        "profile_arn": profile_config['tenant_b_profile_arn'],
        "name": "Tenant B (Sales)"
    }
}

print("\n🔄 Making inference calls with SEPARATE Application Inference Profiles...")
print("=" * 80)

# Track results
results = {}

# Make inference calls for both tenants
for idx, (tenant_id, config) in enumerate(TENANT_PROMPTS.items()):
    print(f"\n🏢 Request from {config['name']}:")
    print(f"   Profile ARN: {config['profile_arn']}")
    print(f"   Prompt: {config['prompt'][:80]}...")

    body = json.dumps({
        "messages": [{
            "role": "user",
            "content": [{"type": "text", "text": config['prompt']}]
        }],
        "max_tokens": 1024,
        "anthropic_version": "bedrock-2023-05-31"
    })

    # THE SOLUTION: Each tenant uses their OWN profile ARN!
    response = bedrock_runtime.invoke_model(
        modelId=config['profile_arn'],  # ✅ Using tenant-specific profile!
        body=body
    )

    response_body = json.loads(response['body'].read())

    output_text = response_body['content'][0]['text']
    input_tokens = response_body['usage']['input_tokens']
    output_tokens = response_body['usage']['output_tokens']

    results[tenant_id] = {
        'input_tokens': input_tokens,
        'output_tokens': output_tokens,
        'output_preview': output_text[:100]
    }

    print(f"   ✅ Response received")
    print(f"   Input tokens: {input_tokens}")
    print(f"   Output tokens: {output_tokens}")
    print(f"   Response preview: {output_text[:100]}...")

    # Add gap between requests for CloudWatch visualization
    if idx == 0:
        print(f"\n   ⏳ Waiting 60 seconds before next request (for CloudWatch separation)...")
        time.sleep(60)
        print(f"   ✅ Wait complete - proceeding with {TENANT_PROMPTS['tenant_b']['name']} request")

print("\n" + "=" * 80)
print("✅ THE SOLUTION: Each tenant used their OWN Application Inference Profile!")
print(f"   Tenant A Profile: {profile_config['tenant_a_profile_arn']}")
print(f"   Tenant B Profile: {profile_config['tenant_b_profile_arn']}")
print("   Now each tenant's usage is tracked SEPARATELY in CloudWatch!")
print("=" * 80)

# Wait for CloudWatch metrics to propagate
print("\n⏳ Waiting 60 seconds for CloudWatch metrics to propagate...")
time.sleep(60)
print("✅ Wait complete - fetching metrics")

# Function to fetch metrics for a specific profile
def fetch_profile_metrics(profile_arn, tenant_name):
    cloudwatch = boto3.client('cloudwatch', region_name=Region)

    end_time = datetime.datetime.now(datetime.UTC)
    start_time = end_time - timedelta(minutes=60)

    # Extract profile ID from ARN
    profile_id = profile_arn.split('/')[-1]

    print(f"\n{'=' * 60}")
    print(f"📊 Fetching metrics for {tenant_name}")
    print(f"   Profile ID: {profile_id}")
    print(f"{'=' * 60}")

    # Get Invocations
    inv_response = cloudwatch.get_metric_statistics(
        Namespace='AWS/Bedrock',
        MetricName='Invocations',
        Dimensions=[
            {
                'Name': 'InferenceProfileId',
                'Value': profile_id
            }
        ],
        StartTime=start_time,
        EndTime=end_time,
        Period=60,
        Statistics=['Sum']
    )

    print(f"\nInvocation Count:")
    inv_count = 0
    for datapoint in sorted(inv_response['Datapoints'], key=lambda x: x['Timestamp']):
        print(f"   Time: {datapoint['Timestamp']}, Count: {datapoint['Sum']}")
        inv_count += datapoint['Sum']
    print(f"   Total Invocations: {inv_count}")

    # Get Input Tokens
    input_response = cloudwatch.get_metric_statistics(
        Namespace='AWS/Bedrock',
        MetricName='InputTokenCount',
        Dimensions=[
            {
                'Name': 'InferenceProfileId',
                'Value': profile_id
            }
        ],
        StartTime=start_time,
        EndTime=end_time,
        Period=60,
        Statistics=['Sum']
    )

    print(f"\nInput Token Count:")
    input_total = 0
    for datapoint in sorted(input_response['Datapoints'], key=lambda x: x['Timestamp']):
        print(f"   Time: {datapoint['Timestamp']}, Tokens: {datapoint['Sum']}")
        input_total += datapoint['Sum']
    print(f"   Total Input Tokens: {input_total}")

    # Get Output Tokens
    output_response = cloudwatch.get_metric_statistics(
        Namespace='AWS/Bedrock',
        MetricName='OutputTokenCount',
        Dimensions=[
            {
                'Name': 'InferenceProfileId',
                'Value': profile_id
            }
        ],
        StartTime=start_time,
        EndTime=end_time,
        Period=60,
        Statistics=['Sum']
    )

    print(f"\nOutput Token Count:")
    output_total = 0
    for datapoint in sorted(output_response['Datapoints'], key=lambda x: x['Timestamp']):
        print(f"   Time: {datapoint['Timestamp']}, Tokens: {datapoint['Sum']}")
        output_total += datapoint['Sum']
    print(f"   Total Output Tokens: {output_total}")

    return inv_response, input_response, output_response

# Fetch metrics for each tenant separately
tenant_a_metrics = fetch_profile_metrics(
    profile_config['tenant_a_profile_arn'],
    "Tenant A (Marketing)"
)

tenant_b_metrics = fetch_profile_metrics(
    profile_config['tenant_b_profile_arn'],
    "Tenant B (Sales)"
)

# Create comparison visualization
print("\n" + "=" * 80)
print("📊 Creating visualization comparing both tenants...")
print("=" * 80)

fig, axes = plt.subplots(3, 2, figsize=(16, 12))
fig.suptitle('Multi-Tenant Usage: Separate Application Inference Profiles', fontsize=16, fontweight='bold')

tenants_data = [
    ("Tenant A (Marketing)", tenant_a_metrics, 'blue'),
    ("Tenant B (Sales)", tenant_b_metrics, 'orange')
]

for col, (tenant_name, metrics, color) in enumerate(tenants_data):
    inv_response, input_response, output_response = metrics

    # Plot Invocations
    inv_data = sorted(inv_response['Datapoints'], key=lambda x: x['Timestamp'])
    if inv_data:
        inv_times = [dp['Timestamp'] for dp in inv_data]
        inv_values = [dp['Sum'] for dp in inv_data]
        axes[0, col].plot(inv_times, inv_values, marker='o', linewidth=2, color=color)
    axes[0, col].set_title(f'{tenant_name} - Invocations')
    axes[0, col].set_ylabel('Count')
    axes[0, col].grid(True)
    axes[0, col].tick_params(axis='x', rotation=45)

    # Plot Input Tokens
    input_data = sorted(input_response['Datapoints'], key=lambda x: x['Timestamp'])
    if input_data:
        input_times = [dp['Timestamp'] for dp in input_data]
        input_values = [dp['Sum'] for dp in input_data]
        axes[1, col].plot(input_times, input_values, marker='o', linewidth=2, color=color)
    axes[1, col].set_title(f'{tenant_name} - Input Tokens')
    axes[1, col].set_ylabel('Tokens')
    axes[1, col].grid(True)
    axes[1, col].tick_params(axis='x', rotation=45)

    # Plot Output Tokens
    output_data = sorted(output_response['Datapoints'], key=lambda x: x['Timestamp'])
    if output_data:
        output_times = [dp['Timestamp'] for dp in output_data]
        output_values = [dp['Sum'] for dp in output_data]
        axes[2, col].plot(output_times, output_values, marker='o', linewidth=2, color=color)
    axes[2, col].set_title(f'{tenant_name} - Output Tokens')
    axes[2, col].set_ylabel('Tokens')
    axes[2, col].grid(True)
    axes[2, col].tick_params(axis='x', rotation=45)

plt.tight_layout()
plt.savefig('/workshop/tenant_separation_metrics.png', dpi=150, bbox_inches='tight')
print("✅ Visualization saved to: /workshop/tenant_separation_metrics.png")

print("\n" + "=" * 80)
print("🎉 SUCCESS: Multi-Tenant Separation Achieved!")
print("=" * 80)
print("\n✅ Key Benefits Demonstrated:")
print("   1. Each tenant has separate CloudWatch metrics")
print("   2. Usage tracked independently per tenant")
print("   3. Can set different quotas/limits per tenant")
print("   4. Cost allocation via tags (tenant, department, costcenter)")
print("   5. No metric aggregation - complete isolation")
print("\n💡 Next Steps:")
print("   - View metrics in CloudWatch console")
print("   - Set up cost allocation reports in AWS Cost Explorer")
print("   - Configure alarms per tenant profile")
print("   - Implement per-tenant rate limiting")
print("=" * 80)
