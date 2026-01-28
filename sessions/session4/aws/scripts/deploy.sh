#!/bin/bash
set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo "======================================"
echo "  Session 4 AWS Deployment Script"
echo "======================================"
echo ""

if ! command -v aws &> /dev/null; then
    echo -e "${RED}Error: AWS CLI not found.${NC}"
    exit 1
fi

AWS_REGION="${AWS_REGION:-us-east-1}"
STACK_NAME="${STACK_NAME:-retail-pipeline-session4}"
PROJECT_NAME="retail-pipeline-session4"
ENVIRONMENT="${ENVIRONMENT:-dev}"
DB_PASSWORD="${DB_PASSWORD:-MySecurePassword123}"
DATA_BUCKET_NAME="${DATA_BUCKET_NAME:-retail-pipeline-data-session4-$(date +%s)}"

CURRENT_IP=$(curl -s https://checkip.amazonaws.com)
ALLOWED_CIDR="${ALLOWED_CIDR:-${CURRENT_IP}/32}"

echo "Deployment Configuration:"
echo "  Stack Name: $STACK_NAME"
echo "  Region: $AWS_REGION"
echo "  Environment: $ENVIRONMENT"
echo "  Data Bucket: $DATA_BUCKET_NAME"
echo "  Allowed CIDR: $ALLOWED_CIDR"
echo ""

read -p "Continue with deployment? (yes/no): " confirm
[ "$confirm" != "yes" ] && exit 0

echo -e "${GREEN}Step 1: Deploying CloudFormation stack...${NC}"

aws cloudformation deploy \
  --template-file ../../infrastructure/cloudformation.yml \
  --stack-name "$STACK_NAME" \
  --parameter-overrides \
    ProjectName="$PROJECT_NAME" \
    Environment="$ENVIRONMENT" \
    DBPassword="$DB_PASSWORD" \
    DataBucketName="$DATA_BUCKET_NAME" \
    AllowedCIDR="$ALLOWED_CIDR" \
  --capabilities CAPABILITY_NAMED_IAM \
  --region "$AWS_REGION"

aws cloudformation wait stack-create-complete --stack-name "$STACK_NAME" --region "$AWS_REGION" || \
aws cloudformation wait stack-update-complete --stack-name "$STACK_NAME" --region "$AWS_REGION"

echo -e "${GREEN}✓ Stack ready${NC}"

echo -e "${GREEN}Step 2: Retrieving stack outputs...${NC}"

RDS_ENDPOINT=$(aws cloudformation describe-stacks --stack-name "$STACK_NAME" --region "$AWS_REGION" --query 'Stacks[0].Outputs[?OutputKey==`RDSEndpoint`].OutputValue' --output text)
RDS_PORT=$(aws cloudformation describe-stacks --stack-name "$STACK_NAME" --region "$AWS_REGION" --query 'Stacks[0].Outputs[?OutputKey==`RDSPort`].OutputValue' --output text)
S3_BUCKET=$(aws cloudformation describe-stacks --stack-name "$STACK_NAME" --region "$AWS_REGION" --query 'Stacks[0].Outputs[?OutputKey==`DataBucketName`].OutputValue' --output text)
SNS_TOPIC=$(aws cloudformation describe-stacks --stack-name "$STACK_NAME" --region "$AWS_REGION" --query 'Stacks[0].Outputs[?OutputKey==`SNSTopicArn`].OutputValue' --output text)
LAMBDA_ARN=$(aws cloudformation describe-stacks --stack-name "$STACK_NAME" --region "$AWS_REGION" --query 'Stacks[0].Outputs[?OutputKey==`LambdaFunctionArn`].OutputValue' --output text)

echo -e "${GREEN}Step 3: Waiting for RDS...${NC}"
aws rds wait db-instance-available \
  --db-instance-identifier "${PROJECT_NAME}-${ENVIRONMENT}" \
  --region "$AWS_REGION"

echo -e "${GREEN}Step 4: Writing aws_config.env...${NC}"

cat > ../aws_config.env <<EOF
AWS_REGION=$AWS_REGION
STACK_NAME=$STACK_NAME
PROJECT_NAME=$PROJECT_NAME
ENVIRONMENT=$ENVIRONMENT
AWS_RDS_HOST=$RDS_ENDPOINT
AWS_RDS_PORT=$RDS_PORT
AWS_RDS_PASSWORD=$DB_PASSWORD
AWS_RDS_DATABASE=retail_db
AWS_RDS_USER=postgres
AWS_S3_BUCKET=$S3_BUCKET
AWS_SNS_TOPIC=$SNS_TOPIC
AWS_LAMBDA_ARN=$LAMBDA_ARN
DBT_PROFILES_DIR=../dbt_profile
DBT_TARGET=aws
EOF

echo -e "${GREEN}✓ Config saved${NC}"

echo -e "${GREEN}Step 5: Initializing bronze schema...${NC}"
python3 initialize_rds.py

echo -e "${GREEN}Step 6: Creating test script...${NC}"

cat > test_rds_connection.sh <<'EOF'
#!/bin/bash
set -e
source ../aws_config.env

echo "Testing RDS connection..."
python3 - <<PYTHON_EOF
import os, psycopg2
conn = psycopg2.connect(
    host=os.getenv("AWS_RDS_HOST"),
    port=os.getenv("AWS_RDS_PORT"),
    user=os.getenv("AWS_RDS_USER"),
    password=os.getenv("AWS_RDS_PASSWORD"),
    dbname=os.getenv("AWS_RDS_DATABASE"),
)
cur = conn.cursor()
cur.execute("SELECT version();")
print("PostgreSQL version:", cur.fetchone()[0])
cur.execute("SELECT COUNT(*) FROM bronze.raw_transactions;")
print("Rows in bronze.raw_transactions:", cur.fetchone()[0])
cur.close()
conn.close()
PYTHON_EOF
EOF

chmod +x test_rds_connection.sh

echo ""
echo -e "${GREEN}Deployment Complete!${NC}"
echo ""
echo "Next steps:"
echo "  cd .."
echo "  source aws_config.env"
echo "  cd scripts"
echo "  bash test_rds_connection.sh"
