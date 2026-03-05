-- ============================================================================
-- Server-Side Attribution Queries for Amazon Bedrock
-- ============================================================================
-- Prerequisites:
--   1. Bedrock model invocation logging enabled → S3
--   2. Glue crawler run over the S3 bucket to create table
--   3. requestMetadata set by server-side gateway (not client)
-- ============================================================================

-- ────────────────────────────────────────────────────────────────────────────
-- TABLE CREATION: Create Glue table over Bedrock invocation logs in S3
-- Run this once, or use a Glue Crawler to auto-detect schema
-- ────────────────────────────────────────────────────────────────────────────
CREATE EXTERNAL TABLE IF NOT EXISTS bedrock_invocation_logs (
  schematype         STRING,
  schemaversion      STRING,
  timestamp          STRING,
  accountid          STRING,
  region             STRING,
  requestid          STRING,
  operation          STRING,
  modelid            STRING,
  inputtokencount    INT,
  outputtokencount   INT,
  inputcontenttype   STRING,
  outputcontenttype  STRING,
  requestmetadata    MAP<STRING, STRING>,
  identity           STRUCT<arn: STRING>
)
ROW FORMAT SERDE 'org.openx.data.jsonserde.JsonSerDe'
LOCATION 's3://YOUR_BUCKET/invocation-logs/'
TBLPROPERTIES ('has_encrypted_data'='false');


-- ────────────────────────────────────────────────────────────────────────────
-- QUERY 1: Per-user token usage from requestMetadata
-- Source of truth for user attribution — fully server-side
-- ────────────────────────────────────────────────────────────────────────────
SELECT
  requestmetadata['userId']     AS user_id,
  requestmetadata['groupId']    AS group_id,
  requestmetadata['tenantId']   AS tenant_id,
  requestmetadata['department'] AS department,
  modelid,
  count(*)                      AS invocations,
  sum(inputtokencount)          AS input_tokens,
  sum(outputtokencount)         AS output_tokens,
  sum(inputtokencount + outputtokencount) AS total_tokens
FROM bedrock_invocation_logs
WHERE requestmetadata['source'] = 'server-side-gateway'
GROUP BY 1, 2, 3, 4, 5
ORDER BY total_tokens DESC;


-- ────────────────────────────────────────────────────────────────────────────
-- QUERY 2: Daily cost estimate by user
-- Adjust per-token prices for your model and pricing tier
-- ────────────────────────────────────────────────────────────────────────────
SELECT
  date_trunc('day', from_iso8601_timestamp(timestamp)) AS day,
  requestmetadata['userId']   AS user_id,
  requestmetadata['groupId']  AS group_id,
  count(*)                    AS invocations,
  sum(inputtokencount)        AS input_tokens,
  sum(outputtokencount)       AS output_tokens,
  -- Claude Opus 4.6 on-demand pricing (update as needed)
  round(sum(inputtokencount)  * 15.0 / 1000000, 4) AS input_cost_usd,
  round(sum(outputtokencount) * 75.0 / 1000000, 4) AS output_cost_usd,
  round(
    sum(inputtokencount)  * 15.0 / 1000000 +
    sum(outputtokencount) * 75.0 / 1000000, 4
  ) AS total_cost_usd
FROM bedrock_invocation_logs
GROUP BY 1, 2, 3
ORDER BY day DESC, total_cost_usd DESC;


-- ────────────────────────────────────────────────────────────────────────────
-- QUERY 3: Group-level aggregation for department chargebacks
-- ────────────────────────────────────────────────────────────────────────────
SELECT
  requestmetadata['groupId']    AS group_id,
  requestmetadata['tenantId']   AS tenant_id,
  requestmetadata['department'] AS department,
  count(DISTINCT requestmetadata['userId']) AS unique_users,
  count(*)                      AS invocations,
  sum(inputtokencount + outputtokencount) AS total_tokens,
  round(
    sum(inputtokencount)  * 15.0 / 1000000 +
    sum(outputtokencount) * 75.0 / 1000000, 2
  ) AS total_cost_usd
FROM bedrock_invocation_logs
WHERE requestmetadata['source'] = 'server-side-gateway'
GROUP BY 1, 2, 3
ORDER BY total_cost_usd DESC;


-- ────────────────────────────────────────────────────────────────────────────
-- QUERY 4: Combined CloudTrail + Invocation Logs (full attribution)
-- Join on requestId for IAM identity + token counts
-- Requires CloudTrail data events enabled for Bedrock
-- ────────────────────────────────────────────────────────────────────────────
SELECT
  regexp_extract(ct.useridentity.arn, 'u=([^|]+)', 1) AS user_id,
  regexp_extract(ct.useridentity.arn, 'g=([^|]+)', 1) AS group_id,
  bil.modelid,
  count(*)                      AS invocations,
  sum(bil.inputtokencount)      AS input_tokens,
  sum(bil.outputtokencount)     AS output_tokens,
  round(
    sum(bil.inputtokencount)  * 15.0 / 1000000 +
    sum(bil.outputtokencount) * 75.0 / 1000000, 4
  ) AS total_cost_usd
FROM cloudtrail_logs ct
JOIN bedrock_invocation_logs bil
  ON ct.requestid = bil.requestid
WHERE ct.eventsource = 'bedrock.amazonaws.com'
  AND ct.eventname IN ('InvokeModel', 'Converse')
GROUP BY 1, 2, 3
ORDER BY total_cost_usd DESC;


-- ────────────────────────────────────────────────────────────────────────────
-- QUERY 5: Hourly usage heatmap (identify peak usage patterns)
-- ────────────────────────────────────────────────────────────────────────────
SELECT
  date_trunc('hour', from_iso8601_timestamp(timestamp)) AS hour,
  requestmetadata['userId'] AS user_id,
  count(*)                  AS invocations,
  sum(inputtokencount + outputtokencount) AS total_tokens
FROM bedrock_invocation_logs
WHERE from_iso8601_timestamp(timestamp) > current_timestamp - interval '7' day
GROUP BY 1, 2
ORDER BY hour DESC, total_tokens DESC;


-- ────────────────────────────────────────────────────────────────────────────
-- QUERY 6: Top users by spend (last 30 days)
-- ────────────────────────────────────────────────────────────────────────────
SELECT
  requestmetadata['userId']   AS user_id,
  requestmetadata['groupId']  AS group_id,
  count(*)                    AS invocations,
  sum(inputtokencount)        AS input_tokens,
  sum(outputtokencount)       AS output_tokens,
  round(
    sum(inputtokencount)  * 15.0 / 1000000 +
    sum(outputtokencount) * 75.0 / 1000000, 2
  ) AS total_cost_usd,
  round(avg(outputtokencount), 0) AS avg_output_per_call
FROM bedrock_invocation_logs
WHERE from_iso8601_timestamp(timestamp) > current_timestamp - interval '30' day
GROUP BY 1, 2
ORDER BY total_cost_usd DESC
LIMIT 20;
