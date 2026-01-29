# Session 4 - AWS Data Pipeline Implementation

This directory contains the AWS implementation of the retail data pipeline. The architecture uses:
- **S3** for data storage
- **RDS PostgreSQL** for the database (medallion architecture)
- **Lambda** for S3 event detection (NOT for running dbt)
- **dbt** runs locally and connects to AWS RDS via dbt-postgres adapter
- **SNS** for notifications
- **CloudWatch** for logging and monitoring
- **EventBridge** for scheduled triggers (optional)

## Architecture Overview

```
┌──────────────────────────────────────────────────────────────────────────────────┐
│                                     AWS CLOUD                                    │
│                                                                                  │
│   ┌──────────────┐      ┌──────────────┐      ┌──────────────┐      ┌────────┐   │
│   │ EventBridge  │─────>│    Lambda    │─────>│   S3 Bucket  │─────>│  SNS   │───┐
│   │  (Schedule)  │      │ (Pull/Check) │      │    (Data)    │      │ (Email)│   │
│   └──────────────┘      └──────────────┘      └──────▲───────┘      └────────┘   │
│                                                      │                   ▲       │
│   ┌──────────────┐      ┌──────────────┐             │                   │       │
│   │  S3 Event    │─────>│    Lambda    │─────────────┼───────────────────┘       │
│   │   Trigger    │      │   (Notify)   │             │                           │
│   └──────▲───────┘      └──────────────┘             │                           │
│          │                                           │                           │
└──────────┼───────────────────────────────────────────┼───────────────────────────┘
           │                                           │
    (S3 Notification)                         (Upload / API Call)
           │                                           │
┌──────────┴───────────────────────────────────────────┴───────────────────────────┐
│                              LOCAL DEVELOPMENT                                   │
│                                                                                  │
│  1. Setup:         initialize_rds.py  ────> [ Create Bronze Schema in RDS ]      │
│                                                                                  │
│  2. Ingestion:     ingest_s3_to_rds.py ───> [ Transform & Push to Bronze ]       │
│                                                                                  │
│  3. Transformation: dbt run (Manual)   ───> [ Create Silver & Gold in RDS ]      │
│                                                                                  │
└──────────────────────────────────────────────────────────────────────────────────┘
```

## Key Architectural Decision

**dbt runs locally, NOT in Lambda:**
- ✅ Lambda: Detects S3 upload events, sends SNS notifications
- ✅ dbt: Runs on local machine, connects to AWS RDS via dbt-postgres adapter
- ✅ Rationale: Lambda limitations (15-min timeout, dependency packaging), dbt complexity

## Prerequisites

### 1. AWS Account and CLI
```bash
# Install AWS CLI
brew install awscli  # macOS
# or
pip install awscli

# Configure AWS credentials
aws configure
# Enter: Access Key ID, Secret Access Key, Region, Output format
```

### 2. Required Tools
- install via uv 

```bash
cd sessions/session4/aws
uv venv
source .venv/bin/activate
uv pip install -r requirements.txt
```

- install in cli

```bash
# PostgreSQL client (for psql)
brew install postgresql  # macOS

# Python dependencies
pip install boto3 pandas openpyxl psycopg2-binary

# dbt (already installed from local setup)
pip install dbt-postgres==1.7.4
```

### 3. Permissions
Your AWS IAM user needs permissions for:
- CloudFormation (full access)
- S3 (create/delete buckets, upload/download objects)
- RDS (create/delete instances)
- Lambda (create/invoke functions)
- VPC/EC2 (create networking components)
- IAM (create roles for Lambda)
- CloudWatch Logs
- SNS (create topics, publish)
- EventBridge (create rules)

## Quick Start

### Step 1: Deploy AWS Infrastructure

```bash
cd aws

# Set environment variables
export AWS_REGION="us-east-1"
export DB_PASSWORD="YourSecurePassword123"
export DATA_BUCKET_NAME="retail-pipeline-data-session4-$(date +%s)"

# Deploy CloudFormation stack (takes 10-15 minutes)
bash scripts/deploy.sh

# Run the initialization
python3 aws/scripts/initialize_rds.py

# In case password not match, reset it
aws rds modify-db-instance \
  --db-instance-identifier retail-pipeline-session4-dev \
  --master-user-password YourSecurePassword123 \
  --apply-immediately \
  --region us-east-1

# after successful run of deploy.sh
# subscribe to sns
aws sns subscribe --topic-arn arn:aws:sns:us-east-1:6x6xx9530xx:retail-pipeline-session4-notifications --protocol email --notification-endpoint your-email@example.com
```

This will create:
- S3 bucket for data storage
- RDS PostgreSQL instance (publicly accessible)
- Lambda function for S3 event handling
- VPC with public/private subnets
- Security groups and IAM roles
- SNS topic for notifications
- CloudWatch log groups

### Step 2: Load Configuration

