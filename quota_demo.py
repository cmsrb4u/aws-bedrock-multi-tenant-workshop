#!/usr/bin/env python3
"""
Demonstration of CCWB Quota Monitoring System
Shows how token usage is tracked and enforced
"""

import json
from datetime import datetime

def simulate_quota_check(user_email, tokens_to_use, current_usage):
    """Simulate quota enforcement logic"""

    # Quota policies (from the system)
    policies = {
        "john.doe@company.com": {
            "monthly_limit": 500_000_000,  # 500M
            "daily_limit": 20_000_000,      # 20M
            "enforcement": "alert"
        },
        "jane@company.com": {
            "monthly_limit": 400_000_000,  # 400M (engineering group)
            "daily_limit": None,
            "enforcement": "alert"
        },
        "default": {
            "monthly_limit": 225_000_000,  # 225M
            "daily_limit": 8_000_000,       # 8M
            "enforcement": "alert"
        }
    }

    # Get user's policy
    if user_email in policies:
        policy = policies[user_email]
        policy_type = "user"
    else:
        policy = policies["default"]
        policy_type = "default"

    print(f"\n{'='*60}")
    print(f"QUOTA CHECK for {user_email}")
    print(f"{'='*60}")
    print(f"Policy Type: {policy_type}")
    print(f"Enforcement Mode: {policy['enforcement']}")
    print(f"Monthly Limit: {policy['monthly_limit']:,} tokens")
    if policy['daily_limit']:
        print(f"Daily Limit: {policy['daily_limit']:,} tokens")

    # Check monthly usage
    print(f"\n📊 Current Usage:")
    print(f"  Monthly: {current_usage['monthly']:,} tokens")
    print(f"  Daily: {current_usage['daily']:,} tokens")

    print(f"\n📝 Request: {tokens_to_use:,} tokens")

    # Calculate new usage
    new_monthly = current_usage['monthly'] + tokens_to_use
    new_daily = current_usage['daily'] + tokens_to_use

    monthly_percent = (new_monthly / policy['monthly_limit']) * 100
    daily_percent = (new_daily / policy['daily_limit']) * 100 if policy['daily_limit'] else 0

    print(f"\n📈 After Request:")
    print(f"  Monthly: {new_monthly:,} ({monthly_percent:.1f}% of limit)")
    if policy['daily_limit']:
        print(f"  Daily: {new_daily:,} ({daily_percent:.1f}% of limit)")

    # Check thresholds
    print(f"\n🚦 Status:")

    # Monthly check
    if monthly_percent > 100:
        if policy['enforcement'] == 'block':
            print(f"  ❌ BLOCKED: Monthly limit exceeded!")
            return False
        else:
            print(f"  ⚠️ WARNING: Monthly limit exceeded (alert mode)")
    elif monthly_percent > 90:
        print(f"  🔴 CRITICAL: {monthly_percent:.1f}% of monthly limit")
    elif monthly_percent > 80:
        print(f"  🟡 WARNING: {monthly_percent:.1f}% of monthly limit")
    else:
        print(f"  🟢 OK: {monthly_percent:.1f}% of monthly limit")

    # Daily check
    if policy['daily_limit'] and daily_percent > 100:
        if policy['enforcement'] == 'block':
            print(f"  ❌ BLOCKED: Daily limit exceeded!")
            return False
        else:
            print(f"  ⚠️ WARNING: Daily limit exceeded (alert mode)")
    elif policy['daily_limit'] and daily_percent > 80:
        print(f"  🟡 WARNING: {daily_percent:.1f}% of daily limit")

    print(f"\n✅ Request ALLOWED")
    return True

# Demonstrate different scenarios
if __name__ == "__main__":
    print("CCWB QUOTA MONITORING DEMONSTRATION")
    print("="*60)

    # Scenario 1: User within limits
    print("\n📌 Scenario 1: Normal usage")
    simulate_quota_check(
        "john.doe@company.com",
        tokens_to_use=1_000_000,  # 1M tokens
        current_usage={"monthly": 50_000_000, "daily": 2_000_000}
    )

    # Scenario 2: Approaching monthly limit
    print("\n\n📌 Scenario 2: Approaching monthly limit (85%)")
    simulate_quota_check(
        "john.doe@company.com",
        tokens_to_use=5_000_000,  # 5M tokens
        current_usage={"monthly": 420_000_000, "daily": 5_000_000}
    )

    # Scenario 3: Exceeding daily limit
    print("\n\n📌 Scenario 3: Exceeding daily limit")
    simulate_quota_check(
        "john.doe@company.com",
        tokens_to_use=3_000_000,  # 3M tokens
        current_usage={"monthly": 100_000_000, "daily": 19_000_000}
    )

    # Scenario 4: Default policy user
    print("\n\n📌 Scenario 4: User with default policy")
    simulate_quota_check(
        "unknown@company.com",
        tokens_to_use=1_000_000,  # 1M tokens
        current_usage={"monthly": 20_000_000, "daily": 1_000_000}
    )

    print("\n" + "="*60)
    print("DEMONSTRATION COMPLETE")
    print("="*60)