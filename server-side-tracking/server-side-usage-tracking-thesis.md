# Server-Side Usage Tracking for Multi-Tenant Bedrock Attribution

**Date:** 2026-03-04

## The Gap

The repo's current approach relies on client-side OTEL telemetry for user-level attribution, meaning the data is only as reliable as the client reporting it. The RoleSessionName in CloudTrail provides a server-side fallback but isn't structured enough for cost attribution dashboards out of the box.

## Three Server-Side Options (Increasing Effort)

### 1. Bedrock Model Invocation Logging → S3 → Athena (Lowest Effort, Highest Signal)

Bedrock natively logs every `InvokeModel` call when model invocation logging is enabled. Each log entry includes:
- `requestId`, `modelId`, `inputTokenCount`, `outputTokenCount`
- Full IAM identity of the caller (from request context, not client-reported)
- Timestamp, region, inference profile ID if used

Enable logging to S3, create a Glue table, query with Athena. Server-side token counts attributed to the IAM principal — no OTEL dependency.

### 2. Structured RoleSessionName Convention (Zero New Infra)

Enforce a convention at the AssumeRole boundary — which CCWB controls server-side:

```
RoleSessionName = "u=john.doe|g=engineering|t=tenant-a"
```

Since the CCWB auth layer (Cognito + Lambda) calls `sts:AssumeRole`, the session name is set by trusted code, not the client. Query in Athena over CloudTrail:

```sql
SELECT
  regexp_extract(useridentity.arn, 'u=([^|]+)', 1) AS user_id,
  regexp_extract(useridentity.arn, 'g=([^|]+)', 1) AS group_id,
  count(*) AS invocation_count
FROM cloudtrail_logs
WHERE eventsource = 'bedrock.amazonaws.com'
  AND eventname = 'InvokeModel'
GROUP BY 1, 2
```

Limitation: CloudTrail alone doesn't give token counts — only invocation counts and model IDs.

### 3. Combined Pipeline (Full Attribution)

Join CloudTrail + Bedrock invocation logs on `requestId` for the complete picture:

```sql
SELECT
  regexp_extract(ct.useridentity.arn, 'u=([^|]+)', 1) AS user_id,
  regexp_extract(ct.useridentity.arn, 'g=([^|]+)', 1) AS group_id,
  bil.modelid,
  sum(bil.inputtokencount) AS input_tokens,
  sum(bil.outputtokencount) AS output_tokens
FROM cloudtrail_logs ct
JOIN bedrock_invocation_logs bil
  ON ct.requestid = bil.requestid
WHERE ct.eventsource = 'bedrock.amazonaws.com'
GROUP BY 1, 2, 3
```

This gives: who called (server-side identity), what they consumed (server-side token counts), and which model/profile they used. Fully server-side, no OTEL trust dependency.

## Trust Model Comparison

| Layer | Source | Trust Level | Latency | Use For |
|-------|--------|-------------|---------|---------|
| OTEL (current) | Client-reported | Medium | Real-time | Operational dashboards, quota enforcement |
| Bedrock invocation logs | Server-side | High | Minutes (S3 delivery) | Cost attribution, audit |
| CloudTrail | Server-side | High | ~5-15 min | Identity correlation, compliance |

## Recommendation

- **Keep OTEL** for real-time quota enforcement (fast, good enough for "should I block this request")
- **Add Bedrock invocation logging → S3 → Athena** as the authoritative cost attribution layer
- **Enforce structured RoleSessionName** in CCWB's auth Lambda — small change that makes both CloudTrail and invocation logs parseable without additional infra

## Cost Note

Bedrock invocation logging can get expensive at high volume (logs full request/response by default). Configure metadata-only logging (still includes token counts and identity) to keep costs down.

## Concrete Implementation (This Repo)

Three files implement this thesis using Claude Opus 4.6:

| File | What It Does |
|------|-------------|
| `setup_server_side_tracking.py` | Creates S3 bucket, enables Bedrock invocation logging (metadata-only), creates per-USER AIPs with structured tags |
| `server_side_tracking_demo.py` | Makes Converse API calls with `requestMetadata` set server-side, queries CloudWatch Logs Insights for `identity.arn` attribution, prints per-user/group usage report, outputs Athena queries |
| `attribution_queries.sql` | 6 ready-to-use Athena queries: per-user usage, daily cost estimate, group chargebacks, CloudTrail join, hourly heatmap, top spenders |

### Run Order
```bash
python setup_server_side_tracking.py    # infrastructure
python server_side_tracking_demo.py     # demo + attribution report
```

### Key Design Decisions
- **Per-user AIPs** (not just per-tenant) — each user gets their own inference profile with `userId`, `group`, `tenant`, `department` tags. Cost Explorer can slice by any dimension.
- **`requestMetadata` set by gateway** — the demo simulates a server-side gateway injecting identity. In production, the CCWB auth Lambda sets this after validating the JWT, before forwarding to Bedrock.
- **Metadata-only logging** — `textDataDeliveryEnabled=False` keeps costs down while still capturing token counts and identity.
- **Athena as source of truth** — the SQL queries in `attribution_queries.sql` replace OTEL as the authoritative cost attribution layer.

### AWS Reference Solutions Used
- [Converse API requestMetadata](https://aws.amazon.com/blogs/machine-learning/cost-tracking-multi-tenant-model-inference-on-amazon-bedrock/) — AWS blog with Glue ETL → QuickSight pipeline
- [Multi-Tenant GenAI Gateway](https://aws.amazon.com/solutions/guidance/multi-tenant-generative-ai-gateway-with-cost-and-usage-tracking-on-aws/) — AWS Solutions Library reference architecture
- [Proactive Cost Sentry](https://aws.amazon.com/blogs/machine-learning/build-a-proactive-ai-cost-management-system-for-amazon-bedrock-part-2/) — Step Functions-based enforcement with custom CloudWatch metrics
- [Track and Limit Bedrock Usage by User](https://repost.aws/articles/ARoDnASCxDQyGFfaagReMZNw/how-to-track-and-limit-amazon-bedrock-usage-by-user) — re:Post guide covering AIPs, invocation logging, and gateway patterns
