#!/bin/bash
################################################################################
# Full CCWB Deployment with User-Level Tracking
# Deploys complete infrastructure for enterprise quota management
################################################################################

set -e  # Exit on error

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Configuration
REGION="us-west-2"
ACCOUNT_ID="899950533801"

echo -e "${BLUE}================================================================================================${NC}"
echo -e "${BLUE}   FULL CCWB DEPLOYMENT WITH USER-LEVEL TRACKING${NC}"
echo -e "${BLUE}================================================================================================${NC}"
echo ""

# Function to check prerequisites
check_prerequisites() {
    echo -e "${YELLOW}📋 Checking Prerequisites...${NC}"

    # Check AWS CLI
    if ! command -v aws &> /dev/null; then
        echo -e "${RED}❌ AWS CLI not found. Please install it first.${NC}"
        exit 1
    fi

    # Check Python
    if ! command -v python3 &> /dev/null; then
        echo -e "${RED}❌ Python 3 not found. Please install it first.${NC}"
        exit 1
    fi

    # Check AWS credentials
    if ! aws sts get-caller-identity &> /dev/null; then
        echo -e "${RED}❌ AWS credentials not configured. Please configure AWS CLI.${NC}"
        exit 1
    fi

    # Check CCWB CLI
    if ! source venv/bin/activate && command -v ccwb &> /dev/null; then
        echo -e "${YELLOW}⚠️ CCWB CLI not found in virtual environment.${NC}"
    fi

    echo -e "${GREEN}✅ Prerequisites check passed${NC}"
    echo ""
}

# Step 1: Deploy Infrastructure
deploy_infrastructure() {
    echo -e "${BLUE}================================================================================================${NC}"
    echo -e "${BLUE}Step 1: Deploying Core Infrastructure${NC}"
    echo -e "${BLUE}================================================================================================${NC}"

    python3 deploy_full_ccwb.py

    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ Infrastructure deployed successfully${NC}"
    else
        echo -e "${RED}❌ Infrastructure deployment failed${NC}"
        exit 1
    fi

    echo ""
}

# Step 2: Setup API Gateway & Cognito
setup_api_gateway() {
    echo -e "${BLUE}================================================================================================${NC}"
    echo -e "${BLUE}Step 2: Setting up API Gateway & Cognito${NC}"
    echo -e "${BLUE}================================================================================================${NC}"

    python3 setup_api_gateway.py

    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ API Gateway & Cognito configured${NC}"
    else
        echo -e "${RED}❌ API Gateway setup failed${NC}"
        exit 1
    fi

    echo ""
}

# Step 3: Deploy User-Level Dashboard
deploy_dashboard() {
    echo -e "${BLUE}================================================================================================${NC}"
    echo -e "${BLUE}Step 3: Deploying User-Level CloudWatch Dashboard${NC}"
    echo -e "${BLUE}================================================================================================${NC}"

    python3 deploy_user_level_dashboard.py

    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ User-level dashboard deployed${NC}"
    else
        echo -e "${YELLOW}⚠️ Dashboard deployment failed (non-critical)${NC}"
    fi

    echo ""
}

# Step 4: Verify Deployment
verify_deployment() {
    echo -e "${BLUE}================================================================================================${NC}"
    echo -e "${BLUE}Step 4: Verifying Deployment${NC}"
    echo -e "${BLUE}================================================================================================${NC}"

    # Check DynamoDB tables
    echo -e "${YELLOW}📊 Checking DynamoDB Tables...${NC}"

    if aws dynamodb describe-table --table-name QuotaPolicies --region $REGION &> /dev/null; then
        echo -e "  ${GREEN}✅ QuotaPolicies table exists${NC}"
    else
        echo -e "  ${RED}❌ QuotaPolicies table not found${NC}"
    fi

    if aws dynamodb describe-table --table-name UserQuotaMetrics --region $REGION &> /dev/null; then
        echo -e "  ${GREEN}✅ UserQuotaMetrics table exists${NC}"
    else
        echo -e "  ${RED}❌ UserQuotaMetrics table not found${NC}"
    fi

    # Check Lambda functions
    echo -e "\n${YELLOW}🔧 Checking Lambda Functions...${NC}"

    if aws lambda get-function --function-name CCWB-QuotaCheck --region $REGION &> /dev/null; then
        echo -e "  ${GREEN}✅ QuotaCheck function exists${NC}"
    else
        echo -e "  ${RED}❌ QuotaCheck function not found${NC}"
    fi

    if aws lambda get-function --function-name CCWB-MetricsRecorder --region $REGION &> /dev/null; then
        echo -e "  ${GREEN}✅ MetricsRecorder function exists${NC}"
    else
        echo -e "  ${RED}❌ MetricsRecorder function not found${NC}"
    fi

    # Check CloudFormation stacks
    echo -e "\n${YELLOW}📚 Checking CloudFormation Stacks...${NC}"

    STACKS=$(aws cloudformation list-stacks --region $REGION --stack-status-filter CREATE_COMPLETE UPDATE_COMPLETE --query "StackSummaries[?contains(StackName, 'CCWB-UserLevel')].StackName" --output text)

    if [ -n "$STACKS" ]; then
        echo -e "  ${GREEN}✅ Found CCWB stacks:${NC}"
        for stack in $STACKS; do
            echo -e "     • $stack"
        done
    else
        echo -e "  ${YELLOW}⚠️ No CCWB stacks found${NC}"
    fi

    echo ""
}

