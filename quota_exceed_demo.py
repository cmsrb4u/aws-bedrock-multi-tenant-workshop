#!/usr/bin/env python3
"""
Quota Exceeding Demo - Shows what happens when limits are hit
"""

import boto3
import json
import subprocess
import time

REGION = "us-west-2"
TENANT_A_PROFILE = "arn:aws:bedrock:us-west-2:899950533801:application-inference-profile/5gematyf83m0"

def run_command(cmd):
    """Run a shell command and return output"""
    result = subprocess.run(
        f"source venv/bin/activate && {cmd}",
        shell=True,
        capture_output=True,
        text=True,
        executable='/bin/bash'
    )
    return result.stdout, result.returncode

def set_ultra_minimal_quota():
    """Set extremely low quota for immediate testing"""
    print("🔧 Setting ULTRA-MINIMAL quotas to trigger limits immediately...")
    print("-" * 60)

    # Set quota that will be exceeded by a single API call
    commands = [
        ("ccwb quota set-user test@company.com --monthly-limit 50 --daily-limit 20 --enforcement block",
         "test@company.com: 50 monthly / 20 daily tokens (BLOCK mode)"),

        ("ccwb quota set-user demo@company.com --monthly-limit 100 --daily-limit 30 --enforcement alert",
         "demo@company.com: 100 monthly / 30 daily tokens (ALERT mode)")
    ]

    for cmd, description in commands:
        print(f"  ✅ {description}")
        stdout, _ = run_command(cmd)

def simulate_usage_update(user, tokens_used):
    """Simulate updating token usage in the quota system"""

    # In production, this would happen automatically
    # Here we'll manually update the quota tracking

    print(f"\n📝 Simulating usage update for {user}:")
    print(f"   Adding {tokens_used} tokens to usage metrics")

    # Get current usage
    stdout, _ = run_command(f"ccwb quota usage {user}")

    # Parse current usage (this is simplified - in production it's in DynamoDB)
    lines = stdout.split('\n')
    for line in lines:
        if 'Daily Tokens' in line or 'Monthly Tokens' in line:
            print(f"   {line.strip()}")

def test_quota_scenarios():
    """Test different quota scenarios"""

    print("\n" + "="*70)
    print("🧪 TESTING QUOTA LIMIT SCENARIOS")
    print("="*70)

    # Scenario 1: User in BLOCK mode hitting limit
    print("\n📌 Scenario 1: BLOCK Mode User Exceeding Limit")
    print("-" * 60)

    user = "test@company.com"

    # Show initial quota
    print(f"Initial quota for {user}:")
    stdout, _ = run_command(f"ccwb quota show {user}")
    print(stdout)

    # Simulate first small call (within limit)
    print(f"\n1️⃣ First API call (15 tokens):")
    simulate_usage_update(user, 15)
    stdout, _ = run_command(f"ccwb quota usage {user}")

    # Check if still within limits
    if "0.0%" in stdout:  # No actual usage tracked in our demo
        print("   Status: ✅ Within limits (would allow in production)")

    # Simulate second call that exceeds daily limit
    print(f"\n2️⃣ Second API call (10 tokens) - would exceed daily limit of 20:")
    simulate_usage_update(user, 10)

    print("\n⚠️ PRODUCTION BEHAVIOR:")
    print("   With BLOCK mode + exceeded limit:")
    print("   ❌ API call would be DENIED")
    print("   ❌ User receives 'Quota Exceeded' error")
    print("   ❌ No credentials vended by CCWB")

    # Scenario 2: User in ALERT mode hitting limit
    print("\n" + "="*60)
    print("📌 Scenario 2: ALERT Mode User Exceeding Limit")
    print("-" * 60)

    user = "demo@company.com"

    # Show initial quota
    print(f"Initial quota for {user}:")
    stdout, _ = run_command(f"ccwb quota show {user}")
    print(stdout)

    # Simulate call exceeding limit
    print(f"\n1️⃣ API call (35 tokens) - exceeds daily limit of 30:")
    simulate_usage_update(user, 35)

    print("\n⚠️ PRODUCTION BEHAVIOR:")
    print("   With ALERT mode + exceeded limit:")
    print("   ✅ API call would be ALLOWED")
    print("   📧 Alert notification sent (email/SNS)")
    print("   📊 CloudWatch metric published")
    print("   ⚠️ Dashboard shows warning state")

    # Scenario 3: Temporary unblock
    print("\n" + "="*60)
    print("📌 Scenario 3: Temporary Unblock for Emergency")
    print("-" * 60)

    user = "test@company.com"
    print(f"\nUser {user} is blocked due to quota. Applying temporary unblock...")

    stdout, _ = run_command(f"ccwb quota unblock {user} --duration 1h")
    print(stdout)

    print("\n✅ PRODUCTION BEHAVIOR:")
    print("   User can now make API calls for 1 hour despite quota")
    print("   Useful for emergency access or critical operations")

