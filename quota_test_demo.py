#!/usr/bin/env python3
"""
Quota Monitoring Demo with AIP Integration
Demonstrates quota functionality with minimal limits and actual Bedrock calls
"""

import boto3
import json
import time
from datetime import datetime
import subprocess
import sys

# Configuration
REGION = "us-west-2"
TENANT_A_PROFILE = "arn:aws:bedrock:us-west-2:899950533801:application-inference-profile/5gematyf83m0"
TENANT_B_PROFILE = "arn:aws:bedrock:us-west-2:899950533801:application-inference-profile/yku79b5wumnr"

# Test users mapped to tenants
USER_TENANT_MAP = {
    "alice@marketing.com": TENANT_A_PROFILE,  # Marketing team
    "bob@sales.com": TENANT_B_PROFILE,        # Sales team
    "charlie@marketing.com": TENANT_A_PROFILE  # Marketing team
}

def setup_minimal_quotas():
    """Set up minimal quotas for testing"""
    print("🔧 Setting up minimal quota limits for testing...")
    print("-" * 60)

    # Set very low limits to trigger quota warnings/blocks quickly
    commands = [
        # Default policy - 1000 tokens monthly, 100 daily
        ("ccwb quota set-default --monthly-limit 1000 --daily-limit 100 --enforcement alert",
         "Default policy: 1,000 monthly / 100 daily (alert)"),

        # Marketing team (Tenant A users) - 5000 tokens monthly, 500 daily
        ("ccwb quota set-group marketing --monthly-limit 5000 --daily-limit 500 --enforcement alert",
         "Marketing group: 5,000 monthly / 500 daily (alert)"),

        # Sales team (Tenant B users) - 3000 tokens monthly, 300 daily
        ("ccwb quota set-group sales --monthly-limit 3000 --daily-limit 300 --enforcement block",
         "Sales group: 3,000 monthly / 300 daily (BLOCK mode)"),

        # Power user - higher limits
        ("ccwb quota set-user alice@marketing.com --monthly-limit 10000 --daily-limit 1000 --enforcement alert",
         "Alice (power user): 10,000 monthly / 1,000 daily (alert)")
    ]

    for cmd, description in commands:
        print(f"  ✅ {description}")
        try:
            result = subprocess.run(
                f"source venv/bin/activate && {cmd}",
                shell=True,
                capture_output=True,
                text=True,
                executable='/bin/bash'
            )
            if result.returncode != 0 and "already exists" not in result.stderr:
                print(f"    ⚠️ Warning: {result.stderr[:100]}")
        except Exception as e:
            print(f"    ⚠️ Error setting quota: {e}")

    print()

def check_user_quota(user_email):
    """Check current quota status for a user"""
    try:
        result = subprocess.run(
            f"source venv/bin/activate && ccwb quota usage {user_email}",
            shell=True,
            capture_output=True,
            text=True,
            executable='/bin/bash'
        )
        return result.stdout
    except:
        return "Unable to check quota"

def estimate_tokens(text):
    """Rough estimate of token count (1 token ≈ 4 characters)"""
    return len(text) // 4

def call_bedrock_with_aip(user_email, prompt, profile_arn):
    """Make a Bedrock API call using Application Inference Profile"""

    bedrock = boto3.client('bedrock-runtime', region_name=REGION)

    # Create a simple request
    request_body = {
        "anthropic_version": "bedrock-2023-05-31",
        "messages": [
            {
                "role": "user",
                "content": prompt
            }
        ],
        "max_tokens": 50,  # Keep response small for testing
        "temperature": 0
    }

    try:
        print(f"\n📤 {user_email} sending request...")
        print(f"   Profile: {profile_arn.split('/')[-1]}")
        print(f"   Prompt: '{prompt[:50]}...'")

        # Estimate input tokens
        input_tokens = estimate_tokens(json.dumps(request_body))
        print(f"   Estimated input tokens: ~{input_tokens}")

        # Make the API call
        response = bedrock.invoke_model(
            modelId=profile_arn,
            body=json.dumps(request_body),
            contentType='application/json',
            accept='application/json'
        )

        response_body = json.loads(response['body'].read())

        # Extract token usage from response
        usage = response_body.get('usage', {})
        actual_input_tokens = usage.get('input_tokens', 0)
        actual_output_tokens = usage.get('output_tokens', 0)
        total_tokens = actual_input_tokens + actual_output_tokens

        print(f"   ✅ Response received!")
        print(f"   Actual tokens: {actual_input_tokens} in / {actual_output_tokens} out = {total_tokens} total")

        # Show response preview
        if 'content' in response_body and response_body['content']:
            content = response_body['content'][0].get('text', '')[:100]
            print(f"   Response: '{content}...'")

        return total_tokens, actual_input_tokens, actual_output_tokens

    except Exception as e:
        print(f"   ❌ Error: {str(e)[:100]}")
        return 0, 0, 0

