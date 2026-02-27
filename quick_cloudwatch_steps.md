# Quick CloudWatch Access Guide

## 🚀 Fastest Way to View Your Metrics

### Option 1: Direct Link (Recommended)
Click this link to go directly to Bedrock metrics:
```
https://us-west-2.console.aws.amazon.com/cloudwatch/home?region=us-west-2#metricsV2:graph=~();namespace=AWS/Bedrock
```

### Option 2: Step-by-Step (5 clicks)

```
1. AWS Console → Search "CloudWatch"
         ↓
2. Left Sidebar → "Metrics" → "All metrics"
         ↓
3. Click "AWS/Bedrock"
         ↓
4. Click "By Inference Profile ID" or "InferenceProfileId"
         ↓
5. Check boxes for metrics you want to see:
   ☑ 5gematyf83m0 (Tenant A)
   ☑ yku79b5wumnr (Tenant B)
```

## 📊 What You'll See

```
Namespace: AWS/Bedrock
    │
    ├─ By Inference Profile ID
    │   ├─ 5gematyf83m0 (Tenant A - Marketing)
    │   │   ├─ Invocations
    │   │   ├─ InputTokenCount
    │   │   └─ OutputTokenCount
    │   │
    │   └─ yku79b5wumnr (Tenant B - Sales)
    │       ├─ Invocations
    │       ├─ InputTokenCount
    │       └─ OutputTokenCount
    │
    └─ By Model ID
        └─ us.anthropic.claude-sonnet-4-6 (Aggregated - old way)
```

## 🎯 Key Points

- **Profile IDs**: Look for `5gematyf83m0` and `yku79b5wumnr`
- **Wait Time**: Metrics appear 3-5 minutes after API calls
- **Region**: Must be in `us-west-2`
- **Time Range**: Adjust to "Last 1 hour" or "Last 3 hours"

## 📱 Mobile/Quick Check

If you just want to verify metrics exist without graphs:

```bash
# Run this in terminal
aws cloudwatch list-metrics \
  --namespace AWS/Bedrock \
  --dimensions Name=InferenceProfileId,Value=5gematyf83m0 \
  --region us-west-2
```

## ✅ Success Indicators

You've successfully separated tenants when you see:

1. ✓ Two distinct `InferenceProfileId` values in CloudWatch
2. ✓ Separate graphs for each tenant
3. ✓ Different token counts per profile
4. ✓ Independent invocation metrics

## ❌ vs ✅ Comparison

**Before (Problem):**
```
CloudWatch → AWS/Bedrock → By Model ID
  └─ us.anthropic.claude-sonnet-4-6
      └─ All tenants aggregated ❌
```

**After (Solution):**
```
CloudWatch → AWS/Bedrock → By Inference Profile ID
  ├─ 5gematyf83m0 (Tenant A only) ✅
  └─ yku79b5wumnr (Tenant B only) ✅
```
