#!/usr/bin/env python3
"""
Continuously generate metrics for CloudWatch dashboard
No user input required - runs automatically
"""

import boto3
import json
import time
import random
from datetime import datetime

# Configuration
REGION = "us-west-2"
TENANT_A_PROFILE = "arn:aws:bedrock:us-west-2:899950533801:application-inference-profile/5gematyf83m0"
TENANT_B_PROFILE = "arn:aws:bedrock:us-west-2:899950533801:application-inference-profile/yku79b5wumnr"

# Initialize Bedrock client
bedrock = boto3.client('bedrock-runtime', region_name=REGION)

def invoke_model(profile_arn, prompt, tenant_name, max_tokens=50):
    """Make an API call to generate metrics"""

    request_body = {
        "anthropic_version": "bedrock-2023-05-31",
        "messages": [
            {
                "role": "user",
                "content": prompt
            }
        ],
        "max_tokens": max_tokens,
        "temperature": 0.5
    }

    try:
        response = bedrock.invoke_model(
            modelId=profile_arn,
            body=json.dumps(request_body),
            contentType='application/json',
            accept='application/json'
        )

        response_body = json.loads(response['body'].read())
        usage = response_body.get('usage', {})

        input_tokens = usage.get('input_tokens', 0)
        output_tokens = usage.get('output_tokens', 0)
        total_tokens = input_tokens + output_tokens

        return input_tokens, output_tokens, total_tokens

    except Exception as e:
        print(f"  ❌ Error: {str(e)[:50]}")
        return 0, 0, 0

def generate_continuous_metrics(iterations=20):
    """Generate continuous metrics for both tenants"""

    print("\n" + "="*70)
    print("🔄 CONTINUOUS METRIC GENERATION FOR CLOUDWATCH")
    print("="*70)
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Iterations: {iterations}")
    print()

    # Quick prompts for rapid generation
    quick_prompts = [
        "Count to 5",
        "What's 10+10?",
        "Name a color",
        "Say hello",
        "Write one word",
        "Yes or no?",
        "True or false?",
        "Pick a number",
        "Name a fruit",
        "Day of week?",
        "Current season?",
        "Hot or cold?",
        "Up or down?",
        "Left or right?",
        "Fast or slow?"
    ]

    # Track totals
    totals = {
        "A": {"input": 0, "output": 0, "calls": 0, "name": "Marketing"},
        "B": {"input": 0, "output": 0, "calls": 0, "name": "Sales"}
    }

    print("Generating metrics", end="")

    for i in range(iterations):
        # Alternate between tenants
        if i % 2 == 0:
            tenant = "A"
            profile = TENANT_A_PROFILE
        else:
            tenant = "B"
            profile = TENANT_B_PROFILE

        prompt = random.choice(quick_prompts)
        max_tokens = random.randint(10, 30)  # Keep responses short

        input_t, output_t, total_t = invoke_model(profile, prompt, f"Tenant {tenant}", max_tokens)

        if total_t > 0:
            totals[tenant]["input"] += input_t
            totals[tenant]["output"] += output_t
            totals[tenant]["calls"] += 1
            print(".", end="", flush=True)
        else:
            print("x", end="", flush=True)

        # Small delay
        time.sleep(random.uniform(0.3, 0.7))

        # Progress indicator every 10 iterations
        if (i + 1) % 10 == 0:
            print(f" [{i+1}/{iterations}]", end="", flush=True)

    print(" Done!")

    # Print summary
    print("\n" + "="*70)
    print("📊 METRICS GENERATION SUMMARY")
    print("="*70)

    grand_total_tokens = 0
    grand_total_calls = 0

    for tenant_id, stats in totals.items():
        total_tokens = stats["input"] + stats["output"]
        grand_total_tokens += total_tokens
        grand_total_calls += stats["calls"]

        print(f"\nTenant {tenant_id} ({stats['name']}):")
        print(f"  • Successful API Calls: {stats['calls']}")
        print(f"  • Input Tokens: {stats['input']:,}")
        print(f"  • Output Tokens: {stats['output']:,}")
        print(f"  • Total Tokens: {total_tokens:,}")

        # Cost estimation
        if total_tokens > 0:
            input_cost = (stats["input"] / 1_000_000) * 3.00
            output_cost = (stats["output"] / 1_000_000) * 15.00
            total_cost = input_cost + output_cost
            print(f"  • Estimated Cost: ${total_cost:.4f}")

    print(f"\n📈 Grand Total: {grand_total_tokens:,} tokens across {grand_total_calls} successful API calls")

    # Calculate metrics rate
    if grand_total_calls > 0:
        print(f"\n⚡ Performance:")
        print(f"  • Average tokens per call: {grand_total_tokens // grand_total_calls}")
        print(f"  • Calls per minute: ~{(grand_total_calls / (iterations * 0.5)):.1f}")

    print("\n" + "="*70)
    print("✅ CONTINUOUS GENERATION COMPLETE")
    print("="*70)

if __name__ == "__main__":
    # Run 20 iterations automatically
    generate_continuous_metrics(20)

    print("\n📊 CloudWatch Dashboard:")
    print(f"https://console.aws.amazon.com/cloudwatch/home?region={REGION}#dashboards:name=CCWB-Quota-Monitoring")
    print("\n⏱️ Metrics appear in CloudWatch within 1-2 minutes")
    print("   The dashboard will auto-refresh every 5 minutes")