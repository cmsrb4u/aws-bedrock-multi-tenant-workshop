#!/usr/bin/env python3
"""
Generate usage metrics for both tenants by making API calls
This will populate the CloudWatch dashboard with real data
"""

import boto3
import json
import time
from datetime import datetime
import random

# Configuration
REGION = "us-west-2"
TENANT_A_PROFILE = "arn:aws:bedrock:us-west-2:899950533801:application-inference-profile/5gematyf83m0"
TENANT_B_PROFILE = "arn:aws:bedrock:us-west-2:899950533801:application-inference-profile/yku79b5wumnr"

# Initialize Bedrock client
bedrock = boto3.client('bedrock-runtime', region_name=REGION)

def invoke_model(profile_arn, prompt, tenant_name, max_tokens=100):
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
        "temperature": 0.7
    }

    try:
        print(f"  Invoking {tenant_name}...", end="")

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

        print(f" ✅ {input_tokens} in / {output_tokens} out = {total_tokens} total")

        # Extract response text
        if 'content' in response_body and response_body['content']:
            content = response_body['content'][0].get('text', '')[:50]
            print(f"     Response: '{content}...'")

        return input_tokens, output_tokens

    except Exception as e:
        print(f" ❌ Error: {str(e)[:50]}")
        return 0, 0

def generate_diverse_prompts():
    """Generate various prompts to simulate different use cases"""

    prompts = [
        # Marketing Team (Tenant A) typical use cases
        {
            "tenant": "A",
            "name": "Marketing",
            "prompts": [
                ("Write a catchy tagline for a new eco-friendly product", 50),
                ("Create 5 social media post ideas about sustainability", 150),
                ("Draft an email subject line for a product launch", 30),
                ("Generate hashtags for an Instagram campaign", 40),
                ("Write a brief product description for an online store", 100),
                ("Create a call-to-action for a landing page", 25),
                ("Suggest blog post titles about digital marketing", 80),
                ("Write a customer testimonial template", 60),
            ]
        },
        # Sales Team (Tenant B) typical use cases
        {
            "tenant": "B",
            "name": "Sales",
            "prompts": [
                ("Write a follow-up email after a sales call", 100),
                ("Create an elevator pitch for our product", 80),
                ("Draft a proposal executive summary", 150),
                ("Generate qualifying questions for prospects", 60),
                ("Write a cold outreach LinkedIn message", 50),
                ("Create objection handling responses", 120),
                ("Draft a meeting agenda for a sales demo", 70),
                ("Write a thank you note after closing a deal", 40),
            ]
        }
    ]

    return prompts

