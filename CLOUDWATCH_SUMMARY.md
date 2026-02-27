# 📊 CloudWatch Viewing Summary

## 🎯 Your Profile IDs
- **Tenant A (Marketing)**: `5gematyf83m0`
- **Tenant B (Sales)**: `yku79b5wumnr`

---

## 🚀 3 Ways to View Graphs

### 1️⃣ AWS Console (Easiest - Click & View)

**Direct Link:**
```
https://us-west-2.console.aws.amazon.com/cloudwatch/home?region=us-west-2#metricsV2:graph=~();namespace=AWS/Bedrock
```

**Steps:**
1. Open the link above (or go to CloudWatch in AWS Console)
2. Click "AWS/Bedrock" namespace
3. Click "By Inference Profile ID"
4. You'll see TWO profile IDs:
   - `5gematyf83m0` (Tenant A)
   - `yku79b5wumnr` (Tenant B)
5. Check boxes for the metrics you want to graph
6. View the separated graphs!

**Available Metrics:**
- ✓ Invocations (API call count)
- ✓ InputTokenCount (prompt tokens)
- ✓ OutputTokenCount (response tokens)
- ✓ InvocationLatency (response time)

---

### 2️⃣ Command Line (Quick Check)

**Check if metrics are available:**
```bash
/workshop/check_metrics.sh
```

**Fetch metrics for Tenant A:**
```bash
aws cloudwatch get-metric-statistics \
  --namespace AWS/Bedrock \
  --metric-name Invocations \
  --dimensions Name=InferenceProfileId,Value=5gematyf83m0 \
  --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 300 \
  --statistics Sum \
  --region us-west-2
```

**Fetch metrics for Tenant B:**
```bash
aws cloudwatch get-metric-statistics \
  --namespace AWS/Bedrock \
  --metric-name Invocations \
  --dimensions Name=InferenceProfileId,Value=yku79b5wumnr \
  --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 300 \
  --statistics Sum \
  --region us-west-2
```

---

### 3️⃣ Python Script (Automated + Visualization)

**Re-run the test to generate graphs:**
```bash
/workshop/venv/bin/python /workshop/test_tenant_profiles.py
```

This will:
- Make new API calls for both tenants
- Wait for metrics to propagate
- Fetch CloudWatch data
- Generate comparison graphs
- Save to: `/workshop/tenant_separation_metrics.png`

---

## ⏱️ Important Timing Notes

### Why Metrics Might Be Empty:
CloudWatch metrics have a delay of **3-5 minutes** after API calls.

### Current Status:
Run this to check:
```bash
/workshop/check_metrics.sh
```

### If No Metrics Yet:
1. ✅ Profiles are created and active
2. ✅ API calls were made successfully
3. ⏳ Just waiting for CloudWatch propagation
4. 🔄 Wait 3-5 minutes and check again

---

## 📊 What You'll See in CloudWatch

### Structure:
```
CloudWatch Console
  └─ Metrics
      └─ All metrics
          └─ AWS/Bedrock
              ├─ By Inference Profile ID ← Look here!
              │   ├─ 5gematyf83m0 (Tenant A)
              │   │   ├─ Invocations
              │   │   ├─ InputTokenCount
              │   │   └─ OutputTokenCount
              │   │
              │   └─ yku79b5wumnr (Tenant B)
              │       ├─ Invocations
              │       ├─ InputTokenCount
              │       └─ OutputTokenCount
              │
              └─ By Model ID (old aggregated way)
                  └─ us.anthropic.claude-sonnet-4-6
```

### Visual Difference:

**Before (Problem):**
```
┌─────────────────────────────┐
│ us.anthropic.claude-        │
│    sonnet-4-6               │
│                             │
│ All Tenants Mixed ❌        │
│ - Tenant A                  │
│ - Tenant B                  │
│ - Can't separate!           │
└─────────────────────────────┘
```