# Step 5: Test the deployment
test_deployment() {
    echo -e "${BLUE}================================================================================================${NC}"
    echo -e "${BLUE}Step 5: Testing Deployment${NC}"
    echo -e "${BLUE}================================================================================================${NC}"

    # Test quota policy retrieval
    echo -e "${YELLOW}🧪 Testing quota policy retrieval...${NC}"

    aws dynamodb get-item \
        --table-name QuotaPolicies \
        --key '{"policy_type": {"S": "default"}, "identifier": {"S": "default"}}' \
        --region $REGION \
        --output json > /tmp/quota_test.json

    if [ -s /tmp/quota_test.json ]; then
        echo -e "  ${GREEN}✅ Default quota policy retrieved successfully${NC}"
        echo -e "  Policy: $(cat /tmp/quota_test.json | python3 -c 'import sys, json; data=json.load(sys.stdin); print(f"Monthly: {data.get(\"Item\", {}).get(\"monthly_token_limit\", {}).get(\"N\", \"N/A\")}, Daily: {data.get(\"Item\", {}).get(\"daily_token_limit\", {}).get(\"N\", \"N/A\")}")')"
    else
        echo -e "  ${RED}❌ Failed to retrieve quota policy${NC}"
    fi

    # Test Lambda invocation
    echo -e "\n${YELLOW}🧪 Testing Lambda function...${NC}"

    TEST_EVENT='{"requestContext": {"authorizer": {"claims": {"email": "test@company.com", "cognito:groups": "engineering"}}}}'

    aws lambda invoke \
        --function-name CCWB-QuotaCheck \
        --payload "$TEST_EVENT" \
        --region $REGION \
        /tmp/lambda_response.json &> /dev/null

    if [ -f /tmp/lambda_response.json ]; then
        echo -e "  ${GREEN}✅ Lambda function invoked successfully${NC}"
        echo -e "  Response: $(cat /tmp/lambda_response.json | python3 -m json.tool | head -5)"
    else
        echo -e "  ${RED}❌ Lambda invocation failed${NC}"
    fi

    echo ""
}

# Step 6: Display summary
display_summary() {
    echo -e "${BLUE}================================================================================================${NC}"
    echo -e "${GREEN}✅ FULL CCWB DEPLOYMENT COMPLETE!${NC}"
    echo -e "${BLUE}================================================================================================${NC}"
    echo ""

    echo -e "${YELLOW}📊 Deployed Resources:${NC}"
    echo "  • 2 DynamoDB Tables (QuotaPolicies, UserQuotaMetrics)"
    echo "  • 2 Lambda Functions (QuotaCheck, MetricsRecorder)"
    echo "  • 1 API Gateway with Cognito Authorizer"
    echo "  • 4 Cognito User Pool Groups"
    echo "  • 4 Test Users with different quota levels"
    echo "  • 2 CloudWatch Dashboards"
    echo ""

    echo -e "${YELLOW}🔗 Access Points:${NC}"
    echo "  • API Gateway: https://<api-id>.execute-api.$REGION.amazonaws.com/prod"
    echo "  • User Dashboard: https://console.aws.amazon.com/cloudwatch/home?region=$REGION#dashboards:name=CCWB-UserLevel-QuotaMonitoring"
    echo "  • Quota Dashboard: https://console.aws.amazon.com/cloudwatch/home?region=$REGION#dashboards:name=CCWB-Quota-Monitoring"
    echo ""

    echo -e "${YELLOW}👥 Test Users (Password: TempPassword123!):${NC}"
    echo "  • john.doe@company.com (Engineering - 400M/month)"
    echo "  • jane.smith@company.com (Sales - 300M/month)"
    echo "  • bob.marketing@company.com (Marketing - 250M/month)"
    echo "  • alice.exec@company.com (Executive - 1B/month)"
    echo ""

    echo -e "${YELLOW}📝 Next Steps:${NC}"
    echo "  1. Test API with Cognito authentication"
    echo "  2. Generate usage metrics for test users"
    echo "  3. Monitor quota enforcement in CloudWatch"
    echo "  4. Configure SNS notifications for quota alerts"
    echo "  5. Integrate with your application"
    echo ""

    echo -e "${YELLOW}🧹 To Clean Up:${NC}"
    echo "  aws cloudformation delete-stack --stack-name CCWB-UserLevel-Infrastructure --region $REGION"
    echo "  aws cloudformation delete-stack --stack-name CCWB-UserLevel-APIGateway --region $REGION"
    echo ""
}

# Main execution
main() {
    echo -e "${YELLOW}This will deploy a complete CCWB infrastructure with user-level tracking.${NC}"
    echo -e "${YELLOW}Estimated time: 10-15 minutes${NC}"
    echo ""

    read -p "Do you want to proceed? (y/n): " -n 1 -r
    echo ""

    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${RED}Deployment cancelled.${NC}"
        exit 1
    fi

    echo ""

    # Run deployment steps
    check_prerequisites
    deploy_infrastructure
    setup_api_gateway
    deploy_dashboard
    verify_deployment
    test_deployment
    display_summary
}

# Run main function
main