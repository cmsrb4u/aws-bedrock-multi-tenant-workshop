#!/usr/bin/env python3
"""
Implement User-Level Metrics using CloudWatch Logs Insights
Alternative approach when full CCWB deployment is not available

This script shows how to:
1. Parse CCWB Lambda logs for user email
2. Create metric filters for user-level tracking
3. Generate custom metrics from log patterns
"""

import boto3
import json
from datetime import datetime, timedelta
from typing import List, Dict, Any

# Configuration
REGION = "us-west-2"
LOG_GROUP_NAME = "/aws/lambda/ccwb-bedrock-proxy"  # Your CCWB Lambda log group
CUSTOM_NAMESPACE = "CCWB/UserMetrics"

class LogBasedUserMetrics:
    """
    Extract user-level metrics from CloudWatch Logs
    """

    def __init__(self):
        self.logs_client = boto3.client('logs', region_name=REGION)
        self.cloudwatch = boto3.client('cloudwatch', region_name=REGION)

    def create_metric_filters(self):
        """
        Create metric filters to automatically extract user metrics from logs
        """

        # Define metric filters for different user events
        filters = [
            {
                'filterName': 'UserTokenUsage',
                'filterPattern': '[timestamp, request_id, user_email, input_tokens, output_tokens, ...]',
                'metricTransformations': [
                    {
                        'metricName': 'UserInputTokens',
                        'metricNamespace': CUSTOM_NAMESPACE,
                        'metricValue': '$input_tokens',
                        'dimensions': {
                            'UserEmail': '$user_email'
                        }
                    },
                    {
                        'metricName': 'UserOutputTokens',
                        'metricNamespace': CUSTOM_NAMESPACE,
                        'metricValue': '$output_tokens',
                        'dimensions': {
                            'UserEmail': '$user_email'
                        }
                    }
                ]
            },
            {
                'filterName': 'UserAPICall',
                'filterPattern': '{ $.userEmail = * && $.eventType = "BedrockInvocation" }',
                'metricTransformations': [
                    {
                        'metricName': 'UserAPICallCount',
                        'metricNamespace': CUSTOM_NAMESPACE,
                        'metricValue': '1',
                        'dimensions': {
                            'UserEmail': '$.userEmail'
                        }
                    }
                ]
            },
            {
                'filterName': 'UserQuotaExceeded',
                'filterPattern': '{ $.eventType = "QuotaExceeded" && $.userEmail = * }',
                'metricTransformations': [
                    {
                        'metricName': 'QuotaExceededCount',
                        'metricNamespace': CUSTOM_NAMESPACE,
                        'metricValue': '1',
                        'dimensions': {
                            'UserEmail': '$.userEmail'
                        }
                    }
                ]
            }
        ]

        for filter_config in filters:
            try:
                # Create the metric filter
                self.logs_client.put_metric_filter(
                    logGroupName=LOG_GROUP_NAME,
                    filterName=filter_config['filterName'],
                    filterPattern=filter_config['filterPattern'],
                    metricTransformations=filter_config['metricTransformations']
                )
                print(f"✅ Created metric filter: {filter_config['filterName']}")
            except Exception as e:
                print(f"⚠️ Error creating filter {filter_config['filterName']}: {e}")

    def query_user_metrics(self, user_email: str, start_time: datetime, end_time: datetime) -> Dict[str, Any]:
        """
        Query CloudWatch Logs Insights for user-specific metrics
        """

        query = f"""
        fields @timestamp, @message
        | filter @message like /{user_email}/
        | parse @message /userEmail: (?<user>[^,]+), inputTokens: (?<input>\d+), outputTokens: (?<output>\d+)/
        | stats sum(input) as totalInput,
                sum(output) as totalOutput,
                count() as apiCalls
        """

        try:
            # Start the query
            response = self.logs_client.start_query(
                logGroupName=LOG_GROUP_NAME,
                startTime=int(start_time.timestamp()),
                endTime=int(end_time.timestamp()),
                queryString=query
            )

            query_id = response['queryId']

            # Wait for query to complete
            status = 'Running'
            while status == 'Running':
                response = self.logs_client.get_query_results(queryId=query_id)
                status = response['status']

            if status == 'Complete':
                results = response['results']
                if results:
                    return {
                        'user': user_email,
                        'totalInput': int(results[0][0]['value']) if results[0][0]['value'] else 0,
                        'totalOutput': int(results[0][1]['value']) if results[0][1]['value'] else 0,
                        'apiCalls': int(results[0][2]['value']) if results[0][2]['value'] else 0
                    }
        except Exception as e:
            print(f"Error querying logs for {user_email}: {e}")

        return {'user': user_email, 'totalInput': 0, 'totalOutput': 0, 'apiCalls': 0}

    def create_insights_dashboard_queries(self) -> List[Dict[str, str]]:
        """
        Create CloudWatch Insights queries for dashboard widgets
        """

        queries = [
            {
                'name': 'Top Users by Token Usage',
                'query': '''
                    fields @timestamp, @message
                    | parse @message /userEmail: (?<user>[^,]+), inputTokens: (?<input>\d+), outputTokens: (?<output>\d+)/
                    | filter ispresent(user)
                    | stats sum(input) + sum(output) as totalTokens by user
                    | sort totalTokens desc
                    | limit 10
                '''
            },
            {
                'name': 'User Token Usage Over Time',
                'query': '''
                    fields @timestamp, @message
                    | parse @message /userEmail: (?<user>[^,]+), inputTokens: (?<input>\d+), outputTokens: (?<output>\d+)/
                    | filter ispresent(user)
                    | stats sum(input) as inputTokens,
                            sum(output) as outputTokens
                            by bin(5m) as time, user
                    | sort time asc
                '''
            },
            {
                'name': 'User API Call Frequency',
                'query': '''
                    fields @timestamp, @message
                    | parse @message /userEmail: (?<user>[^,]+)/
                    | filter ispresent(user)
                    | stats count() as apiCalls by user, bin(1h) as hour
                    | sort hour desc
                '''
            },
            {
                'name': 'Quota Violations by User',
                'query': '''
                    fields @timestamp, @message
                    | filter @message like /QuotaExceeded/
                    | parse @message /userEmail: (?<user>[^,]+), quotaType: (?<type>[^,]+)/
                    | stats count() as violations by user, type
                    | sort violations desc
                '''
            },
            {
                'name': 'Average Token Usage per Request',
                'query': '''
                    fields @timestamp, @message
                    | parse @message /userEmail: (?<user>[^,]+), inputTokens: (?<input>\d+), outputTokens: (?<output>\d+)/
                    | filter ispresent(user)
                    | stats avg(input) as avgInput,
                            avg(output) as avgOutput,
                            count() as requests
                            by user
                '''
            }
        ]

        return queries

