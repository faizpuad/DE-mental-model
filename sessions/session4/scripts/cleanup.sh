#!/bin/bash

set -e

PROJECT_NAME=${PROJECT_NAME:-"retail-data-pipeline"}
REGION=${AWS_REGION:-"us-east-1"}
STACK_NAME="${PROJECT_NAME}-stack"

echo "Cleanup AWS Retail Data Pipeline..."
echo "Project: $PROJECT_NAME"
echo "Region: $REGION"
echo "Stack: $STACK_NAME"
echo ""

echo "Step 1: Deleting CloudFormation stack..."
aws cloudformation delete-stack \
  --stack-name $STACK_NAME \
  --region $REGION

echo "Waiting for stack deletion..."
aws cloudformation wait stack-delete-complete \
  --stack-name $STACK_NAME \
  --region $REGION || echo "Stack deletion timed out or failed"

echo "Step 2: Getting S3 bucket names..."
DATA_BUCKET="${PROJECT_NAME}-data"
LAMBDA_BUCKET="${PROJECT_NAME}-lambda"

echo "Step 3: Emptying and deleting S3 buckets..."

if aws s3 ls s3://$DATA_BUCKET --region $REGION 2>/dev/null; then
    echo "  Emptying $DATA_BUCKET..."
    aws s3 rm s3://$DATA_BUCKET --recursive --region $REGION
    
    echo "  Deleting $DATA_BUCKET..."
    aws s3 rb s3://$DATA_BUCKET --region $REGION
else
    echo "  $DATA_BUCKET does not exist or is already deleted"
fi

if aws s3 ls s3://$LAMBDA_BUCKET --region $REGION 2>/dev/null; then
    echo "  Emptying $LAMBDA_BUCKET..."
    aws s3 rm s3://$LAMBDA_BUCKET --recursive --region $REGION
    
    echo "  Deleting $LAMBDA_BUCKET..."
    aws s3 rb s3://$LAMBDA_BUCKET --region $REGION
else
    echo "  $LAMBDA_BUCKET does not exist or is already deleted"
fi

echo "Step 4: Checking for orphaned resources..."

if aws lambda get-function --function-name ingestion-function --region $REGION 2>/dev/null; then
    echo "  Deleting orphaned ingestion-function..."
    aws lambda delete-function --function-name ingestion-function --region $REGION
fi

if aws lambda get-function --function-name transformation-function --region $REGION 2>/dev/null; then
    echo "  Deleting orphaned transformation-function..."
    aws lambda delete-function --function-name transformation-function --region $REGION
fi

if aws stepfunctions describe-state-machine --state-machine-arn "arn:aws:states:${REGION}:$(aws sts get-caller-identity --query Account --output text):stateMachine:${PROJECT_NAME}-statemachine" --region $REGION 2>/dev/null; then
    echo "  Deleting orphaned state machine..."
    aws stepfunctions delete-state-machine --state-machine-arn "arn:aws:states:${REGION}:$(aws sts get-caller-identity --query Account --output text):stateMachine:${PROJECT_NAME}-statemachine" --region $REGION
fi

if aws events list-rules --name-prefix "${PROJECT_NAME}-schedule" --region $REGION 2>/dev/null | grep -q "${PROJECT_NAME}-schedule"; then
    echo "  Deleting orphaned EventBridge rule..."
    RULE_ARN=$(aws events list-rules --name-prefix "${PROJECT_NAME}-schedule" --region $REGION --query "Rules[?Name=='${PROJECT_NAME}-schedule'].Arn" --output text)
    
    LAMBDA_ARN=$(aws lambda get-function --function-name ingestion-function --region $REGION --query 'Configuration.FunctionArn' --output text 2>/dev/null || echo "")
    
    if [ -n "$LAMBDA_ARN" ]; then
        aws events remove-targets --rule "${PROJECT_NAME}-schedule" --ids "1" --region $REGION 2>/dev/null || true
        aws lambda remove-permission --function-name ingestion-function --statement-id "EventBridgeTrigger" --region $REGION 2>/dev/null || true
    fi
    
    aws events delete-rule --name "${PROJECT_NAME}-schedule" --region $REGION
fi

echo "Step 5: Cleaning up CloudWatch log groups..."
LOG_GROUPS=(
    "/aws/lambda/ingestion-function"
    "/aws/lambda/transformation-function"
)

for log_group in "${LOG_GROUPS[@]}"; do
    if aws logs describe-log-groups --log-group-name-prefix "$log_group" --region $REGION 2>/dev/null | grep -q "$log_group"; then
        echo "  Deleting log group: $log_group"
        aws logs delete-log-group --log-group-name "$log_group" --region $REGION
    fi
done

echo ""
echo "Cleanup completed successfully!"
echo "All resources for project '$PROJECT_NAME' have been deleted."
echo ""
echo "Note: Some resources may take a few minutes to fully disappear from AWS console."
