#!/bin/bash
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "======================================"
echo "  Upload Data to S3"
echo "======================================"
echo ""

# Load configuration
if [ -f "../aws_config.env" ]; then
    source ../aws_config.env
    echo -e "${GREEN}✓ Loaded configuration from aws_config.env${NC}"
else
    echo -e "${RED}Error: aws_config.env not found. Run deploy.sh first.${NC}"
    exit 1
fi

# Check for data file
DATA_FILE="${DATA_FILE:-../../data/online_retail.xlsx}"

if [ ! -f "$DATA_FILE" ]; then
    echo -e "${RED}Error: Data file not found at $DATA_FILE${NC}"
    echo "Please specify the correct path:"
    echo "  DATA_FILE=/path/to/online_retail.xlsx bash upload_data.sh"
    exit 1
fi

echo "Configuration:"
echo "  S3 Bucket: $AWS_S3_BUCKET"
echo "  Data File: $DATA_FILE"
echo "  File Size: $(du -h "$DATA_FILE" | cut -f1)"
echo ""

# Upload to S3
echo -e "${GREEN}Uploading data to S3...${NC}"
aws s3 cp "$DATA_FILE" \
    "s3://${AWS_S3_BUCKET}/input/online_retail.xlsx" \
    --region "$AWS_REGION" \
    --metadata "upload-date=$(date +%Y-%m-%d),source=local"

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Data uploaded successfully${NC}"
    echo ""
    echo "S3 Object: s3://${AWS_S3_BUCKET}/input/online_retail.xlsx"
    echo ""
    echo "Lambda function will be triggered automatically to detect this upload."
    echo ""
    # echo "Next steps:"
    # echo "1. Check Lambda logs:"
    # echo "   aws logs tail /aws/lambda/${PROJECT_NAME}-s3-event-handler --follow"
    # echo ""
    # echo "2. Load data from S3 to RDS bronze layer:"
    # echo "   cd ../local"
    # echo "   python3 scripts/ingest_from_s3.py"
    # echo ""
    # echo "3. Run dbt transformations targeting AWS RDS:"
    # echo "   cd ../local"
    # echo "   dbt run --profiles-dir ../aws/dbt_profile --target aws"
    # echo ""
    # echo "4. Verify data in RDS:"
    # echo "   bash ../aws/test_rds_connection.sh"
else
    echo -e "${RED}✗ Upload failed${NC}"
    exit 1
fi