def update_lambda_for_structured_logging():
    """
    Sample Lambda code update to emit structured logs for parsing
    """

    lambda_update = '''
import json
import logging
import boto3
from datetime import datetime

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    """
    Enhanced CCWB Lambda with structured logging for user metrics
    """

    # Extract user information from the authenticated request
    user_email = event['requestContext']['authorizer']['claims']['email']
    tenant_id = event['requestContext']['authorizer']['claims']['custom:tenant_id']
    request_id = context.request_id

    # Log the request start
    logger.info(json.dumps({
        'eventType': 'BedrockInvocationStart',
        'requestId': request_id,
        'userEmail': user_email,
        'tenantId': tenant_id,
        'timestamp': datetime.utcnow().isoformat()
    }))

    try:
        # Call Bedrock
        bedrock_response = invoke_bedrock(event['body'])

        # Extract token usage
        input_tokens = bedrock_response['usage']['input_tokens']
        output_tokens = bedrock_response['usage']['output_tokens']
        total_tokens = input_tokens + output_tokens

        # Check quota
        quota_check = check_user_quota(user_email, total_tokens)

        # Log structured metrics
        logger.info(json.dumps({
            'eventType': 'BedrockInvocationComplete',
            'requestId': request_id,
            'userEmail': user_email,
            'tenantId': tenant_id,
            'inputTokens': input_tokens,
            'outputTokens': output_tokens,
            'totalTokens': total_tokens,
            'quotaRemaining': quota_check['remaining'],
            'quotaLimit': quota_check['limit'],
            'timestamp': datetime.utcnow().isoformat()
        }))

        # Log in parseable format for metric filters
        logger.info(f"METRICS: userEmail: {user_email}, inputTokens: {input_tokens}, outputTokens: {output_tokens}, requestId: {request_id}")

        if quota_check['exceeded']:
            logger.warning(json.dumps({
                'eventType': 'QuotaExceeded',
                'userEmail': user_email,
                'quotaType': quota_check['quota_type'],
                'limit': quota_check['limit'],
                'usage': quota_check['usage'],
                'timestamp': datetime.utcnow().isoformat()
            }))

        return bedrock_response

    except Exception as e:
        logger.error(json.dumps({
            'eventType': 'BedrockInvocationError',
            'requestId': request_id,
            'userEmail': user_email,
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }))
        raise
'''

    print("\n📝 Updated Lambda Code for Structured Logging:")
    print("=" * 60)
    print(lambda_update)
    print("=" * 60)

    return lambda_update