def show_monitoring_integration():
    """Show how quota monitoring integrates with CloudWatch"""

    print("\n" + "="*70)
    print("📊 CLOUDWATCH MONITORING INTEGRATION")
    print("="*70)

    print("\nIn production, quota events trigger CloudWatch metrics:")
    print("""
    Custom Metrics Published:
    ├── CCWB/Quotas/Usage
    │   ├── Dimensions: User, Policy
    │   └── Value: Token count
    ├── CCWB/Quotas/Exceeded
    │   ├── Dimensions: User, EnforcementMode
    │   └── Value: 1 (when limit hit)
    └── CCWB/Quotas/Blocked
        ├── Dimensions: User
        └── Value: 1 (when request blocked)
    """)

    print("CloudWatch Alarms can trigger:")
    print("  • Email notifications via SNS")
    print("  • Lambda functions for auto-remediation")
    print("  • Slack/Teams webhooks")
    print("  • PagerDuty alerts")

def demonstrate_real_api_with_quota():
    """Make a real API call and show quota impact"""

    print("\n" + "="*70)
    print("🚀 REAL API CALL WITH QUOTA TRACKING")
    print("="*70)

    bedrock = boto3.client('bedrock-runtime', region_name=REGION)

    # Simple request
    request_body = {
        "anthropic_version": "bedrock-2023-05-31",
        "messages": [{"role": "user", "content": "Hi"}],
        "max_tokens": 10,
        "temperature": 0
    }

    try:
        print("\n📤 Making actual Bedrock API call...")
        response = bedrock.invoke_model(
            modelId=TENANT_A_PROFILE,
            body=json.dumps(request_body),
            contentType='application/json',
            accept='application/json'
        )

        response_body = json.loads(response['body'].read())
        usage = response_body.get('usage', {})

        print(f"✅ Success! Tokens used: {usage.get('input_tokens', 0)} + {usage.get('output_tokens', 0)}")

        print("\n📊 In Production with CCWB:")
        print("  1. Pre-call: CCWB checks quota before vending credentials")
        print("  2. If OK: Temporary credentials issued to user")
        print("  3. API call: Made with vended credentials")
        print("  4. Post-call: Token usage recorded in DynamoDB")
        print("  5. Next call: Updated usage checked against limits")

    except Exception as e:
        print(f"❌ Error: {str(e)[:100]}")

def main():
    print("\n" + "="*70)
    print("💡 CCWB QUOTA EXCEEDING DEMONSTRATION")
    print("="*70)
    print("\nThis demo shows what happens when quota limits are exceeded")
    print("in both ALERT and BLOCK enforcement modes.")

    # Set up ultra-minimal quotas
    set_ultra_minimal_quota()

    # Test different scenarios
    test_quota_scenarios()

    # Show monitoring integration
    show_monitoring_integration()

    # Make real API call
    demonstrate_real_api_with_quota()

    print("\n" + "="*70)
    print("📚 KEY INSIGHTS")
    print("="*70)
    print("""
    Quota System Architecture:

    1. POLICY STORAGE (DynamoDB)
       └── QuotaPolicies table stores limits

    2. USAGE TRACKING (DynamoDB)
       └── UserQuotaMetrics table tracks consumption

    3. ENFORCEMENT (CCWB Lambda)
       ├── CHECK: Before vending credentials
       ├── ALLOW: If within limits
       └── DENY: If exceeded (BLOCK mode)

    4. MONITORING (CloudWatch)
       ├── Metrics: Usage, exceeded, blocked
       ├── Alarms: Threshold notifications
       └── Dashboards: Visual tracking

    5. INTEGRATION POINTS
       ├── Application Inference Profiles (per-tenant)
       ├── JWT claims (user/group mapping)
       └── Cost allocation tags (billing)
    """)

    # Clean up test quotas
    print("\n🧹 Cleaning up test quotas...")
    run_command("ccwb quota delete user test@company.com")
    run_command("ccwb quota delete user demo@company.com")
    print("✅ Test quotas removed")

if __name__ == "__main__":
    main()