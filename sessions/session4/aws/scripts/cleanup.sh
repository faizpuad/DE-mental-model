#!/bin/bash
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "======================================"
echo "  AWS Infrastructure Cleanup"
echo "======================================"
echo ""

# Load configuration
if [ -f "../aws_config.env" ]; then
    source ../aws_config.env
    echo -e "${GREEN}✓ Loaded configuration from aws_config.env${NC}"
else
    echo -e "${YELLOW}Warning: aws_config.env not found. Using defaults${NC}"
    STACK_NAME="${STACK_NAME:-retail-pipeline-session4}"
    AWS_REGION="${AWS_REGION:-us-east-1}"
fi

echo "Cleanup Configuration:"
echo "  Stack Name: $STACK_NAME"
echo "  Region: $AWS_REGION"
echo ""

echo -e "${RED}WARNING: This will delete all AWS resources including:${NC}"
echo "  - S3 Bucket and all data"
echo "  - RDS PostgreSQL instance and all data"
echo "  - Lambda functions"
echo "  - VPC and networking components"
echo "  - SNS topics and subscriptions"
echo "  - EventBridge rules"
echo "  - CloudWatch logs"
echo ""
read -p "Are you sure you want to continue? (yes/no): " confirm

if [ "$confirm" != "yes" ]; then
    echo "Cleanup cancelled."
    exit 0
fi

# Step 1: Drop Python-created RDS schema/tables (if RDS is still alive)
if [ -n "$AWS_RDS_HOST" ] && [ -n "$AWS_RDS_DATABASE" ]; then
    echo ""
    echo -e "${YELLOW}Step 1: Dropping RDS bronze schema (if exists)...${NC}"
    python3 - <<PYTHON_EOF || echo "RDS schema cleanup skipped (RDS may be deleted)"
import os
import psycopg2

try:
    conn = psycopg2.connect(
        host=os.getenv("AWS_RDS_HOST"),
        port=os.getenv("AWS_RDS_PORT", "5432"),
        user=os.getenv("AWS_RDS_USER", "postgres"),
        password=os.getenv("AWS_RDS_PASSWORD"),
        dbname=os.getenv("AWS_RDS_DATABASE")
    )
    conn.autocommit = True
    cur = conn.cursor()
    cur.execute("DROP SCHEMA IF EXISTS bronze CASCADE;")
    print("✓ Bronze schema dropped")
    cur.close()
    conn.close()
except Exception as e:
    print("⚠ RDS schema cleanup skipped:", e)
PYTHON_EOF
    echo -e "${GREEN}✓ RDS schema cleanup step complete${NC}"
fi

# Step 2: Empty S3 bucket first
if [ -n "$AWS_S3_BUCKET" ]; then
    echo ""
    echo -e "${YELLOW}Step 2: Emptying S3 bucket...${NC}"
    aws s3 rm "s3://${AWS_S3_BUCKET}" \
        --recursive \
        --region "$AWS_REGION" \
        2>/dev/null || echo "Bucket already empty or doesn't exist"
    echo -e "${GREEN}✓ S3 bucket emptied${NC}"
fi

# Step 3: Delete CloudFormation stack
echo ""
echo -e "${YELLOW}Step 3: Deleting CloudFormation stack...${NC}"
aws cloudformation delete-stack \
    --stack-name "$STACK_NAME" \
    --region "$AWS_REGION"

echo "Waiting for stack deletion (this may take several minutes)..."
aws cloudformation wait stack-delete-complete \
    --stack-name "$STACK_NAME" \
    --region "$AWS_REGION" \
    2>/dev/null || {
        echo -e "${YELLOW}Note: Stack may have already been deleted${NC}"
    }
echo -e "${GREEN}✓ CloudFormation stack deleted${NC}"

# Step 4: Cleanup leftover Lambda function if exists (manual delete)
if [ -n "$AWS_LAMBDA_ARN" ]; then
    echo ""
    echo -e "${YELLOW}Step 4: Deleting Lambda function (if exists)...${NC}"
    aws lambda delete-function \
        --function-name "$AWS_LAMBDA_ARN" \
        --region "$AWS_REGION" 2>/dev/null || echo "Lambda already deleted"
    echo -e "${GREEN}✓ Lambda cleanup complete${NC}"
fi

# Step 5: Cleanup leftover SNS topic if exists
if [ -n "$AWS_SNS_TOPIC" ]; then
    echo ""
    echo -e "${YELLOW}Step 5: Deleting SNS topic (if exists)...${NC}"
    aws sns delete-topic \
        --topic-arn "$AWS_SNS_TOPIC" \
        --region "$AWS_REGION" 2>/dev/null || echo "SNS topic already deleted"
    echo -e "${GREEN}✓ SNS cleanup complete${NC}"
fi

# Step 6: Delete leftover EventBridge rules (optional, only if used)
echo ""
echo -e "${YELLOW}Step 6: Cleaning up EventBridge rules (if any)...${NC}"
RULES=$(aws events list-rules --region "$AWS_REGION" --query "Rules[?starts_with(Name,'${PROJECT_NAME}')].Name" --output text)
for rule in $RULES; do
    aws events delete-rule --name "$rule" --region "$AWS_REGION" --force
    echo "  - Deleted EventBridge rule: $rule"
done
echo -e "${GREEN}✓ EventBridge cleanup complete${NC}"

# Step 7: Remove local configuration files
echo ""
echo -e "${YELLOW}Step 7: Cleaning up local configuration files...${NC}"
if [ -f "../aws_config.env" ]; then
    rm ../aws_config.env
    echo "  - Removed aws_config.env"
fi
if [ -f "../test_rds_connection.sh" ]; then
    rm ../test_rds_connection.sh
    echo "  - Removed test_rds_connection.sh"
fi
echo -e "${GREEN}✓ Local files cleaned up${NC}"

echo ""
echo -e "${GREEN}======================================"
echo "  Cleanup Complete!"
echo "======================================${NC}"
echo ""
echo "All AWS resources and local artifacts have been deleted."
echo ""
echo "To redeploy:"
echo "  bash aws/scripts/deploy.sh"
