#!/usr/bin/env python3
"""
Real-time Quota Tracking Simulation
Shows how CCWB quota monitoring works in production
"""

import json
import time
import random
from datetime import datetime, timedelta
import subprocess

class QuotaSimulator:
    def __init__(self):
        self.users = {
            "alice@marketing.com": {
                "profile": "5gematyf83m0",
                "group": "marketing",
                "monthly_limit": 10000,
                "daily_limit": 1000,
                "enforcement": "alert",
                "monthly_used": 0,
                "daily_used": 0
            },
            "bob@sales.com": {
                "profile": "yku79b5wumnr",
                "group": "sales",
                "monthly_limit": 3000,
                "daily_limit": 300,
                "enforcement": "block",
                "monthly_used": 0,
                "daily_used": 0
            }
        }
        self.events = []

    def clear_screen(self):
        """Clear screen for dashboard effect"""
        print("\033[2J\033[H")  # ANSI escape codes

    def display_dashboard(self):
        """Display real-time quota dashboard"""
        self.clear_screen()
        print("="*80)
        print("📊 CCWB REAL-TIME QUOTA MONITORING DASHBOARD")
        print("="*80)
        print(f"🕐 Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()

        # User status
        for email, data in self.users.items():
            monthly_percent = (data['monthly_used'] / data['monthly_limit']) * 100
            daily_percent = (data['daily_used'] / data['daily_limit']) * 100

            # Determine status indicator
            if daily_percent > 100 or monthly_percent > 100:
                if data['enforcement'] == 'block':
                    status = "🔴 BLOCKED"
                else:
                    status = "🟠 EXCEEDED"
            elif daily_percent > 80 or monthly_percent > 80:
                status = "🟡 WARNING"
            else:
                status = "🟢 OK"

            print(f"👤 {email} [{data['group']}] - {status}")
            print(f"   Enforcement: {data['enforcement'].upper()}")
            print(f"   Daily:   {data['daily_used']:,}/{data['daily_limit']:,} tokens ({daily_percent:.1f}%)")
            print(f"   Monthly: {data['monthly_used']:,}/{data['monthly_limit']:,} tokens ({monthly_percent:.1f}%)")

            # Progress bars
            self.print_progress_bar("   Daily  ", daily_percent)
            self.print_progress_bar("   Monthly", monthly_percent)
            print()

        # Recent events
        print("-"*80)
        print("📜 RECENT EVENTS (Last 5):")
        for event in self.events[-5:]:
            print(f"   {event}")

    def print_progress_bar(self, label, percent):
        """Print a visual progress bar"""
        bar_length = 40
        filled = int(bar_length * min(percent, 100) / 100)
        bar = "█" * filled + "░" * (bar_length - filled)

        color = "\033[32m"  # Green
        if percent > 100:
            color = "\033[31m"  # Red
        elif percent > 80:
            color = "\033[33m"  # Yellow

        print(f"{label}: {color}{bar}\033[0m {percent:.1f}%")

    def simulate_api_call(self, email, tokens):
        """Simulate an API call with quota check"""
        user = self.users[email]
        timestamp = datetime.now().strftime('%H:%M:%S')

        # Check quota
        new_daily = user['daily_used'] + tokens
        new_monthly = user['monthly_used'] + tokens

        would_exceed_daily = new_daily > user['daily_limit']
        would_exceed_monthly = new_monthly > user['monthly_limit']

        if (would_exceed_daily or would_exceed_monthly) and user['enforcement'] == 'block':
            # BLOCKED
            event = f"[{timestamp}] ❌ {email}: Request for {tokens} tokens BLOCKED (quota exceeded)"
            self.events.append(event)
            return False
        else:
            # ALLOWED
            user['daily_used'] = new_daily
            user['monthly_used'] = new_monthly

            if would_exceed_daily or would_exceed_monthly:
                event = f"[{timestamp}] ⚠️ {email}: {tokens} tokens (OVER LIMIT - alert mode)"
            else:
                event = f"[{timestamp}] ✅ {email}: {tokens} tokens consumed"

            self.events.append(event)
            return True

    def run_simulation(self):
        """Run the real-time simulation"""
        print("Starting real-time quota monitoring simulation...")
        print("Press Ctrl+C to stop")
        time.sleep(2)

        # Simulation scenarios
        scenarios = [
            # Normal operations
            ("alice@marketing.com", 50, "Small query"),
            ("bob@sales.com", 30, "Report generation"),
            ("alice@marketing.com", 100, "Document analysis"),
            ("bob@sales.com", 40, "Customer lookup"),

            # Larger operations
            ("alice@marketing.com", 300, "Batch processing"),
            ("bob@sales.com", 150, "Large report"),

            # Push towards limits
            ("alice@marketing.com", 400, "Complex analysis"),
            ("bob@sales.com", 100, "Data export"),

            # Exceed limits
            ("alice@marketing.com", 500, "Heavy processing"),
            ("bob@sales.com", 200, "Bulk operation"),
        ]

        scenario_index = 0

        try:
            while scenario_index < len(scenarios):
                # Get next scenario
                email, tokens, description = scenarios[scenario_index]

                # Random delay between calls
                time.sleep(random.uniform(1, 3))

                # Make the call
                self.simulate_api_call(email, tokens)

                # Update display
                self.display_dashboard()

                scenario_index += 1

                # Show quota enforcement in action
                if scenario_index == 8:
                    print("\n" + "="*80)
                    print("⚠️ APPROACHING QUOTA LIMITS - Watch enforcement modes!")
                    print("="*80)
                    time.sleep(2)

            # Final summary
            time.sleep(2)
            self.show_final_summary()

        except KeyboardInterrupt:
            print("\n\nSimulation stopped by user")

    def show_final_summary(self):
        """Show final summary of the simulation"""
        print("\n" + "="*80)
        print("📊 SIMULATION SUMMARY")
        print("="*80)

        for email, data in self.users.items():
            print(f"\n{email}:")
            print(f"  Total consumed: {data['monthly_used']:,} tokens")
            print(f"  Monthly limit: {data['monthly_limit']:,} tokens")
            print(f"  Status: ", end="")

            if data['monthly_used'] > data['monthly_limit']:
                if data['enforcement'] == 'block':
                    print("🔴 BLOCKED (would deny further requests)")
                else:
                    print("🟠 OVER LIMIT (alerts sent, access continues)")
            else:
                print("🟢 WITHIN LIMITS")

        print("\n" + "="*80)
        print("💡 KEY BEHAVIORS DEMONSTRATED:")
        print("="*80)
        print("""
        1. REAL-TIME TRACKING
           • Every API call updates usage metrics
           • Dashboard shows current consumption

        2. ENFORCEMENT MODES
           • ALERT: Warns but allows continued access
           • BLOCK: Prevents API calls when limit exceeded

        3. THRESHOLD WARNINGS
           • 80% = Warning (yellow)
           • 100% = Critical (red/orange)

        4. PRODUCTION INTEGRATION
           • DynamoDB for storage
           • CloudWatch for metrics
           • SNS for notifications
           • Application Inference Profiles for isolation
        """)

def main():
    print("\n" + "="*80)
    print("🚀 CCWB QUOTA REAL-TIME TRACKING SIMULATION")
    print("="*80)
    print("\nThis simulation demonstrates how quota monitoring works in production")
    print("with real-time tracking and enforcement.\n")

    # Set up test quotas
    print("Setting up test quotas...")
    commands = [
        "ccwb quota set-user alice@marketing.com --monthly-limit 10K --daily-limit 1K --enforcement alert",
        "ccwb quota set-user bob@sales.com --monthly-limit 3K --daily-limit 300 --enforcement block"
    ]

    for cmd in commands:
        subprocess.run(
            f"source venv/bin/activate && {cmd}",
            shell=True,
            capture_output=True,
            executable='/bin/bash'
        )

    print("✅ Test quotas configured\n")

    # Run simulation
    simulator = QuotaSimulator()
    simulator.run_simulation()

    # Clean up
    print("\n🧹 Cleaning up test quotas...")
    subprocess.run(
        "source venv/bin/activate && ccwb quota delete user alice@marketing.com",
        shell=True,
        capture_output=True,
        executable='/bin/bash'
    )
    subprocess.run(
        "source venv/bin/activate && ccwb quota delete user bob@sales.com",
        shell=True,
        capture_output=True,
        executable='/bin/bash'
    )
    print("✅ Test quotas removed")

if __name__ == "__main__":
    main()