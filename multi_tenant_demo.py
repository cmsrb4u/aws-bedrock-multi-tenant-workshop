import boto3
import json
import time
import datetime
from datetime import timedelta
import matplotlib.pyplot as plt
from lab_helpers.config import Region, ModelId

# Create CloudWatch client

def fetch_metrices(Region, ModelId, Period=300, Timedelta=60):

    cloudwatch = boto3.client('cloudwatch', region_name=Region)

    # Get metrics for the last hour
    #end_time = datetime.utcnow()
    end_time=datetime.datetime.now(datetime.UTC)
    start_time = end_time - timedelta(minutes=60)

    # Get Bedrock invocation metrics
    #Invocations - Number of API calls
    response = cloudwatch.get_metric_statistics(
        Namespace='AWS/Bedrock',
        MetricName='Invocations',
        Dimensions=[
            {
                'Name': 'ModelId',
                'Value': ModelId
            }
        ],
        StartTime=start_time,
        EndTime=end_time,
        Period=60,  # 1 minute
        Statistics=['Sum']
    )

    print("Invocation Count:")
    for datapoint in response['Datapoints']:
        print(f"Time: {datapoint['Timestamp']}, Count: {datapoint['Sum']}")

    # Get input token metrics
    # InputTokenCount - Total input tokens processed

    input_token_response = cloudwatch.get_metric_statistics(
        Namespace='AWS/Bedrock',
        MetricName='InputTokenCount',
        Dimensions=[
            {
                'Name': 'ModelId',
                'Value': ModelId
            }
        ],
        StartTime=start_time,
        EndTime=end_time,
        Period=60,
        Statistics=['Sum']
    )

    print("\nInput Token Count:")
    for datapoint in input_token_response['Datapoints']:
        print(f"Time: {datapoint['Timestamp']}, Tokens: {datapoint['Sum']}")

    # Get output token metrics
    #OutputTokenCount - Total output tokens generated
    output_token_response = cloudwatch.get_metric_statistics(
        Namespace='AWS/Bedrock',
        MetricName='OutputTokenCount',
        Dimensions=[
            {
                'Name': 'ModelId',
                'Value': ModelId
            }
        ],
        StartTime=start_time,
        EndTime=end_time,
        Period=60,
        Statistics=['Sum']
    )

    print("\nOutput Token Count:")
    for datapoint in output_token_response['Datapoints']:
        print(f"Time: {datapoint['Timestamp']}, Tokens: {datapoint['Sum']}")

    return response,input_token_response,output_token_response


# Simulate multi-tenant requests using System Inference Profile
# In a real multi-tenant app, these would come from different customers

# Define prompts for two tenants (same as Lab 03 context)
TENANT_PROMPTS = {
    "tenant_a": "Generate a brief marketing campaign for a B2B SaaS DevOps automation platform targeting CTOs.",
    "tenant_b": "Generate a brief marketing campaign for a B2C sustainable fashion collection targeting millennials."
}

# Create Bedrock runtime client
bedrock = boto3.client('bedrock-runtime', region_name=Region)

print("🔄 Simulating requests from multiple tenants using System Inference Profile...")
print("=" * 80)

# Make inference calls for both tenants
for idx, (tenant_id, prompt) in enumerate(TENANT_PROMPTS.items()):
    print(f"\n🏢 Request from {tenant_id.upper()}:")
    print(f"Prompt: {prompt[:80]}...")

    body=json.dumps({
        "messages": [{
            "role": "user",
            "content": [{"type": "text", "text": prompt}]
        }],
        "max_tokens": 1024,
        "anthropic_version": "bedrock-2023-05-31"
    })

    # THE PROBLEM: Both tenants use the SAME modelId!
    response = bedrock.invoke_model(
        modelId=ModelId.DEFAULT,  # ❌ Same for all tenants - no way to distinguish!
        body=body
    )

    response_body = json.loads(response['body'].read())

    output_text = response_body['content'][0]['text']
    input_tokens = response_body['usage']['input_tokens']
    output_tokens = response_body['usage']['output_tokens']
    total_tokens = input_tokens + output_tokens

    print(f"✅ Response received")
    print(f"   Input tokens: {input_tokens}")
    print(f"   Output tokens: {output_tokens}")
    print(f"   Response preview: {output_text[:100]}...")

    # Add 1-minute gap between tenant requests for CloudWatch visualization
    if idx == 0:  # After first tenant only
        print(f"\n⏳ Waiting 80 seconds before next request (for CloudWatch separation)...")
        time.sleep(60)
        print(f"✅ Wait complete - proceeding with Tenant B request")

print("\n" + "=" * 80)
print("THE PROBLEM: Both tenant requests used the SAME modelId!")
print(f"   ModelId: {ModelId.DEFAULT}")
print("   All usage will be aggregated in CloudWatch - no way to separate!")
print("=" * 80)

# Fetch CloudWatch metrics to demonstrate the aggregation problem
print("\n" + "=" * 80)
print("📊 Fetching CloudWatch Metrics (last 60 minutes)...")
print("=" * 80)
fetch_metrices(Region, ModelId.DEFAULT)

# Check CloudWatch metrics After campaign generation
print("\n⏳ Waiting 60 seconds for CloudWatch metrics to propagate...")
time.sleep(60)
print("✅ Wait complete - proceeding with metrics monitoring")

# Create graphs
response, input_token_response, output_token_response = fetch_metrices(Region, ModelId.DEFAULT, 60, 60)

fig, axes = plt.subplots(3, 1, figsize=(12, 10))

# Plot Invocations
inv_data = sorted(response['Datapoints'], key=lambda x: x['Timestamp'])
inv_times = [dp['Timestamp'] for dp in inv_data]
inv_values = [dp['Sum'] for dp in inv_data]
axes[0].plot(inv_times, inv_values, marker='o', linewidth=2)  # Added linewidth
axes[0].set_title('Invocations over 1 hour')
axes[0].set_ylabel('Count')
axes[0].grid(True)

# Plot Input Tokens
input_data = sorted(input_token_response['Datapoints'], key=lambda x: x['Timestamp'])
input_times = [dp['Timestamp'] for dp in input_data]
input_values = [dp['Sum'] for dp in input_data]
axes[1].plot(input_times, input_values, marker='o', color='green', linewidth=2)  # Added linewidth
axes[1].set_title('Input Token Count over 1 hour')
axes[1].set_ylabel('Tokens')
axes[1].grid(True)

# Plot Output Tokens
output_data = sorted(output_token_response['Datapoints'], key=lambda x: x['Timestamp'])
output_times = [dp['Timestamp'] for dp in output_data]
output_values = [dp['Sum'] for dp in output_data]
axes[2].plot(output_times, output_values, marker='o', color='red', linewidth=2)  # Added linewidth
axes[2].set_title('Output Token Count over 1 hour')
axes[2].set_ylabel('Tokens')
axes[2].grid(True)

plt.tight_layout()
plt.savefig('/workshop/cloudwatch_metrics.png', dpi=150, bbox_inches='tight')
print("\n📊 Graphs saved to /workshop/cloudwatch_metrics.png")
plt.show()
