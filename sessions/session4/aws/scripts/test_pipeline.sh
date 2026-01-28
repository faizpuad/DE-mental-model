#!/bin/bash
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "======================================"
echo "  End-to-End Pipeline Test"
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

TEST_RESULTS=()
TESTS_PASSED=0
TESTS_FAILED=0

# Function to run a test
run_test() {
    local test_name="$1"
    local test_command="$2"

    echo ""
    echo -e "${YELLOW}Testing: $test_name${NC}"

    if eval "$test_command" > /dev/null 2>&1; then
        echo -e "${GREEN}✓ PASSED${NC}"
        TEST_RESULTS+=("✓ $test_name")
        ((TESTS_PASSED++))
        return 0
    else
        echo -e "${RED}✗ FAILED${NC}"
        TEST_RESULTS+=("✗ $test_name")
        ((TESTS_FAILED++))
        return 1
    fi
}

echo "Running comprehensive pipeline tests..."
echo ""

# Test 1: AWS CLI connectivity
run_test "AWS CLI connectivity" "aws sts get-caller-identity"

# Test 2: S3 bucket exists
run_test "S3 bucket exists" "aws s3 ls s3://${AWS_S3_BUCKET}/"

# Test 3: RDS instance accessible
run_test "RDS instance accessible" "PGPASSWORD=${AWS_RDS_PASSWORD} pg_isready -h ${AWS_RDS_HOST} -p ${AWS_RDS_PORT}"

# Test 4: RDS database connection
run_test "RDS database connection" "PGPASSWORD=${AWS_RDS_PASSWORD} psql -h ${AWS_RDS_HOST} -p ${AWS_RDS_PORT} -U ${AWS_RDS_USER} -d ${AWS_RDS_DATABASE} -c 'SELECT 1;'"

# Test 5: Bronze schema exists
run_test "Bronze schema exists" "PGPASSWORD=${AWS_RDS_PASSWORD} psql -h ${AWS_RDS_HOST} -p ${AWS_RDS_PORT} -U ${AWS_RDS_USER} -d ${AWS_RDS_DATABASE} -c 'SELECT schema_name FROM information_schema.schemata WHERE schema_name = '\''bronze'\'';' | grep bronze"

# Test 6: Lambda function exists
run_test "Lambda function exists" "aws lambda get-function --function-name ${PROJECT_NAME}-s3-event-handler --region ${AWS_REGION}"

# Test 7: SNS topic exists
run_test "SNS topic exists" "aws sns get-topic-attributes --topic-arn ${AWS_SNS_TOPIC} --region ${AWS_REGION}"

# Test 8: Check if data exists in S3
if run_test "Data file in S3" "aws s3 ls s3://${AWS_S3_BUCKET}/input/online_retail.xlsx"; then
    echo "  S3 object found"
else
    echo -e "  ${YELLOW}Note: No data file uploaded yet. Run: bash aws/scripts/upload_data.sh${NC}"
fi

# Test 9: Check bronze layer data
echo ""
echo -e "${YELLOW}Testing: Bronze layer data count${NC}"
BRONZE_COUNT=$(PGPASSWORD=${AWS_RDS_PASSWORD} psql -h ${AWS_RDS_HOST} -p ${AWS_RDS_PORT} -U ${AWS_RDS_USER} -d ${AWS_RDS_DATABASE} -t -c "SELECT COUNT(*) FROM bronze.raw_transactions;" 2>/dev/null | xargs || echo "0")

if [ "$BRONZE_COUNT" -gt "0" ]; then
    echo -e "${GREEN}✓ PASSED (${BRONZE_COUNT} records)${NC}"
    TEST_RESULTS+=("✓ Bronze layer data count: ${BRONZE_COUNT}")
    ((TESTS_PASSED++))
else
    echo -e "${YELLOW}⚠ WARNING (0 records)${NC}"
    echo "  Run ingestion: python3 aws/scripts/ingest_from_s3_to_rds.py ..."
    TEST_RESULTS+=("⚠ Bronze layer data count: 0 (not yet ingested)")
fi

# Test 10: Check silver layer (if dbt has been run)
echo ""
echo -e "${YELLOW}Testing: Silver layer tables${NC}"
SILVER_TABLES=$(PGPASSWORD=${AWS_RDS_PASSWORD} psql -h ${AWS_RDS_HOST} -p ${AWS_RDS_PORT} -U ${AWS_RDS_USER} -d ${AWS_RDS_DATABASE} -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public_silver';" 2>/dev/null | xargs || echo "0")

if [ "$SILVER_TABLES" -gt "0" ]; then
    echo -e "${GREEN}✓ PASSED (${SILVER_TABLES} tables)${NC}"
    TEST_RESULTS+=("✓ Silver layer tables: ${SILVER_TABLES}")
    ((TESTS_PASSED++))
else
    echo -e "${YELLOW}⚠ WARNING (0 tables)${NC}"
    echo "  Run dbt: cd local && dbt run --profiles-dir ../aws/dbt_profile --target aws"
    TEST_RESULTS+=("⚠ Silver layer tables: 0 (dbt not yet run)")
fi

# Print summary
echo ""
echo -e "${GREEN}======================================"
echo "  Test Summary"
echo "======================================${NC}"
echo ""

for result in "${TEST_RESULTS[@]}"; do
    echo "  $result"
done

echo ""
echo "Results: ${TESTS_PASSED} passed, ${TESTS_FAILED} failed"
echo ""

if [ $TESTS_FAILED -eq 0 ] && [ "$BRONZE_COUNT" -gt "0" ] && [ "$SILVER_TABLES" -gt "0" ]; then
    echo -e "${GREEN}✓ All tests passed! Pipeline is fully operational.${NC}"
    exit 0
elif [ $TESTS_FAILED -eq 0 ]; then
    echo -e "${YELLOW}⚠ Infrastructure tests passed, but pipeline not fully executed yet.${NC}"
    echo ""
    echo "Complete the pipeline:"
    echo "1. Upload data: bash aws/scripts/upload_data.sh"
    echo "2. Ingest data: python3 aws/scripts/ingest_from_s3_to_rds.py ..."
    echo "3. Run dbt: cd local && dbt run --profiles-dir ../aws/dbt_profile --target aws"
    exit 0
else
    echo -e "${RED}✗ Some tests failed. Check the output above for details.${NC}"
    exit 1
fi
