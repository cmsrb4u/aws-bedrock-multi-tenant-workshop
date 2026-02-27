# AWS Bedrock Multi-Tenant Workshop

A hands-on workshop for implementing multi-tenant architectures using AWS Bedrock Application Inference Profiles with complete monitoring and cost allocation.

## 🎯 What You'll Learn

- Create Application Inference Profiles for tenant separation
- Set up CloudWatch alarms for usage monitoring
- Configure AWS Budgets for cost tracking per tenant
- Implement tag-based cost allocation
- Visualize tenant metrics with Python

## 📋 Prerequisites

- AWS Account with Bedrock access enabled
- Python 3.10+
- AWS CLI configured
- Basic knowledge of AWS services

## 🚀 Quick Start

### 1. Clone and Setup

```bash
git clone https://github.com/cmsrb4u/aws-bedrock-multi-tenant-workshop.git
cd aws-bedrock-multi-tenant-workshop

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure AWS

```bash
# Set your AWS region
export AWS_REGION=us-west-2

# Verify AWS credentials
aws sts get-caller-identity
```

### 3. Create Application Inference Profiles

```bash
python create_tenant_profiles.py
```

This creates two tenant profiles:
- **Tenant A (Marketing)** - Profile ID: `5gematyf83m0`
- **Tenant B (Sales)** - Profile ID: `yku79b5wumnr`

### 4. Test the Profiles

```bash
python test_tenant_profiles.py
```

### 5. Set Up Monitoring

```bash
# Create CloudWatch alarms
bash setup_monitoring.sh

# Create AWS Budgets
bash setup_budgets.sh
```

## 📁 Repository Structure

```
├── README.md                          # This file
├── requirements.txt                   # Python dependencies
├── .env.claude                        # Environment configuration
│
├── lab_helpers/                       # Helper modules
│   ├── config.py                      # Configuration settings
│   └── __init__.py
│
├── Python Scripts/
│   ├── create_tenant_profiles.py      # Create Application Inference Profiles
│   ├── test_tenant_profiles.py        # Test and generate metrics
│   ├── invoke_and_visualize.py        # Make API calls and visualize
│   ├── verify_setup.py                # Verify profile configuration
│   ├── comparison_summary.py          # Before/after comparison
│   ├── cloudwatch_viewing_guide.py    # CloudWatch viewing guide
│   └── multi_tenant_demo.py           # Problem demonstration
│
├── Monitoring Scripts/
│   ├── setup_monitoring.sh            # Create CloudWatch alarms
│   ├── setup_budgets.sh               # Create AWS Budgets
│   └── check_metrics.sh               # Quick metrics check
│
├── Configuration Files/
│   ├── tenant_profiles.json           # Profile ARNs
│   ├── tenant-a-budget.json           # Tenant A budget config
│   ├── tenant-a-notifications.json    # Tenant A alerts
│   ├── tenant-b-budget.json           # Tenant B budget config
│   └── tenant-b-notifications.json    # Tenant B alerts
│
└── Documentation/
    ├── TESTING_GUIDE.md               # Complete testing guide
    ├── CLOUDWATCH_SUMMARY.md          # CloudWatch setup
    ├── QUOTA_MANAGEMENT_GUIDE.md      # Quota management comparison
    └── quick_cloudwatch_steps.md      # Quick reference
```

## 🧪 Workshop Exercises

### Exercise 1: Create Tenant Profiles

Create separate Application Inference Profiles for two tenants with cost allocation tags.

```bash
python create_tenant_profiles.py
```

**Expected Output:**
- Two active Application Inference Profiles
- Tags applied: tenant, department, costcenter

### Exercise 2: Generate Usage Metrics

Make inference calls for both tenants and generate CloudWatch metrics.

```bash
python test_tenant_profiles.py
```

**Expected Output:**
- API calls succeed for both tenants
- Separate CloudWatch metrics per profile
- Visualization images created

### Exercise 3: Set Up CloudWatch Alarms

Create alarms to monitor token usage and invocations.

```bash
bash setup_monitoring.sh
```

**Creates:**
- 6 CloudWatch alarms (3 per tenant)
- Token usage monitoring (80% threshold)
- Invocation count monitoring

### Exercise 4: Configure AWS Budgets

Set up monthly cost budgets with email alerts.

```bash
bash setup_budgets.sh
```

**Creates:**
- Tenant A: $500/month budget
- Tenant B: $750/month budget
- Email alerts at 80% and 100%

## 📊 Key Concepts

### Application Inference Profiles

Application Inference Profiles provide tenant-level isolation for:
- **Separate CloudWatch metrics** per tenant
- **Tag-based cost allocation** for billing
- **Independent quota management** per profile
- **Isolated monitoring and alerting**

### Cost Allocation Tags

Each profile has tags for cost tracking:
```python
tenant: tenant_a | tenant_b
department: marketing | sales
costcenter: marketing-ops | sales-ops
```

### Monitoring Architecture

```
┌─────────────────────┐
│  Application Code   │
│                     │
│  Tenant A / B calls │
└──────────┬──────────┘
           │
           v
┌─────────────────────┐
│ Inference Profiles  │
│  5gematyf83m0 (A)   │
│  yku79b5wumnr (B)   │
└──────────┬──────────┘
           │
           ├──────────> CloudWatch Metrics
           ├──────────> CloudWatch Alarms
           └──────────> Cost Explorer (tags)
```

## 📈 Viewing Metrics

### CloudWatch Console

1. Go to [CloudWatch Metrics](https://console.aws.amazon.com/cloudwatch)
2. Select **AWS/Bedrock** namespace
3. Choose **By Inference Profile ID**
4. Select your tenant profiles

### AWS CLI

```bash
# Get metrics for Tenant A
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

## 💰 Cost Management

### View Costs by Tenant

1. Go to [Cost Explorer](https://console.aws.amazon.com/cost-management/home#/cost-explorer)
2. Group by: **Tag** → `tenant`
3. Filter: **Service** = Amazon Bedrock
4. View monthly costs per tenant

### Budget Alerts

After creating budgets:
1. Check email for SNS confirmation
2. Click confirmation link
3. Receive alerts at 80% and 100% of budget

## 🔧 Troubleshooting

### No CloudWatch Metrics

**Problem:** Metrics showing 0 or empty
**Solution:** Wait 3-5 minutes after API calls for propagation

### Budget Not Filtering by Tags

**Problem:** Budget shows all Bedrock costs
**Solution:**
1. Activate cost allocation tags in AWS Billing Console
2. Wait 24 hours for tags to appear in billing data

### Alarms in INSUFFICIENT_DATA State

**Problem:** Alarms show no data
**Solution:** Normal for new alarms; will update after usage

## 📚 Additional Resources

- [AWS Bedrock Documentation](https://docs.aws.amazon.com/bedrock/)
- [Application Inference Profiles Guide](https://docs.aws.amazon.com/bedrock/latest/userguide/inference-profiles.html)
- [CloudWatch Metrics for Bedrock](https://docs.aws.amazon.com/bedrock/latest/userguide/monitoring-cloudwatch.html)
- [AWS Cost Allocation Tags](https://docs.aws.amazon.com/awsaccountbilling/latest/aboutv2/cost-alloc-tags.html)

## 🤝 Contributing

Contributions welcome! Please open an issue or submit a pull request.

## 📝 License

This project is licensed under the MIT License.

## 🙏 Acknowledgments

Based on AWS best practices for multi-tenant SaaS architectures using Amazon Bedrock.

---

**Ready to get started?** Run `python create_tenant_profiles.py` to begin! 🚀