def create_insights_widgets_json(queries: List[Dict[str, str]]) -> str:
    """
    Create dashboard widgets using CloudWatch Logs Insights
    """

    widgets = []

    for i, query_config in enumerate(queries):
        x_position = (i % 2) * 12
        y_position = (i // 2) * 6

        widgets.append({
            "type": "log",
            "x": x_position,
            "y": y_position,
            "width": 12,
            "height": 6,
            "properties": {
                "query": f"SOURCE '{LOG_GROUP_NAME}' | {query_config['query']}",
                "region": REGION,
                "title": query_config['name'],
                "queryLanguage": "kusto"  # CloudWatch Insights Query Language
            }
        })

    dashboard_body = {"widgets": widgets}

    return json.dumps(dashboard_body)

def create_log_based_alarms():
    """
    Create CloudWatch alarms based on log metrics
    """

    cloudwatch = boto3.client('cloudwatch', region_name=REGION)

    alarms = [
        {
            'AlarmName': 'HighUserTokenUsage',
            'MetricName': 'UserInputTokens',
            'Namespace': CUSTOM_NAMESPACE,
            'Statistic': 'Sum',
            'Period': 3600,
            'EvaluationPeriods': 1,
            'Threshold': 50000,
            'ComparisonOperator': 'GreaterThanThreshold',
            'AlarmDescription': 'Alert when any user exceeds 50K tokens per hour'
        },
        {
            'AlarmName': 'FrequentQuotaViolations',
            'MetricName': 'QuotaExceededCount',
            'Namespace': CUSTOM_NAMESPACE,
            'Statistic': 'Sum',
            'Period': 3600,
            'EvaluationPeriods': 2,
            'Threshold': 5,
            'ComparisonOperator': 'GreaterThanThreshold',
            'AlarmDescription': 'Alert on repeated quota violations'
        }
    ]

    for alarm_config in alarms:
        try:
            cloudwatch.put_metric_alarm(**alarm_config)
            print(f"✅ Created alarm: {alarm_config['AlarmName']}")
        except Exception as e:
            print(f"⚠️ Error creating alarm {alarm_config['AlarmName']}: {e}")

def main():
    print("\n" + "="*80)
    print("🔍 IMPLEMENTING USER-LEVEL METRICS WITH CLOUDWATCH LOGS")
    print("="*80)

    log_metrics = LogBasedUserMetrics()

    print("\n📋 IMPLEMENTATION STEPS:")
    print("-" * 60)

    print("\n1️⃣ UPDATE LAMBDA FOR STRUCTURED LOGGING")
    print("-" * 40)
    update_lambda_for_structured_logging()

    print("\n2️⃣ CREATE METRIC FILTERS")
    print("-" * 40)
    print("Creating metric filters to extract user metrics from logs...")
    log_metrics.create_metric_filters()

    print("\n3️⃣ CLOUDWATCH INSIGHTS QUERIES")
    print("-" * 40)
    queries = log_metrics.create_insights_dashboard_queries()
    for query in queries:
        print(f"\n📊 {query['name']}:")
        print(query['query'])

    print("\n4️⃣ CREATE INSIGHTS-BASED DASHBOARD")
    print("-" * 40)
    dashboard_name = "CCWB-UserMetrics-LogsInsights"
    client = boto3.client('cloudwatch', region_name=REGION)

    try:
        dashboard_body = create_insights_widgets_json(queries)
        response = client.put_dashboard(
            DashboardName=dashboard_name,
            DashboardBody=dashboard_body
        )

        if response['ResponseMetadata']['HTTPStatusCode'] == 200:
            print(f"✅ Dashboard '{dashboard_name}' created successfully!")
            print(f"📊 View at: https://console.aws.amazon.com/cloudwatch/home?region={REGION}#dashboards:name={dashboard_name}")
    except Exception as e:
        print(f"❌ Error creating dashboard: {e}")

    print("\n5️⃣ CREATE LOG-BASED ALARMS")
    print("-" * 40)
    create_log_based_alarms()

    print("\n6️⃣ QUERY EXAMPLE USER METRICS")
    print("-" * 40)
    # Example: Query metrics for a specific user
    end_time = datetime.utcnow()
    start_time = end_time - timedelta(hours=24)

    user_metrics = log_metrics.query_user_metrics(
        "alice@marketing.com",
        start_time,
        end_time
    )
    print(f"User metrics for last 24 hours: {json.dumps(user_metrics, indent=2)}")

    print("\n✅ ADVANTAGES OF LOG-BASED APPROACH:")
    print("-" * 60)
    print("• No need to modify CCWB core infrastructure")
    print("• Can parse existing logs retroactively")
    print("• Flexible queries with CloudWatch Insights")
    print("• Can create custom metrics from any log pattern")
    print("• Cost-effective for moderate volume")

    print("\n⚠️ LIMITATIONS:")
    print("-" * 60)
    print("• Slight delay (1-2 minutes) for metrics")
    print("• Insights queries have cost per GB scanned")
    print("• Limited to 20 concurrent Insights queries")
    print("• Log retention affects historical data availability")

    print("\n🚀 BEST PRACTICES:")
    print("-" * 60)
    print("1. Use structured JSON logging for easier parsing")
    print("2. Include correlation IDs (requestId) in all log entries")
    print("3. Implement log sampling for high-volume users")
    print("4. Set up log retention policies (30-90 days)")
    print("5. Use metric math for complex calculations")
    print("6. Export critical metrics to S3 for long-term storage")

    print("\n💡 HYBRID APPROACH:")
    print("-" * 60)
    print("Combine both approaches for comprehensive monitoring:")
    print("• Use log-based metrics for immediate implementation")
    print("• Gradually migrate to custom metrics with full CCWB")
    print("• Keep Insights queries for ad-hoc analysis")
    print("• Use DynamoDB for quota enforcement")

if __name__ == "__main__":
    main()