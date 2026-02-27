"""
Invoke Application Inference Profiles and Visualize Metrics

This script:
1. Makes inference calls using tenant-specific profiles
2. Waits for CloudWatch metrics to propagate (3-5 minutes)
3. Fetches the metrics
4. Creates comparison visualizations
"""

import boto3
import json
import time
import datetime
from datetime import timedelta
import matplotlib.pyplot as plt
from lab_helpers.config import Region

print("=" * 80)
print("🚀 Invoking Application Inference Profiles & Generating Metrics")
print("=" * 80)

# Load tenant profiles
with open('/workshop/tenant_profiles.json', 'r') as f:
    profile_config = json.load(f)

bedrock_runtime = boto3.client('bedrock-runtime', region_name=Region)
cloudwatch = boto3.client('cloudwatch', region_name=Region)

# Define test prompts
PROMPTS = {
    "tenant_a": {
        "prompt": "Explain quantum computing in 2 sentences.",
        "profile_arn": profile_config['tenant_a_profile_arn'],
        "name": "Tenant A (Marketing)"
    },
    "tenant_b": {
        "prompt": "What are the benefits of cloud computing?",
        "profile_arn": profile_config['tenant_b_profile_arn'],
        "name": "Tenant B (Sales)"
    }
}

print("\n📞 Making inference calls...")
print("-" * 80)

call_times = []

# Make calls for both tenants
for tenant_id, config in PROMPTS.items():
    print(f"\n🏢 {config['name']}")
    print(f"   Using profile: {config['profile_arn'].split('/')[-1]}")

    body = json.dumps({
        "messages": [{
            "role": "user",
            "content": [{"type": "text", "text": config['prompt']}]
        }],
        "max_tokens": 512,
        "anthropic_version": "bedrock-2023-05-31"
    })

    call_time = datetime.datetime.now(datetime.UTC)
    call_times.append(call_time)

    response = bedrock_runtime.invoke_model(
        modelId=config['profile_arn'],
        body=body
    )

    response_body = json.loads(response['body'].read())
    input_tokens = response_body['usage']['input_tokens']
    output_tokens = response_body['usage']['output_tokens']

    print(f"   ✅ Success: {input_tokens} input tokens, {output_tokens} output tokens")

    time.sleep(5)  # Small gap between calls

print("\n" + "=" * 80)
print("⏳ Waiting for CloudWatch metrics to propagate...")
print("   This typically takes 3-5 minutes. Please be patient...")
print("=" * 80)