def run_tenant_simulations():
    """Run multiple API calls for both tenants"""

    print("\n" + "="*70)
    print("🚀 GENERATING TENANT USAGE METRICS FOR CLOUDWATCH DASHBOARD")
    print("="*70)
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Region: {REGION}")
    print()

    # Get prompts for each tenant
    tenant_configs = generate_diverse_prompts()

    # Track totals
    totals = {
        "A": {"input": 0, "output": 0, "calls": 0},
        "B": {"input": 0, "output": 0, "calls": 0}
    }

    # Run simulations
    for config in tenant_configs:
        tenant = config["tenant"]
        tenant_name = config["name"]
        profile = TENANT_A_PROFILE if tenant == "A" else TENANT_B_PROFILE

        print(f"\n📊 Tenant {tenant} ({tenant_name}) - Profile: {profile.split('/')[-1]}")
        print("-" * 60)

        for prompt, max_tokens in config["prompts"]:
            print(f"\n• Prompt: '{prompt[:40]}...'")
            print(f"  Max tokens: {max_tokens}")

            input_t, output_t = invoke_model(profile, prompt, f"Tenant {tenant}", max_tokens)

            if input_t > 0:
                totals[tenant]["input"] += input_t
                totals[tenant]["output"] += output_t
                totals[tenant]["calls"] += 1

            # Small delay between calls
            time.sleep(random.uniform(0.5, 1.5))

    # Print summary
    print("\n" + "="*70)
    print("📈 SUMMARY OF GENERATED METRICS")
    print("="*70)

    for tenant in ["A", "B"]:
        stats = totals[tenant]
        total_tokens = stats["input"] + stats["output"]
        tenant_name = "Marketing" if tenant == "A" else "Sales"

        print(f"\nTenant {tenant} ({tenant_name}):")
        print(f"  • API Calls: {stats['calls']}")
        print(f"  • Input Tokens: {stats['input']:,}")
        print(f"  • Output Tokens: {stats['output']:,}")
        print(f"  • Total Tokens: {total_tokens:,}")

        # Cost estimation (Claude Sonnet pricing)
        input_cost = (stats["input"] / 1_000_000) * 3.00
        output_cost = (stats["output"] / 1_000_000) * 15.00
        total_cost = input_cost + output_cost
        print(f"  • Estimated Cost: ${total_cost:.4f}")

    grand_total = sum(totals[t]["input"] + totals[t]["output"] for t in ["A", "B"])
    print(f"\n📊 Grand Total: {grand_total:,} tokens across {sum(totals[t]['calls'] for t in ['A', 'B'])} API calls")

    print("\n" + "="*70)
    print("✅ METRICS GENERATED SUCCESSFULLY")
    print("="*70)
    print("\n📊 View your dashboard at:")
    print(f"https://console.aws.amazon.com/cloudwatch/home?region={REGION}#dashboards:name=CCWB-Quota-Monitoring")
    print("\n⏱️ Note: Metrics may take 1-2 minutes to appear in CloudWatch")
    print("    Refresh your dashboard to see the latest data")

def run_continuous_simulation(duration_minutes=5):
    """Run continuous simulation for specified duration"""

    print(f"\n🔄 Running continuous simulation for {duration_minutes} minutes...")
    print("Press Ctrl+C to stop early\n")

    end_time = time.time() + (duration_minutes * 60)
    iteration = 1

    try:
        while time.time() < end_time:
            print(f"\n--- Iteration {iteration} ---")

            # Randomly select a tenant
            tenant = random.choice(["A", "B"])
            tenant_name = "Marketing" if tenant == "A" else "Sales"
            profile = TENANT_A_PROFILE if tenant == "A" else TENANT_B_PROFILE

            # Select a random prompt
            prompts = [
                "Tell me a short joke",
                "What's the weather like?",
                "Explain quantum computing in one sentence",
                "Write a haiku about clouds",
                "Give me a motivational quote",
                "What's 2+2?",
                "Describe the color blue",
                "Name three fruits"
            ]

            prompt = random.choice(prompts)
            max_tokens = random.randint(20, 100)

            print(f"Tenant {tenant} ({tenant_name}): '{prompt}'")
            invoke_model(profile, prompt, f"Tenant {tenant}", max_tokens)

            # Wait before next call
            wait_time = random.uniform(5, 15)
            print(f"Waiting {wait_time:.1f} seconds...")
            time.sleep(wait_time)

            iteration += 1

    except KeyboardInterrupt:
        print("\n\n⏹️ Simulation stopped by user")

    print("\n✅ Continuous simulation complete")
    print(f"   Completed {iteration-1} iterations")

if __name__ == "__main__":
    # Run the main simulation
    run_tenant_simulations()

    # Ask if user wants continuous simulation
    print("\n" + "-"*70)
    response = input("\nWould you like to run continuous simulation for more data? (y/n): ")

    if response.lower() == 'y':
        try:
            minutes = int(input("How many minutes? (1-10): "))
            minutes = max(1, min(10, minutes))  # Clamp between 1 and 10
            run_continuous_simulation(minutes)
        except ValueError:
            print("Invalid input, skipping continuous simulation")

    print("\n🎉 All done! Check your CloudWatch dashboard for the metrics.")