def simulate_quota_tracking(user_email, tokens_used, current_totals):
    """Simulate how quota tracking would work"""

    current_totals['daily'] += tokens_used
    current_totals['monthly'] += tokens_used

    print(f"\n📊 Quota Impact for {user_email}:")
    print(f"   Daily total: {current_totals['daily']} tokens")
    print(f"   Monthly total: {current_totals['monthly']} tokens")

    # Check quota status
    quota_status = check_user_quota(user_email)
    if quota_status:
        # Parse and display key info
        lines = quota_status.split('\n')
        for line in lines:
            if 'Monthly' in line or 'Daily' in line or 'Policy' in line or 'Enforcement' in line:
                print(f"   {line.strip()}")

    return current_totals

def run_demo():
    """Run the full quota demonstration"""

    print("\n" + "="*70)
    print("🚀 CCWB QUOTA MONITORING DEMO WITH APPLICATION INFERENCE PROFILES")
    print("="*70)

    # Step 1: Set up minimal quotas
    setup_minimal_quotas()

    # Step 2: Show initial quota status
    print("\n📋 Initial Quota Status:")
    print("-" * 60)

    users = ["alice@marketing.com", "bob@sales.com", "charlie@marketing.com"]
    for user in users:
        print(f"\n{user}:")
        subprocess.run(
            f"source venv/bin/activate && ccwb quota show {user}",
            shell=True,
            executable='/bin/bash'
        )

    # Step 3: Simulate API calls with quota tracking
    print("\n" + "="*70)
    print("🎯 SIMULATING API CALLS WITH QUOTA MONITORING")
    print("="*70)

    # Track usage for each user
    user_totals = {
        "alice@marketing.com": {"daily": 0, "monthly": 0},
        "bob@sales.com": {"daily": 0, "monthly": 0},
        "charlie@marketing.com": {"daily": 0, "monthly": 0}
    }

    # Test scenarios
    test_scenarios = [
        {
            "user": "alice@marketing.com",
            "prompt": "Count to 3",
            "description": "Small request from power user"
        },
        {
            "user": "bob@sales.com",
            "prompt": "What is 2+2?",
            "description": "Small request from sales (BLOCK mode group)"
        },
        {
            "user": "charlie@marketing.com",
            "prompt": "Say hello",
            "description": "Small request from marketing user"
        },
        {
            "user": "alice@marketing.com",
            "prompt": "Write a very long detailed explanation of quantum computing including its history, principles, applications, and future prospects",
            "description": "Large request to approach limits"
        },
        {
            "user": "bob@sales.com",
            "prompt": "Explain machine learning in detail with examples",
            "description": "Request that might trigger BLOCK mode"
        }
    ]

    for i, scenario in enumerate(test_scenarios, 1):
        print(f"\n{'='*60}")
        print(f"📌 Scenario {i}: {scenario['description']}")
        print(f"{'='*60}")

        user = scenario['user']
        profile = USER_TENANT_MAP.get(user, TENANT_A_PROFILE)

        # Make the API call
        total, input_t, output_t = call_bedrock_with_aip(
            user,
            scenario['prompt'],
            profile
        )

        # Update and check quotas
        if total > 0:
            user_totals[user] = simulate_quota_tracking(
                user,
                total,
                user_totals[user]
            )

        # Check if we should stop (in real system, BLOCK mode would prevent the call)
        if user_totals[user]['daily'] > 300 and "bob@sales.com" in user:
            print(f"\n   🚫 WARNING: {user} has exceeded daily limit!")
            print(f"   In production, BLOCK mode would prevent further calls")

        time.sleep(1)  # Small delay between calls

    # Step 4: Final quota report
    print("\n" + "="*70)
    print("📊 FINAL QUOTA USAGE REPORT")
    print("="*70)

    for user in users:
        print(f"\n{'='*40}")
        print(f"User: {user}")
        print(f"{'='*40}")
        subprocess.run(
            f"source venv/bin/activate && ccwb quota usage {user}",
            shell=True,
            executable='/bin/bash'
        )

        # Show what would happen in production
        totals = user_totals.get(user, {"daily": 0, "monthly": 0})
        if "bob@sales.com" in user and totals['daily'] > 300:
            print("\n🚫 PRODUCTION BEHAVIOR: User would be BLOCKED from further API calls")
            print("   (Sales group has enforcement mode = BLOCK)")
        elif totals['daily'] > 500 and "marketing" in user:
            print("\n⚠️ PRODUCTION BEHAVIOR: User would receive ALERT notifications")
            print("   (Marketing group has enforcement mode = ALERT)")

    print("\n" + "="*70)
    print("✅ DEMONSTRATION COMPLETE")
    print("="*70)
    print("\nKey Takeaways:")
    print("• Quotas are checked before each Bedrock API call")
    print("• ALERT mode: Warns but allows continued access")
    print("• BLOCK mode: Prevents API calls when limit exceeded")
    print("• Token usage is tracked in real-time via DynamoDB")
    print("• Application Inference Profiles enable per-tenant tracking")

if __name__ == "__main__":
    run_demo()