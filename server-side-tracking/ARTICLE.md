# Closing the Attribution Gap: Server-Side Usage Tracking for Amazon Bedrock Multi-Tenant Environments

## The Problem: Who Used What?

When you roll out generative AI to multiple teams via Amazon Bedrock, leadership asks a simple question: *who's using what, and how much is it costing us?*

The answer is harder than it sounds. Standard AWS billing shows Bedrock costs aggregated by model and region — not by user, team, or business unit. Without per-user visibility, one heavy user can blow through your entire organization's token allocation before anyone notices.

Two approaches exist today. This article compares them, explains why you might need both, and walks through a production-grade server-side implementation.

## Two Approaches to Attribution

### Client-Side: CCWB's OpenTelemetry Model

Claude Code with Bedrock (CCWB) solves per-user tracking by instrumenting the client. When a developer uses Claude Code, the CCWB CLI:

1. Authenticates the user via Cognito (SSO)
2. Sends telemetry from the developer's machine via OpenTelemetry
3. Records token usage in DynamoDB per user
4. Displays real-time consumption on a CloudWatch dashboard

```
Developer's Terminal
    │
    ├─ CCWB CLI authenticates via Cognito
    ├─ Developer makes requests to Bedrock
    ├─ OTEL collector on client reports usage ◄── trust boundary
    │
    ▼
DynamoDB (quota tracking) → CloudWatch Dashboard
```

This works well for its use case — it's fast, gives real-time dashboards, and enables quota enforcement at the request level. But there's a fundamental limitation: **the attribution data is only as reliable as the client reporting it.**

If the OTEL collector is misconfigured, crashes, or is bypassed, usage happens without attribution. The server (Bedrock) has no idea who the caller is beyond the IAM role — which is typically a shared role for all users in a tenant.

### Server-Side: Attribution at the Gateway

The server-side approach moves the trust boundary from the client to your API gateway. Instead of trusting the client to report who it is, the gateway:

1. Validates the user's JWT token (signed by your IdP — can't be forged)
2. Extracts identity from verified claims
3. Stamps the Bedrock request with `requestMetadata` containing the user's identity
4. Routes the request through a per-user Application Inference Profile (AIP)

```
User → IdP (JWT) → API Gateway / Lambda
                        │
                        ├─ Validate JWT (server-side)
                        ├─ Set requestMetadata = {userId, group, tenant}
                        ├─ Route to per-user AIP
                        │
                        ▼
                   Amazon Bedrock
                        │
         ┌──────────────┼──────────────┐
         ▼              ▼              ▼
   CloudWatch      CloudWatch      S3 Logs
   Metrics         Logs            (Athena)
   (per AIP)       (identity.arn)  (requestMetadata)
```

The user never touches `requestMetadata`. The gateway reads identity from the verified JWT and injects it. Three independent server-side records are created — all derived from the same verified token.

## Trust Model Comparison

