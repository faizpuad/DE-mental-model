#!/bin/bash

set -e

echo "Deploying AWS Retail Data Pipeline..."

PROJECT_NAME=${PROJECT_NAME:-"retail-data-pipeline"}
REGION=${AWS_REGION:-"us-east-1"}
STACK_NAME="${PROJECT_NAME}-stack"

echo "Project: $PROJECT_NAME"
echo "Region: $REGION"
echo "Stack: $STACK_NAME"

echo "Step 1: Deploying CloudFormation stack..."
aws cloudformation create-stack \
  --stack-name $STACK_NAME \
  --template-body file://infrastructure/cloudformation-template.yaml \
  --parameters \
    ParameterKey=ProjectName,ParameterValue=$PROJECT_NAME \
    ParameterKey=DBName,ParameterValue=retail_db \
    ParameterKey=DBUsername,ParameterValue=retail_admin \
    ParameterKey=DBPassword,ParameterValue=$DB_PASSWORD \
  --capabilities CAPABILITY_NAMED_IAM \
  --region $REGION

echo "Waiting for stack creation..."
aws cloudformation wait stack-create-complete \
  --stack-name $STACK_NAME \
  --region $REGION

echo "Step 2: Getting stack outputs..."
DATA_BUCKET=$(aws cloudformation describe-stacks \
  --stack-name $STACK_NAME \
  --query 'Stacks[0].Outputs[?OutputKey==`DataBucketName`].OutputValue' \
  --output text \
  --region $REGION)

LAMBDA_BUCKET=$(aws cloudformation describe-stacks \
  --stack-name $STACK_NAME \
  --query 'Stacks[0].Outputs[?OutputKey==`LambdaBucketName`].OutputValue' \
  --output text \
  --region $REGION)

DB_ENDPOINT=$(aws cloudformation describe-stacks \
  --stack-name $STACK_NAME \
  --query 'Stacks[0].Outputs[?OutputKey==`DatabaseEndpoint`].OutputValue' \
  --output text \
  --region $REGION)

echo "Data Bucket: $DATA_BUCKET"
echo "Lambda Bucket: $LAMBDA_BUCKET"
echo "Database Endpoint: $DB_ENDPOINT"

echo "Step 3: Packaging Lambda functions..."
cd lambdas

pip install -r ../scripts/requirements.txt -t packages

for lambda in ingestion_function transformation_function; do
  echo "Packaging $lambda..."
  cd $lambda
  zip -r ../../deployment/${lambda}.zip . -x \*__pycache__\* || true
  cd ..
  cp -r packages ${lambda}/
  cd ${lambda}
  zip -ur ../../deployment/${lambda}.zip .
  cd ..
  rm -rf packages
done

cd ..

echo "Step 4: Uploading Lambda packages to S3..."
for lambda_zip in deployment/*.zip; do
  echo "Uploading $lambda_zip..."
  aws s3 cp $lambda_zip s3://$LAMBDA_BUCKET/lambda/
done

echo "Step 5: Deploying Lambda functions..."
aws lambda create-function \
  --function-name ingestion-function \
  --runtime python3.11 \
  --role arn:aws:iam::ACCOUNT_ID:role/lambda-execution-role \
  --handler ingestion_function.lambda_handler \
  --code S3Bucket=$LAMBDA_BUCKET,S3Key=lambda/ingestion_function.zip \
  --timeout 300 \
  --memory-size 512 \
  --environment Variables={S3_BUCKET=$DATA_BUCKET,DB_HOST=$DB_ENDPOINT,DB_NAME=retail_db,DB_USER=retail_admin,DB_PASSWORD=$DB_PASSWORD} \
  --region $REGION || aws lambda update-function-code \
    --function-name ingestion-function \
    --s3-bucket $LAMBDA_BUCKET \
    --s3-key lambda/ingestion_function.zip \
    --region $REGION

aws lambda create-function \
  --function-name transformation-function \
  --runtime python3.11 \
  --role arn:aws:iam::ACCOUNT_ID:role/lambda-execution-role \
  --handler transformation_function.lambda_handler \
  --code S3Bucket=$LAMBDA_BUCKET,S3Key=lambda/transformation_function.zip \
  --timeout 600 \
  --memory-size 1024 \
  --environment Variables={DB_HOST=$DB_ENDPOINT,DB_NAME=retail_db,DB_USER=retail_admin,DB_PASSWORD=$DB_PASSWORD} \
  --region $REGION || aws lambda update-function-code \
    --function-name transformation-function \
    --s3-bucket $LAMBDA_BUCKET \
    --s3-key lambda/transformation_function.zip \
    --region $REGION

echo "Step 6: Creating Step Functions state machine..."
STATE_MACHINE_ARN=$(aws cloudformation describe-stacks \
  --stack-name $STACK_NAME \
  --query 'Stacks[0].Outputs[?OutputKey==`StateMachineArn`].OutputValue' \
  --output text \
  --region $REGION)

sed "s/REGION/$REGION/g; s/ACCOUNT_ID/$(aws sts get-caller-identity --query Account --output text)/g" \
  step_functions/state-machine.json > /tmp/state-machine.json

aws stepfunctions create-state-machine \
  --name "${PROJECT_NAME}-statemachine" \
  --definition file:///tmp/state-machine.json \
  --role-arn arn:aws:iam::ACCOUNT_ID:role/states-execution-role \
  --region $REGION || aws stepfunctions update-state-machine \
    --state-machine-arn $STATE_MACHINE_ARN \
    --definition file:///tmp/state-machine.json \
    --role-arn arn:aws:iam::ACCOUNT_ID:role/states-execution-role \
    --region $REGION

echo "Step 7: Creating EventBridge schedule rule..."
aws events put-rule \
  --name "${PROJECT_NAME}-schedule" \
  --schedule-expression "cron(0 2 * * ? *)" \
  --state ENABLED \
  --region $REGION

aws lambda add-permission \
  --function-name ingestion-function \
  --statement-id "EventBridgeTrigger" \
  --action "lambda:InvokeFunction" \
  --principal events.amazonaws.com \
  --source-arn arn:aws:events:${REGION}:$(aws sts get-caller-identity --query Account --output text):rule/${PROJECT_NAME}-schedule \
  --region $REGION

aws events put-targets \
  --rule "${PROJECT_NAME}-schedule" \
  --targets "Id=1,Arn=arn:aws:lambda:${REGION}:$(aws sts get-caller-identity --query Account --output text):function:ingestion-function" \
  --region $REGION

echo "Deployment completed successfully!"
echo "State Machine ARN: $STATE_MACHINE_ARN"
echo "Schedule Rule: ${PROJECT_NAME}-schedule (daily at 2 AM UTC)"