```bash
# Load generated configuration
source aws_config.env

# Verify configuration
cat aws_config.env
```

### Step 3: Test/validate service/Connection

```bash
# Test direct connection (auto created in deploy.sh)
bash scripts/test_rds_connection.sh

# Or manually
psql -h $AWS_RDS_HOST -p $AWS_RDS_PORT -U postgres -d retail_db
```

### Step 4: Upload Data to S3

```bash
# Upload Excel file to S3 (triggers Lambda)
cd scripts
bash upload_data.sh

# Lambda will automatically detect the upload and send SNS notification
```

### Step 5: Ingest Data from S3 to RDS

```bash
# Download from S3 and load to RDS bronze layer
cd scripts
python3 ingest_from_s3_to_rds.py \
    --s3-bucket $AWS_S3_BUCKET \
    --s3-key input/online_retail.xlsx \
    --db-host $AWS_RDS_HOST \
    --db-port $AWS_RDS_PORT \
    --db-name $AWS_RDS_DATABASE \
    --db-user $AWS_RDS_USER \
    --db-password $AWS_RDS_PASSWORD \
    --aws-region $AWS_REGION
```

### Step 6: Run dbt Transformations (Local → AWS RDS)

```bash
# Navigate to local dbt project
cd ../aws/dbt_project

# Test dbt connection to AWS RDS
export $(grep -v '^#' ../.env | xargs) && dbt debug --profiles-dir ../dbt_project --target aws
dbt debug --profiles-dir ../aws/dbt_project --target aws

# Run dbt models (creates silver and gold layers in RDS)
export $(grep -v '^#' ../.env | xargs) && dbt run --profiles-dir ../dbt_project --target aws

# Run dbt tests
export $(grep -v '^#' ../.env | xargs) && dbt test --profiles-dir ../dbt_project --target aws
```

### Step 7: Verify Data

```bash
# Check row counts in RDS
psql -h $AWS_RDS_HOST -p $AWS_RDS_PORT -U postgres -d retail_db -c "
SELECT 'bronze.raw_transactions' AS table_name, COUNT(*) AS row_count
FROM bronze.raw_transactions
UNION ALL
SELECT 'public_silver.dim_date', COUNT(*) FROM public_silver.dim_date
UNION ALL
SELECT 'public_silver.dim_product', COUNT(*) FROM public_silver.dim_product
UNION ALL
SELECT 'public_silver.fact_sales_daily', COUNT(*) FROM public_silver.fact_sales_daily
UNION ALL
SELECT 'public_gold.monthly_sales_summary', COUNT(*) FROM public_gold.monthly_sales_summary;
"
```

Expected results:
- bronze.raw_transactions: 541,897
- public_silver.dim_date: 305
- public_silver.dim_product: 4,069
- public_silver.fact_sales_daily: 305,476
- public_gold.monthly_sales_summary: 13

## End-to-End Testing

```bash
# Run comprehensive test suite
cd aws
bash scripts/test_pipeline.sh
```

This tests:
- ✅ AWS CLI connectivity
- ✅ S3 bucket access
- ✅ RDS instance accessibility
- ✅ Database connection
- ✅ Schema existence
- ✅ Lambda function deployment
- ✅ SNS topic configuration
- ✅ Data ingestion completion
- ✅ dbt transformation success

## Monitoring

### Lambda Logs
```bash
# Tail Lambda logs in real-time
aws logs tail /aws/lambda/${PROJECT_NAME}-s3-event-handler --follow

# Get recent logs
aws logs tail /aws/lambda/${PROJECT_NAME}-s3-event-handler --since 1h
```

### RDS Logs
```bash
# RDS logs are exported to CloudWatch
aws logs tail /aws/rds/instance/${PROJECT_NAME}-dev/postgresql --follow
```

### SNS Notifications
```bash
# Subscribe your email to SNS topic
aws sns subscribe \
    --topic-arn $AWS_SNS_TOPIC \
    --protocol email \
    --notification-endpoint your-email@example.com

# Confirm subscription in your email
```

## Scheduled Execution (Optional)

Enable EventBridge rule to run pipeline on schedule:

```bash
# Enable daily execution at 2 AM UTC
aws events enable-rule \
    --name ${PROJECT_NAME}-schedule \
    --region $AWS_REGION
```

When triggered, you'll receive SNS notification to run dbt locally.

## Cost Estimation

Approximate monthly costs (us-east-1, as of 2026):

| Service | Configuration | Monthly Cost |
|---------|--------------|--------------|
| RDS db.t3.micro | 20 GB storage | ~$15-20 |
| S3 Standard | < 5 GB | ~$0.50 |
| Lambda | < 1M invocations | Free tier |
| NAT Gateway | 1 instance | ~$32 |
| Data Transfer | < 10 GB out | ~$1 |
| CloudWatch Logs | < 5 GB | ~$2.50 |
| **Total** | | **~$50-55/month** |

