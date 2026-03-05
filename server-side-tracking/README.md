# Server-Side Bedrock Usage Tracking

Production-grade per-user cost attribution for Amazon Bedrock — fully server-side, no client OTEL dependency.

## Architecture

```
User → IdP (JWT) → API Gateway + Lambda Gateway
                         │
                         ├─ Validate JWT (server-side identity)
                         ├─ Check DynamoDB quota (block/allow)
                         ├─ Set requestMetadata (userId, group, tenant)
                         ├─ Route to per-user AIP
                         │
                         ▼
                    Amazon Bedrock (Opus 4.6)
                         │
          ┌──────────────┼──────────────────┐
          ▼              ▼                  ▼
    CloudWatch      CloudWatch Logs     S3 (encrypted)
    Metrics         (identity.arn)      (invocation logs)
          │              │                  │
          ▼              │                  ▼
    CW Alarms ──────────────────────► Glue Crawler
          │                                 │
          ▼                                 ▼
    SNS → Lambda                      Athena (queries)
    (enforcement)                           │
          │                                 ▼
          ▼                           QuickSight
    DynamoDB                          (chargebacks)
    (block flag)
```

## What's Included

| File | Purpose |
|------|---------|
| `infra.yaml` | CloudFormation (SAM) — S3, KMS, CloudWatch, IAM, Glue, Athena, DynamoDB, Lambda, SNS |
| `enforcement/handler.py` | Lambda — alarm processing, policy resolution, block/alert enforcement |
| `setup_server_side_tracking.py` | Enable Bedrock logging, create per-user AIPs |
| `seed_policies_and_alarms.py` | Seed DynamoDB quota policies, create per-user CW Alarms at 80%/95% |
| `server_side_tracking_demo.py` | Generate traffic via Converse API with server-side requestMetadata |
| `validate_pipeline.py` | Validate all three data paths (CW Metrics, CW Logs, S3) |
| `deploy_dashboard.py` | CloudWatch dashboard — sparklines, gauges, trends, comparisons |
| `attribution_queries.sql` | 6 Athena queries — per-user cost, chargebacks, heatmaps, top spenders |
| `deploy.sh` | One-command deploy: infra → AIPs → policies → demo → validate → dashboard |

## Quick Start

```bash
# One command — deploys everything
cd server-side-tracking
ALERT_EMAIL=you@company.com ./deploy.sh
```

## Manual Deploy

```bash
# 1. Infrastructure (SAM)
cd server-side-tracking
sam build --template-file infra.yaml
sam deploy --stack-name bedrock-server-side-tracking \
  --capabilities CAPABILITY_NAMED_IAM \
  --parameter-overrides AlertEmail=you@company.com \
  --resolve-s3

# 2. Per-user AIPs + enable logging
cd ..
python server-side-tracking/setup_server_side_tracking.py

# 3. Quota policies + alarms
python server-side-tracking/seed_policies_and_alarms.py

# 4. Generate test traffic
python server-side-tracking/server_side_tracking_demo.py

# 5. Wait 3-5 min, then validate
python server-side-tracking/validate_pipeline.py

# 6. Deploy dashboard
python server-side-tracking/deploy_dashboard.py

# 7. Start Glue crawler (first run)
aws glue start-crawler --name bedrock-invocation-log-crawler

# 8. After crawler completes (~2 min), run Athena queries
#    Workgroup: bedrock-tracking | Database: bedrock_tracking
```

## Infrastructure Components

### Security
- **KMS** — Customer-managed key encrypts S3 logs, Athena results, DynamoDB tables, CloudWatch Logs
- **S3 access logging** — All access to the invocation log bucket is logged
- **S3 bucket policy** — Denies unencrypted transport (TLS enforced)
- **IAM least privilege** — Each role scoped to specific resources
- **DynamoDB encryption** — SSE with KMS
- **Versioning** — S3 bucket versioning enabled for audit trail

### Data Pipeline
- **Bedrock invocation logging** — Metadata-only mode (token counts + identity, no prompts/responses)
- **S3 lifecycle** — Standard → IA at 30d → Glacier at 90d
- **Glue crawler** — Scheduled daily, auto-detects schema changes
- **Athena workgroup** — Encrypted results, 10 GB scan limit safety

### Enforcement
- **DynamoDB QuotaPolicies** — Hierarchical: user → group → default precedence
- **DynamoDB UserQuotaMetrics** — Real-time usage with 90-day TTL
- **CloudWatch Alarms** — Per-user at 80% (warning) and 95% (critical)
- **Lambda enforcement** — Resolves policy, records breach, blocks or alerts
- **SNS** — Separate topics for quota breaches (critical) and usage alerts (info)

### Monitoring
- **CloudWatch dashboard** — Per-user sparklines, quota gauges, token trends, latency, comparisons
- **Athena queries** — Per-user cost, group chargebacks, hourly heatmaps, top spenders, CloudTrail join

## Quota Policy Schema

```json
{
  "policyId": "user#john.doe",
  "policyType": "user",
  "monthlyLimit": 500000000,
  "dailyLimit": 25000000,
  "enforcementMode": "block",
  "enabled": true,
  "description": "Power user override"
}
```

Precedence: `user#john.doe` > `group#engineering` > `default`

Enforcement modes:
- `alert` — Log warning, send notification, allow request
- `block` — Set `blocked=true` in DynamoDB, gateway denies further requests

## Trust Model

| Layer | Source | Trust | Latency | Use For |
|-------|--------|-------|---------|---------|
| Per-user AIP metrics | CloudWatch | ✅ High | ~1 min | Real-time dashboard, alarms |
| `requestMetadata` | Bedrock invocation logs | ✅ High | ~5 min | Athena cost attribution |
| `identity.arn` | CloudWatch Logs | ✅ High | ~5 min | Compliance audit |
| CloudTrail + logs join | Athena | ✅ High | ~15 min | Forensic analysis |
| OTEL (optional) | Client-reported | ⚠️ Medium | Real-time | Not required |

## Teardown

```bash
aws cloudformation delete-stack --stack-name bedrock-server-side-tracking
# Manually delete AIPs:
# aws bedrock delete-inference-profile --inference-profile-identifier aip-user-john-doe
```

## AWS Reference Architectures

- [Converse API requestMetadata cost tracking](https://aws.amazon.com/blogs/machine-learning/cost-tracking-multi-tenant-model-inference-on-amazon-bedrock/)
- [Multi-Tenant GenAI Gateway](https://aws.amazon.com/solutions/guidance/multi-tenant-generative-ai-gateway-with-cost-and-usage-tracking-on-aws/)
- [Proactive AI Cost Management (Part 1 & 2)](https://aws.amazon.com/blogs/machine-learning/build-a-proactive-ai-cost-management-system-for-amazon-bedrock-part-2/)
- [Track and Limit Bedrock Usage by User](https://repost.aws/articles/ARoDnASCxDQyGFfaagReMZNw/how-to-track-and-limit-amazon-bedrock-usage-by-user)
- [Multi-Tenant GenAI Economics Workshop](https://catalog.us-east-1.prod.workshops.aws/workshops/043313ad-6c93-426e-a90d-981bb366f43d)