# Wait 4 minutes for metrics to propagate
wait_time = 240  # 4 minutes
for i in range(wait_time // 30):
    remaining = wait_time - (i * 30)
    print(f"   ⏱️  {remaining} seconds remaining...")
    time.sleep(30)

print("   ✅ Wait complete - fetching metrics now")

# Function to fetch and display metrics
def fetch_and_plot_metrics(profile_arn, tenant_name, color):
    profile_id = profile_arn.split('/')[-1]

    end_time = datetime.datetime.now(datetime.UTC)
    start_time = end_time - timedelta(minutes=15)  # Look back 15 minutes

    print(f"\n{'=' * 60}")
    print(f"📊 Fetching metrics for {tenant_name}")
    print(f"   Profile ID: {profile_id}")
    print(f"{'=' * 60}")

    # Fetch Invocations
    inv_response = cloudwatch.get_metric_statistics(
        Namespace='AWS/Bedrock',
        MetricName='Invocations',
        Dimensions=[{'Name': 'InferenceProfileId', 'Value': profile_id}],
        StartTime=start_time,
        EndTime=end_time,
        Period=60,
        Statistics=['Sum']
    )

    # Fetch Input Tokens
    input_response = cloudwatch.get_metric_statistics(
        Namespace='AWS/Bedrock',
        MetricName='InputTokenCount',
        Dimensions=[{'Name': 'InferenceProfileId', 'Value': profile_id}],
        StartTime=start_time,
        EndTime=end_time,
        Period=60,
        Statistics=['Sum']
    )

    # Fetch Output Tokens
    output_response = cloudwatch.get_metric_statistics(
        Namespace='AWS/Bedrock',
        MetricName='OutputTokenCount',
        Dimensions=[{'Name': 'InferenceProfileId', 'Value': profile_id}],
        StartTime=start_time,
        EndTime=end_time,
        Period=60,
        Statistics=['Sum']
    )

    # Print results
    inv_total = sum(dp['Sum'] for dp in inv_response['Datapoints'])
    input_total = sum(dp['Sum'] for dp in input_response['Datapoints'])
    output_total = sum(dp['Sum'] for dp in output_response['Datapoints'])

    print(f"\n📈 Metrics Summary:")
    print(f"   Invocations: {int(inv_total)}")
    print(f"   Input Tokens: {int(input_total)}")
    print(f"   Output Tokens: {int(output_total)}")
    print(f"   Total Tokens: {int(input_total + output_total)}")

    return inv_response, input_response, output_response

# Fetch metrics for both tenants
print("\n" + "=" * 80)
print("📊 FETCHING CLOUDWATCH METRICS")
print("=" * 80)

tenant_a_metrics = fetch_and_plot_metrics(
    profile_config['tenant_a_profile_arn'],
    "Tenant A (Marketing)",
    'blue'
)

tenant_b_metrics = fetch_and_plot_metrics(
    profile_config['tenant_b_profile_arn'],
    "Tenant B (Sales)",
    'orange'
)

# Create visualization
print("\n" + "=" * 80)
print("📊 Creating Visualizations")
print("=" * 80)

fig, axes = plt.subplots(2, 3, figsize=(18, 10))
fig.suptitle('Multi-Tenant Application Inference Profile Metrics', fontsize=16, fontweight='bold')

tenants_data = [
    ("Tenant A (Marketing)", tenant_a_metrics, 'blue', 0),
    ("Tenant B (Sales)", tenant_b_metrics, 'orange', 1)
]

for tenant_name, metrics, color, row in tenants_data:
    inv_response, input_response, output_response = metrics

    # Plot Invocations
    inv_data = sorted(inv_response['Datapoints'], key=lambda x: x['Timestamp'])
    if inv_data:
        inv_times = [dp['Timestamp'] for dp in inv_data]
        inv_values = [dp['Sum'] for dp in inv_data]
        axes[row, 0].plot(inv_times, inv_values, marker='o', linewidth=2, color=color)
        axes[row, 0].fill_between(inv_times, inv_values, alpha=0.3, color=color)
    axes[row, 0].set_title(f'{tenant_name}\nInvocations', fontweight='bold')
    axes[row, 0].set_ylabel('Count')
    axes[row, 0].grid(True, alpha=0.3)
    axes[row, 0].tick_params(axis='x', rotation=45)

    # Plot Input Tokens
    input_data = sorted(input_response['Datapoints'], key=lambda x: x['Timestamp'])
    if input_data:
        input_times = [dp['Timestamp'] for dp in input_data]
        input_values = [dp['Sum'] for dp in input_data]
        axes[row, 1].bar(range(len(input_times)), input_values, color=color, alpha=0.7)
        axes[row, 1].set_xticks(range(len(input_times)))
        axes[row, 1].set_xticklabels([t.strftime('%H:%M') for t in input_times], rotation=45)
    axes[row, 1].set_title(f'{tenant_name}\nInput Tokens', fontweight='bold')
    axes[row, 1].set_ylabel('Tokens')
    axes[row, 1].grid(True, alpha=0.3, axis='y')

    # Plot Output Tokens
    output_data = sorted(output_response['Datapoints'], key=lambda x: x['Timestamp'])
    if output_data:
        output_times = [dp['Timestamp'] for dp in output_data]
        output_values = [dp['Sum'] for dp in output_data]
        axes[row, 2].bar(range(len(output_times)), output_values, color=color, alpha=0.7)
        axes[row, 2].set_xticks(range(len(output_times)))
        axes[row, 2].set_xticklabels([t.strftime('%H:%M') for t in output_times], rotation=45)
    axes[row, 2].set_title(f'{tenant_name}\nOutput Tokens', fontweight='bold')
    axes[row, 2].set_ylabel('Tokens')
    axes[row, 2].grid(True, alpha=0.3, axis='y')

plt.tight_layout()
plt.savefig('/workshop/aip_metrics_comparison.png', dpi=150, bbox_inches='tight')
print("✅ Visualization saved to: /workshop/aip_metrics_comparison.png")

# Create a summary comparison
fig2, axes2 = plt.subplots(1, 3, figsize=(15, 5))
fig2.suptitle('Tenant Comparison - Application Inference Profiles', fontsize=14, fontweight='bold')

# Calculate totals
tenant_a_inv = sum(dp['Sum'] for dp in tenant_a_metrics[0]['Datapoints'])
tenant_a_input = sum(dp['Sum'] for dp in tenant_a_metrics[1]['Datapoints'])
tenant_a_output = sum(dp['Sum'] for dp in tenant_a_metrics[2]['Datapoints'])

tenant_b_inv = sum(dp['Sum'] for dp in tenant_b_metrics[0]['Datapoints'])
tenant_b_input = sum(dp['Sum'] for dp in tenant_b_metrics[1]['Datapoints'])
tenant_b_output = sum(dp['Sum'] for dp in tenant_b_metrics[2]['Datapoints'])

# Plot comparisons
tenants = ['Tenant A\n(Marketing)', 'Tenant B\n(Sales)']
colors = ['blue', 'orange']

axes2[0].bar(tenants, [tenant_a_inv, tenant_b_inv], color=colors, alpha=0.7)
axes2[0].set_title('Total Invocations', fontweight='bold')
axes2[0].set_ylabel('Count')
axes2[0].grid(True, alpha=0.3, axis='y')

axes2[1].bar(tenants, [tenant_a_input, tenant_b_input], color=colors, alpha=0.7)
axes2[1].set_title('Total Input Tokens', fontweight='bold')
axes2[1].set_ylabel('Tokens')
axes2[1].grid(True, alpha=0.3, axis='y')

axes2[2].bar(tenants, [tenant_a_output, tenant_b_output], color=colors, alpha=0.7)
axes2[2].set_title('Total Output Tokens', fontweight='bold')
axes2[2].set_ylabel('Tokens')
axes2[2].grid(True, alpha=0.3, axis='y')

plt.tight_layout()
plt.savefig('/workshop/aip_tenant_comparison.png', dpi=150, bbox_inches='tight')
print("✅ Comparison chart saved to: /workshop/aip_tenant_comparison.png")

print("\n" + "=" * 80)
print("🎉 SUCCESS - Metrics Retrieved and Visualized!")
print("=" * 80)

print(f"""
📊 Summary:
   Tenant A (Marketing): {int(tenant_a_inv)} invocations, {int(tenant_a_input + tenant_a_output)} total tokens
   Tenant B (Sales): {int(tenant_b_inv)} invocations, {int(tenant_b_input + tenant_b_output)} total tokens

📁 Generated Files:
   • /workshop/aip_metrics_comparison.png (detailed time-series)
   • /workshop/aip_tenant_comparison.png (summary comparison)

✅ Benefits Achieved:
   • Separate tracking per tenant ✓
   • Independent CloudWatch metrics ✓
   • Tag-based cost allocation ✓
   • Isolated monitoring and alerting ✓
""")

print("=" * 80)