| | Client-Side (CCWB/OTEL) | Server-Side (Gateway) |
|---|---|---|
| **Who reports identity?** | The client (user's machine) | The server (your gateway) |
| **Can users spoof it?** | Possible if OTEL is bypassed | No — JWT is cryptographically signed |
| **Token counts from?** | Client-reported | Bedrock's own invocation logs |
| **Works if client is buggy?** | No | Yes |
| **Latency** | Real-time | 1-5 minutes |
| **Best for** | Quota enforcement, real-time dashboards | Cost attribution, audit, compliance |

Neither approach is wrong — they serve different purposes. The recommendation is to use both: OTEL for the real-time "should I block this request?" loop, and the server-side pipeline as the source of truth for billing.

## How the Server-Side Pipeline Works

### Layer 1: Per-User Application Inference Profiles

Each user gets their own AIP with cost allocation tags:

```python
bedrock.create_inference_profile(
    inferenceProfileName="aip-user-john-doe",
    modelSource={"copyFrom": system_profile_arn},
    tags=[
        {"key": "userId", "value": "john.doe"},
        {"key": "group", "value": "engineering"},
        {"key": "tenant", "value": "tenant_a"},
        {"key": "department", "value": "platform"},
    ],
)
```

These tags flow directly into AWS Cost Explorer and Cost & Usage Reports. Finance teams can slice Bedrock spend by user, group, department, or tenant — no custom pipeline needed.

### Layer 2: Converse API with requestMetadata

The gateway injects identity metadata into every Bedrock call:

```python
# Gateway code — identity comes from verified JWT, not client input
response = bedrock_runtime.converse(
    modelId=user_profile_arn,
    messages=[{"role": "user", "content": [{"text": prompt}]}],
    inferenceConfig={"maxTokens": 256},
    requestMetadata={
        "userId": claims["sub"],        # from verified JWT
        "groupId": claims["groups"][0],  # from verified JWT
        "tenantId": claims["tenant"],    # from verified JWT
        "source": "server-side-gateway",
    },
)
```

This metadata lands in Bedrock's invocation logs — both in S3 and CloudWatch Logs. It doesn't affect the model's response; it's purely for tracking.

### Layer 3: Three Independent Data Paths

Every call creates three server-side records:

**CloudWatch Metrics** (real-time, ~1 min delay)
- `AWS/Bedrock` namespace, dimensioned by the AIP's ModelId
- Invocations, InputTokenCount, OutputTokenCount, InvocationLatency
- Powers the CloudWatch dashboard with per-user sparklines and gauges

**CloudWatch Logs** (near real-time, ~2-5 min delay)
- Full invocation log with `identity.arn` (the IAM principal) and `requestMetadata`
- Queryable via CloudWatch Logs Insights:

```
stats sum(input.inputTokenCount) as inputTokens,
      sum(output.outputTokenCount) as outputTokens,
      count(*) as calls
  by requestMetadata.userId, requestMetadata.groupId
| sort inputTokens desc
```

**S3** (batch, ~5-10 min delay)
- Raw JSON logs in S3, crawled by Glue, queryable via Athena
- Supports complex analytics: daily cost estimates, group chargebacks, hourly heatmaps, top spenders

```sql
SELECT
  requestmetadata['userId'] AS user_id,
  requestmetadata['groupId'] AS group_id,
  modelid,
  count(*) AS invocations,
  sum(inputtokencount + outputtokencount) AS total_tokens,
  round(
    sum(inputtokencount) * 15.0 / 1000000 +
    sum(outputtokencount) * 75.0 / 1000000, 4
  ) AS total_cost_usd
FROM bedrock_invocation_logs
WHERE requestmetadata['source'] = 'server-side-gateway'
GROUP BY 1, 2, 3
ORDER BY total_cost_usd DESC;
```

## Quota Enforcement

The server-side approach includes a hierarchical quota system stored in DynamoDB:

```
Precedence: user#john.doe > group#engineering > default
```

| Policy | Monthly Limit | Mode |
|--------|-------------|------|
| `default` | 225M tokens | alert |
| `group#engineering` | 500M tokens | block |
| `group#sales` | 300M tokens | block |
| `user#john.doe` | 500M tokens | block (power user override) |

CloudWatch Alarms monitor each user's AIP at 80% (warning) and 95% (critical). When an alarm fires:

```
CloudWatch Alarm → SNS → Lambda (enforcement)
                              │
                              ├─ Resolve effective policy (user > group > default)
                              ├─ Record breach in DynamoDB
                              ├─ Block mode? Set blocked=true (gateway checks this)
                              └─ Publish notification via SNS
```

The gateway checks the `blocked` flag in DynamoDB before forwarding requests. Blocked users get a clear error message — no silent failures.

## Infrastructure

The entire solution deploys via a single SAM template:

| Component | Purpose |
|-----------|---------|
| S3 (encrypted, lifecycle rules) | Invocation log storage → IA at 30d → Glacier at 90d |
| KMS | Customer-managed key for S3 and DynamoDB encryption |
| CloudWatch Log Group | Real-time invocation logs for Logs Insights queries |
| IAM roles (3) | Bedrock logging, Glue crawler, Lambda enforcement — least privilege |
| Glue Database + Crawler | Auto-discovers schema, runs daily over S3 logs |
| Athena Workgroup | Encrypted query results, 10 GB scan safety limit |
| DynamoDB (2 tables) | QuotaPolicies (hierarchical limits) + UserQuotaMetrics (usage with TTL) |
| Lambda | Enforcement function triggered by alarm breaches |
| SNS (2 topics) | Quota breaches (critical) + usage alerts (informational) |
| CloudWatch Dashboard | 16 widgets: sparklines, gauges, trends, comparisons |

Deploy with one command:

```bash
ALERT_EMAIL=you@company.com ./deploy.sh
```

## When to Use Which Approach

| Scenario | Recommended Approach |
|----------|---------------------|
| Real-time quota enforcement (block before overspend) | Client-side (CCWB/OTEL) |
| Cost attribution for finance/chargebacks | Server-side (this solution) |
| Compliance audit trail | Server-side |
| Developer self-service usage dashboard | Either — OTEL is faster |
| Multi-tenant SaaS with untrusted clients | Server-side (mandatory) |
| Internal developer tools with trusted clients | Client-side is sufficient |
| Belt-and-suspenders (both) | OTEL for speed, server-side for truth |

## Key Takeaway

Client-side telemetry and server-side attribution aren't competing approaches — they're complementary layers. OTEL gives you speed; the server-side pipeline gives you trust. For enterprise deployments where cost attribution drives real financial decisions, the server-side pipeline should be the source of truth, with OTEL as an optional real-time overlay.

The `requestMetadata` parameter in the Converse API is the key enabler. If your gateway sets it from a verified JWT — not from client input — you get per-user cost attribution with zero client-side dependencies, backed by Bedrock's own invocation logs.

---

*The complete implementation — CloudFormation template, Lambda enforcement, Athena queries, CloudWatch dashboard, and deploy scripts — is available at [github.com/cmsrb4u/aws-bedrock-multi-tenant-workshop/tree/main/server-side-tracking](https://github.com/cmsrb4u/aws-bedrock-multi-tenant-workshop/tree/main/server-side-tracking).*
