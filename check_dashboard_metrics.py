#!/usr/bin/env python3
"""
Check CloudWatch dashboard metrics and verify data availability
"""

import boto3
import json
from datetime import datetime, timedelta

REGION = "us-west-2"
DASHBOARD_NAME = "CCWB-Quota-Monitoring"

def check_metrics():
    """Check what metrics are available in CloudWatch"""

    cloudwatch = boto3.client('cloudwatch', region_name=REGION)

    print("\n" + "="*70)
    print("📊 CLOUDWATCH METRICS STATUS CHECK")
    print("="*70)
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    # Check for metrics with no dimensions (aggregated)
    print("1️⃣ CHECKING AGGREGATED METRICS (No Dimensions):")
    print("-" * 40)

    metrics_to_check = [
        "InputTokenCount",
        "OutputTokenCount",
        "Invocations"
    ]

    end_time = datetime.utcnow()
    start_time = end_time - timedelta(hours=1)

    total_tokens = 0

    for metric_name in metrics_to_check:
        try:
            response = cloudwatch.get_metric_statistics(
                Namespace='AWS/Bedrock',
                MetricName=metric_name,
                StartTime=start_time,
                EndTime=end_time,
                Period=3600,  # 1 hour
                Statistics=['Sum']
            )

            datapoints = response.get('Datapoints', [])
            if datapoints:
                total = sum(dp['Sum'] for dp in datapoints)
                print(f"  ✅ {metric_name}: {total:.0f} (last hour)")
                if 'Token' in metric_name:
                    total_tokens += total
            else:
                print(f"  ⚫ {metric_name}: No data in last hour")

        except Exception as e:
            print(f"  ❌ {metric_name}: Error - {str(e)[:50]}")

    if total_tokens > 0:
        print(f"\n  📊 Total Tokens (last hour): {total_tokens:.0f}")
        cost = (total_tokens / 1_000_000) * 9  # Average $9/M tokens
        print(f"  💰 Estimated Cost: ${cost:.4f}")

    # Check for Application Inference Profile specific metrics
    print("\n2️⃣ CHECKING APPLICATION INFERENCE PROFILE METRICS:")
    print("-" * 40)

    profiles = {
        "5gematyf83m0": "Tenant A (Marketing)",
        "yku79b5wumnr": "Tenant B (Sales)"
    }

    found_aip_metrics = False

    for profile_id, name in profiles.items():
        print(f"\n  {name} - Profile: {profile_id}")

        # Try with InferenceProfileId dimension
        try:
            response = cloudwatch.get_metric_statistics(
                Namespace='AWS/Bedrock',
                MetricName='InputTokenCount',
                Dimensions=[
                    {'Name': 'InferenceProfileId', 'Value': profile_id}
                ],
                StartTime=start_time,
                EndTime=end_time,
                Period=3600,
                Statistics=['Sum']
            )

            datapoints = response.get('Datapoints', [])
            if datapoints:
                total = sum(dp['Sum'] for dp in datapoints)
                print(f"    ✅ Found metrics: {total:.0f} input tokens")
                found_aip_metrics = True
            else:
                print(f"    ⚫ No InferenceProfileId metrics found")

        except Exception as e:
            print(f"    ❌ Error: {str(e)[:50]}")

    # Check available dimensions
    print("\n3️⃣ AVAILABLE METRIC DIMENSIONS:")
    print("-" * 40)

    try:
        response = cloudwatch.list_metrics(
            Namespace='AWS/Bedrock',
            MetricName='InputTokenCount'
        )

        dimensions_found = set()
        for metric in response.get('Metrics', []):
            for dim in metric.get('Dimensions', []):
                dimensions_found.add(dim['Name'])

        if dimensions_found:
            print("  Dimensions found for InputTokenCount:")
            for dim in sorted(dimensions_found):
                print(f"    • {dim}")
        else:
            print("  No dimensions found")

    except Exception as e:
        print(f"  Error listing metrics: {str(e)[:50]}")

    # Dashboard status
    print("\n4️⃣ DASHBOARD STATUS:")
    print("-" * 40)

    try:
        response = cloudwatch.get_dashboard(
            DashboardName=DASHBOARD_NAME
        )

        if response:
            print(f"  ✅ Dashboard '{DASHBOARD_NAME}' exists")
            print(f"  🔗 View at: https://console.aws.amazon.com/cloudwatch/home?region={REGION}#dashboards:name={DASHBOARD_NAME}")

            # Parse dashboard to check widget configuration
            body = json.loads(response.get('DashboardBody', '{}'))
            widgets = body.get('widgets', [])

            widget_types = {}
            for w in widgets:
                w_type = w.get('type', 'unknown')
                widget_types[w_type] = widget_types.get(w_type, 0) + 1

            print(f"  📈 Widgets: {len(widgets)} total")
            for wt, count in widget_types.items():
                print(f"     - {wt}: {count}")

    except Exception as e:
        print(f"  ❌ Dashboard error: {str(e)[:50]}")

    # Recommendations
    print("\n5️⃣ ANALYSIS & RECOMMENDATIONS:")
    print("-" * 40)

    if total_tokens > 0:
        print("  ✅ Metrics ARE being published to CloudWatch")
        print("  ✅ Token usage is being tracked")

        if not found_aip_metrics:
            print("  ⚠️  Application Inference Profiles may not publish")
            print("      metrics with InferenceProfileId dimension")
            print("  💡 Recommendation: Dashboard widgets should use")
            print("     aggregated metrics (no dimensions) or ModelId")
            print()
            print("  📝 Note: AIP metrics might be aggregated at the")
            print("     account level rather than per-profile")
    else:
        print("  ⚠️ No metrics found in the last hour")
        print("  💡 Try generating more traffic to the AIPs")

    print("\n" + "="*70)
    print("✅ METRICS CHECK COMPLETE")
    print("="*70)

if __name__ == "__main__":
    check_metrics()