**After (Solution):**
```
┌──────────────┐  ┌──────────────┐
│ 5gematyf83m0 │  │ yku79b5wumnr │
│              │  │              │
│ Tenant A ✅  │  │ Tenant B ✅  │
│ - Marketing  │  │ - Sales      │
│ - Isolated   │  │ - Isolated   │
└──────────────┘  └──────────────┘
```

---

## 🎨 Creating a Dashboard

### Quick Dashboard Setup:

1. In CloudWatch, select your metrics
2. Click **"Actions"** → **"Add to dashboard"**
3. Create new dashboard: **"Bedrock Multi-Tenant Metrics"**
4. Add multiple widgets:

**Recommended Layout:**
```
┌─────────────────────────────────────────┐
│  📊 Dashboard: Bedrock Multi-Tenant     │
├─────────────────────────────────────────┤
│                                         │
│  [Tenant A Invocations] [Tenant B Inv] │
│                                         │
│  [Tenant A Input Tokens] [Tenant B In] │
│                                         │
│  [Tenant A Output Tokens] [Tenant B O] │
│                                         │
│  [Side-by-Side Comparison]             │
│                                         │
└─────────────────────────────────────────┘
```

---

## 🔔 Setting Up Alarms

### Create Alarms for Each Tenant:

1. Select a metric (e.g., Tenant A Invocations)
2. Click **"Create alarm"**
3. Set threshold (e.g., > 100 invocations per hour)
4. Configure SNS notification
5. Repeat for Tenant B

**Example Use Cases:**
- Alert when tenant exceeds usage quota
- Notify on unusual spike in tokens
- Monitor for errors per tenant

---

## 📁 Local Visualization Files

We've already generated local visualizations:

```bash
# View the problem (aggregated metrics)
open /workshop/cloudwatch_metrics.png

# View the solution (separated metrics)
open /workshop/tenant_separation_metrics.png
```

---

## ✅ Verification Checklist

- [ ] CloudWatch Console opens in us-west-2 region
- [ ] AWS/Bedrock namespace is visible
- [ ] "By Inference Profile ID" dimension exists
- [ ] Two profile IDs appear: `5gematyf83m0` and `yku79b5wumnr`
- [ ] Can select metrics for each profile independently
- [ ] Metrics show data (after 3-5 minute wait)
- [ ] Graphs display separated data per tenant

---

## 🆘 Troubleshooting

### No metrics showing?
```bash
# Check if metrics exist
/workshop/check_metrics.sh

# If empty, wait 3-5 minutes and try again
```

### Wrong region?
Make sure you're in **us-west-2**:
- Check top-right corner of AWS Console
- CLI: Add `--region us-west-2` to commands

### Can't find profile IDs?
Your IDs are:
- Tenant A: `5gematyf83m0`
- Tenant B: `yku79b5wumnr`

### Still issues?
```bash
# Verify profiles exist
/workshop/venv/bin/python /workshop/verify_setup.py

# Make new test calls
/workshop/venv/bin/python /workshop/test_tenant_profiles.py
```

---

## 📚 Additional Resources

- **Full Guide**: `/workshop/cloudwatch_viewing_guide.py`
- **Quick Steps**: `/workshop/quick_cloudwatch_steps.md`
- **Testing Guide**: `/workshop/TESTING_GUIDE.md`
- **Verification**: `/workshop/verify_setup.py`

---

## 🎯 Summary

**To view your graphs in CloudWatch:**

1. **Go to**: https://us-west-2.console.aws.amazon.com/cloudwatch/home?region=us-west-2#metricsV2:
2. **Click**: AWS/Bedrock → By Inference Profile ID
3. **Select**: Both profile IDs (`5gematyf83m0` and `yku79b5wumnr`)
4. **View**: Separated metrics and graphs for each tenant!

**Remember**: Wait 3-5 minutes after API calls for metrics to appear. ⏱️

---

✅ **You now have complete tenant isolation with separate CloudWatch monitoring!**
