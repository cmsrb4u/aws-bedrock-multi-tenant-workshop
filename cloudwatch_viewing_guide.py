"""
Step-by-Step Guide: Viewing Application Inference Profile Graphs in CloudWatch
"""

import json

# Load tenant profiles
with open('/workshop/tenant_profiles.json', 'r') as f:
    config = json.load(f)

print("=" * 80)
print("📊 How to View Application Inference Profile Graphs in CloudWatch")
print("=" * 80)

print("\n" + "=" * 80)
print("METHOD 1: AWS Console (Web Interface)")
print("=" * 80)

print("""
STEP 1: Open CloudWatch Console
--------------------------------
1. Log in to AWS Console: https://console.aws.amazon.com
2. Make sure you're in the correct region: us-west-2 (top-right corner)
3. Search for "CloudWatch" in the search bar
4. Click on "CloudWatch" to open the service

STEP 2: Navigate to Metrics
----------------------------
1. In the left sidebar, click "Metrics" → "All metrics"
2. You'll see a list of AWS service namespaces

STEP 3: Select Bedrock Metrics
-------------------------------
1. Click on "AWS/Bedrock" (may take a moment to load)
2. You'll see different metric groupings

STEP 4: View by Inference Profile
----------------------------------
1. Click on "By Inference Profile ID" or "InferenceProfileId"
2. You should see TWO profile IDs listed:
   ✓ 5gematyf83m0 (Tenant A - Marketing)
   ✓ yku79b5wumnr (Tenant B - Sales)

STEP 5: Select Metrics to Graph
--------------------------------
1. Check the boxes for metrics you want to view:
   ☑ Invocations (number of API calls)
   ☑ InputTokenCount (tokens in prompts)
   ☑ OutputTokenCount (tokens in responses)

2. You can select the same metric for BOTH profiles to compare

STEP 6: Customize Your Graph
-----------------------------
1. Use the "Graphed metrics" tab to customize:
   - Statistic: Sum, Average, Maximum, etc.
   - Period: 1 minute, 5 minutes, etc.
   - Time range: 1 hour, 3 hours, 12 hours, etc.

2. Click the time range selector (top-right) to adjust:
   - Last 1 hour
   - Last 3 hours
   - Custom range

STEP 7: Create a Dashboard (Optional)
--------------------------------------
1. Click "Actions" → "Add to dashboard"
2. Create a new dashboard or add to existing
3. Name it something like "Bedrock Multi-Tenant Metrics"
4. You can add multiple graphs to one dashboard
""")

print("\n" + "=" * 80)
print("METHOD 2: AWS CLI")
print("=" * 80)

print(f"""
You can also view metrics using AWS CLI commands:

# Get Invocations for Tenant A
aws cloudwatch get-metric-statistics \\
  --namespace AWS/Bedrock \\
  --metric-name Invocations \\
  --dimensions Name=InferenceProfileId,Value=5gematyf83m0 \\
  --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%S) \\
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \\
  --period 300 \\
  --statistics Sum \\
  --region us-west-2

# Get Invocations for Tenant B
aws cloudwatch get-metric-statistics \\
  --namespace AWS/Bedrock \\
  --metric-name Invocations \\
  --dimensions Name=InferenceProfileId,Value=yku79b5wumnr \\
  --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%S) \\
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \\
  --period 300 \\
  --statistics Sum \\
  --region us-west-2
""")

print("\n" + "=" * 80)
print("METHOD 3: CloudWatch Insights")
print("=" * 80)

print("""
For advanced queries:

1. In CloudWatch, click "Logs" → "Insights"
2. Select log group: /aws/bedrock/modelinvocations
3. Run queries to analyze usage patterns
4. Create custom visualizations
""")

print("\n" + "=" * 80)
print("📋 Quick Reference")
print("=" * 80)

print(f"""
Your Profile Information:
-------------------------
Region: {config['region']}

Tenant A (Marketing):
  Profile ID: 5gematyf83m0
  ARN: {config['tenant_a_profile_arn']}
  Tags: tenant=tenant_a, department=marketing

Tenant B (Sales):
  Profile ID: yku79b5wumnr
  ARN: {config['tenant_b_profile_arn']}
  Tags: tenant=tenant_b, department=sales

Available Metrics:
------------------
• Invocations - Number of API calls
• InputTokenCount - Tokens in requests
• OutputTokenCount - Tokens in responses
• InvocationLatency - Response time
• InvocationClientErrors - 4xx errors
• InvocationServerErrors - 5xx errors

Useful Dimensions:
------------------
• InferenceProfileId - Your tenant profiles (5gematyf83m0, yku79b5wumnr)
• ModelId - The underlying model
• Region - us-west-2
""")

print("\n" + "=" * 80)
print("🎯 Recommended Dashboard Setup")
print("=" * 80)

print("""
Create a dashboard with these widgets:

Row 1: Invocations
  - Tenant A Invocations (blue line)
  - Tenant B Invocations (orange line)

Row 2: Token Usage
  - Tenant A Input Tokens (green bars)
  - Tenant A Output Tokens (red bars)

Row 3: Token Usage
  - Tenant B Input Tokens (green bars)
  - Tenant B Output Tokens (red bars)

Row 4: Comparison
  - Side-by-side total usage comparison
  - Cost estimation based on tokens
""")

print("\n" + "=" * 80)
print("⚠️ Important Notes")
print("=" * 80)

print("""
1. WAIT TIME: Metrics take 3-5 minutes to appear after API calls
2. REFRESH: Click the refresh button in CloudWatch to see latest data
3. PERIOD: Use 1-minute periods for detailed views, 5-minute for overview
4. RETENTION: Metrics are retained for 15 months
5. ALARMS: You can set alarms on any metric to get notified
""")

print("\n" + "=" * 80)
print("🔗 Direct Links")
print("=" * 80)

print(f"""
CloudWatch Console (us-west-2):
https://us-west-2.console.aws.amazon.com/cloudwatch/home?region=us-west-2#metricsV2:

CloudWatch Metrics Explorer:
https://us-west-2.console.aws.amazon.com/cloudwatch/home?region=us-west-2#metricsV2:graph=~()

Bedrock Metrics:
https://us-west-2.console.aws.amazon.com/cloudwatch/home?region=us-west-2#metricsV2:graph=~();namespace=AWS/Bedrock
""")

print("\n" + "=" * 80)
print("✅ Next Steps")
print("=" * 80)

print("""
1. Open CloudWatch Console using the link above
2. Navigate to AWS/Bedrock metrics
3. Select "By Inference Profile ID"
4. Check boxes for both tenant profiles
5. View the separated metrics!
6. Create a dashboard to monitor ongoing usage
""")

print("=" * 80)
