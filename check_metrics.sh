#!/bin/bash

# Quick script to check if CloudWatch metrics are available for tenant profiles

echo "================================================"
echo "🔍 Checking CloudWatch Metrics Availability"
echo "================================================"
echo ""

echo "Tenant A (Marketing) - Profile ID: 5gematyf83m0"
echo "------------------------------------------------"
METRICS_A=$(aws cloudwatch list-metrics \
  --namespace AWS/Bedrock \
  --dimensions Name=InferenceProfileId,Value=5gematyf83m0 \
  --region us-west-2 \
  --query 'Metrics[*].MetricName' \
  --output text)

if [ -z "$METRICS_A" ]; then
    echo "⏳ No metrics yet (still propagating...)"
else
    echo "✅ Metrics available: $METRICS_A"
fi

echo ""
echo "Tenant B (Sales) - Profile ID: yku79b5wumnr"
echo "------------------------------------------------"
METRICS_B=$(aws cloudwatch list-metrics \
  --namespace AWS/Bedrock \
  --dimensions Name=InferenceProfileId,Value=yku79b5wumnr \
  --region us-west-2 \
  --query 'Metrics[*].MetricName' \
  --output text)

if [ -z "$METRICS_B" ]; then
    echo "⏳ No metrics yet (still propagating...)"
else
    echo "✅ Metrics available: $METRICS_B"
fi

echo ""
echo "================================================"
echo "💡 Note: Metrics typically appear 3-5 minutes after API calls"
echo "   Run this script again in a few minutes if no metrics shown"
echo "================================================"
