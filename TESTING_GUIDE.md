# Application Inference Profiles - Testing Guide

## 🎯 What We Built

A multi-tenant architecture using AWS Bedrock Application Inference Profiles (AIPs) that provides:
- Separate usage tracking per tenant
- Independent cost allocation
- Isolated CloudWatch metrics
- Tag-based billing

## 📁 Files Created

### Configuration
- `lab_helpers/config.py` - Configuration with Region, ModelId, and tenant tags
- `tenant_profiles.json` - Profile ARNs for easy reference

### Setup Scripts
- `aip_setup.py` - Initialize AWS Bedrock clients
- `create_tenant_profiles.py` - Create Application Inference Profiles for both tenants

### Demo Scripts
- `multi_tenant_demo.py` - Shows the PROBLEM (shared profile, aggregated metrics)
- `test_tenant_profiles.py` - Shows the SOLUTION (separate profiles, isolated metrics)

### Verification Scripts
- `verify_setup.py` - Check profile configuration and status
- `comparison_summary.py` - Before/After comparison

## 🧪 How to Test

### 1. View Current Setup

```bash
# Check profile configuration
/workshop/venv/bin/python /workshop/verify_setup.py

# View before/after comparison
/workshop/venv/bin/python /workshop/comparison_summary.py
```

### 2. Run the Problem Demo (Baseline)

```bash
# This shows what happens WITHOUT Application Inference Profiles
# Both tenants use the same system profile - metrics are aggregated
/workshop/venv/bin/python /workshop/multi_tenant_demo.py
```

**Expected Output:**
- Both tenants use `us.anthropic.claude-sonnet-4-6`
- Metrics show aggregated usage
- Can't distinguish between tenants

### 3. Run the Solution Demo

```bash
# This shows the solution WITH Application Inference Profiles
# Each tenant has their own profile - metrics are separated
/workshop/venv/bin/python /workshop/test_tenant_profiles.py
```

**Expected Output:**
- Tenant A uses `5gematyf83m0`
- Tenant B uses `yku79b5wumnr`
- Each tenant has separate metrics
- Visualizations show side-by-side comparison

### 4. Wait for CloudWatch Metrics

⏳ **Important:** CloudWatch metrics take 3-5 minutes to propagate.

After running the test, wait a few minutes, then check:

#### Option A: Re-run the test script
```bash
/workshop/venv/bin/python /workshop/test_tenant_profiles.py
```

#### Option B: Check AWS Console
1. Go to **CloudWatch Console**
2. Navigate to **Metrics** → **All metrics**
3. Select **AWS/Bedrock** namespace
4. Look for dimension **InferenceProfileId**
5. You should see TWO separate profile IDs:
   - `5gematyf83m0` (Tenant A - Marketing)
   - `yku79b5wumnr` (Tenant B - Sales)

### 5. Check Cost Allocation

#### AWS Cost Explorer
1. Go to **AWS Cost Explorer**
2. Click **Cost Allocation Tags**
3. Filter by tags:
   - `tenant=tenant_a` → Marketing costs
   - `tenant=tenant_b` → Sales costs
4. View costs separately per tenant

#### AWS Billing Dashboard
1. Go to **AWS Billing Console**
2. Navigate to **Cost Allocation Tags**
3. Activate the tags: `tenant`, `department`, `costcenter`
4. Wait 24 hours for tags to appear in billing reports

## 📊 Generated Visualizations

### 1. `cloudwatch_metrics.png`
- Shows the PROBLEM: Aggregated metrics from shared system profile
- All tenant usage mixed together

### 2. `tenant_separation_metrics.png`
- Shows the SOLUTION: Separated metrics per tenant
- Side-by-side comparison of Tenant A vs Tenant B

## ✅ Verification Checklist

- [ ] Both Application Inference Profiles created successfully
- [ ] Profiles have status: ACTIVE
- [ ] Tags properly applied (tenant, department, costcenter)
- [ ] Inference calls succeed with tenant-specific profiles
- [ ] CloudWatch shows separate InferenceProfileId dimensions
- [ ] Metrics can be queried independently per tenant
- [ ] Cost allocation tags are active

## 🔧 Troubleshooting

### No CloudWatch Metrics
**Problem:** Metrics showing 0 or empty graphs
**Solution:** Wait 3-5 minutes for CloudWatch to propagate metrics, then re-run

### Profile Already Exists Error
**Problem:** Error creating profile - already exists
**Solution:** Script automatically fetches existing profile, no action needed

### Authentication Error
**Problem:** Unable to connect to AWS
**Solution:** Check AWS credentials are configured:
```bash
aws sts get-caller-identity
```

### Wrong Region
**Problem:** Resources not found
**Solution:** Verify region is set to `us-west-2` in config

## 🎓 Key Concepts Demonstrated

1. **System Inference Profile** (us.anthropic.claude-sonnet-4-6)
   - Shared across all users
   - Cross-region routing
   - No isolation

2. **Application Inference Profile** (5gematyf83m0, yku79b5wumnr)
   - Tenant-specific
   - Independent metrics
   - Tag-based cost allocation
   - Isolated monitoring

3. **CloudWatch Dimensions**
   - `ModelId` → System profile (shared)
   - `InferenceProfileId` → Application profile (isolated)

4. **Cost Allocation**
   - Tags enable cost tracking per tenant
   - Can set budgets and alerts per profile
   - Monthly cost reports by tag

## 📈 Next Steps

1. **Set up CloudWatch Alarms**
   - Create alarms for per-tenant usage thresholds
   - Get notified when limits are exceeded

2. **Implement Rate Limiting**
   - Use AWS Service Quotas per profile
   - Set different limits per tenant tier

3. **Cost Monitoring**
   - Set up AWS Budgets per tenant
   - Create cost anomaly detection

4. **Production Deployment**
   - Create profiles for production tenants
   - Implement automated profile creation
   - Add monitoring dashboards

## 🔗 Resources

- [AWS Bedrock Documentation](https://docs.aws.amazon.com/bedrock/)
- [Application Inference Profiles Guide](https://docs.aws.amazon.com/bedrock/latest/userguide/inference-profiles.html)
- [CloudWatch Metrics for Bedrock](https://docs.aws.amazon.com/bedrock/latest/userguide/monitoring-cloudwatch.html)
- [AWS Cost Allocation Tags](https://docs.aws.amazon.com/awsaccountbilling/latest/aboutv2/cost-alloc-tags.html)