**Cost optimization tips:**
- Stop RDS instance when not in use (reduces cost to ~$3/month for storage only)
- Use RDS instance in public subnet to avoid NAT Gateway charges
- Delete stack when not needed: `bash scripts/cleanup.sh`

## Cleanup

To delete all AWS resources:

```bash
cd aws
bash scripts/cleanup.sh
```

This will:
- Empty and delete S3 bucket
- Delete RDS instance (and all data)
- Delete Lambda functions
- Delete VPC and networking
- Delete CloudWatch logs
- Remove local configuration files

**⚠️ WARNING: This is irreversible!**

## Troubleshooting

### Cannot connect to RDS

**Problem:** Connection timeout or refused

**Solutions:**
1. Check security group allows your IP:
   ```bash
   # Update AllowedCIDR parameter
   export ALLOWED_CIDR="$(curl -s https://checkip.amazonaws.com)/32"
   bash scripts/deploy.sh  # Redeploy with new CIDR
   ```

2. Verify RDS is publicly accessible:
   ```bash
   aws rds describe-db-instances \
       --db-instance-identifier ${PROJECT_NAME}-dev \
       --query 'DBInstances[0].PubliclyAccessible'
   ```

3. Test with psql:
   ```bash
   PGPASSWORD=$AWS_RDS_PASSWORD psql \
       -h $AWS_RDS_HOST \
       -p 5432 \
       -U postgres \
       -d retail_db
   ```

### Lambda not triggered by S3

**Problem:** File uploaded to S3 but Lambda didn't run

**Solutions:**
1. Check S3 event notification configuration:
   ```bash
   aws s3api get-bucket-notification-configuration \
       --bucket $AWS_S3_BUCKET
   ```

2. Verify Lambda permission:
   ```bash
   aws lambda get-policy \
       --function-name ${PROJECT_NAME}-s3-event-handler
   ```

3. Check Lambda logs:
   ```bash
   aws logs tail /aws/lambda/${PROJECT_NAME}-s3-event-handler --since 1h
   ```

### dbt cannot connect to RDS

**Problem:** `dbt debug` fails with connection error

**Solutions:**
1. Verify environment variables:
   ```bash
   echo $AWS_RDS_HOST
   echo $AWS_RDS_PASSWORD
   ```

2. Test PostgreSQL connectivity:
   ```bash
   pg_isready -h $AWS_RDS_HOST -p 5432
   ```

3. Check dbt profile:
   ```bash
   cat aws/dbt_profile/profiles.yml
   ```

4. Run dbt debug with verbose output:
   ```bash
   dbt debug --profiles-dir ../aws/dbt_profile --target aws --debug
   ```

### CloudFormation stack creation failed

**Problem:** Stack rollback during deployment

**Solutions:**
1. Check CloudFormation events:
   ```bash
   aws cloudformation describe-stack-events \
       --stack-name $STACK_NAME \
       --max-items 20
   ```

2. Common issues:
   - Bucket name not unique (change DATA_BUCKET_NAME)
   - Insufficient IAM permissions
   - Resource limits exceeded

## Local vs AWS Comparison

| Aspect | Local | AWS |
|--------|-------|-----|
| **Database** | PostgreSQL (Docker) | RDS PostgreSQL |
| **Storage** | Local filesystem | S3 |
| **Compute** | Docker containers | Lambda + Local dbt |
| **Orchestration** | Cron + Python | SNS + Manual dbt |
| **Monitoring** | Log files | CloudWatch |
| **Cost** | Free (electricity) | ~$50/month |
| **Scalability** | Limited by machine | Cloud scalable |
| **Access** | localhost only | Internet accessible |
| **Backup** | Manual | Automated (RDS) |
| **Setup Time** | 5 minutes | 15 minutes |

## Next Steps

1. **Automation**: Create automated deployment scripts with AWS CLI
2. **Scheduling**: Set up automated dbt runs via EventBridge or cron
3. **Monitoring**: Add custom CloudWatch dashboards and alerts
4. **Security**: Implement AWS Secrets Manager for passwords
5. **Optimization**: Add incremental dbt models and performance tuning
6. **Documentation**: Generate and publish dbt documentation
7. **Cost Management**: Implement budget alerts and resource optimization

## Resources

- [AWS CloudFormation Documentation](https://docs.aws.amazon.com/cloudformation/)
- [AWS RDS PostgreSQL](https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/CHAP_PostgreSQL.html)
- [AWS Lambda Python](https://docs.aws.amazon.com/lambda/latest/dg/lambda-python.html)
- [dbt Documentation](https://docs.getdbt.com/)
- [dbt Postgres Adapter](https://docs.getdbt.com/reference/warehouse-setups/postgres-setup)

## Support

For issues or questions:
1. Check the [Troubleshooting](#troubleshooting) section
2. Review CloudFormation events and Lambda logs
3. Verify RDS connectivity with psql
4. Test dbt connection with `dbt debug`
