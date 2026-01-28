#!/usr/bin/env python3
"""
Validation Script
Runs custom SQL checks on silver layer
Complements dbt tests
"""

import argparse
import sys
import logging

import psycopg2

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('validate')


class DataValidator:
    """Custom validation checks"""

    def __init__(self, db_host, db_port, db_name, db_user, db_password):
        self.db_host = db_host
        self.db_port = db_port
        self.db_name = db_name
        self.db_user = db_user
        self.db_password = db_password
        self.conn = None

    def connect(self):
        """Connect to PostgreSQL"""
        self.conn = psycopg2.connect(
            host=self.db_host,
            port=self.db_port,
            database=self.db_name,
            user=self.db_user,
            password=self.db_password,
            connect_timeout=10,
        )
        logger.info("Connected to database for validation")

    def disconnect(self):
        """Disconnect from PostgreSQL"""
        if self.conn:
            self.conn.close()

    def run_check(self, check_name, query, expected_condition):
        """Run a validation check"""
        cursor = self.conn.cursor()
        try:
            cursor.execute(query)
            result = cursor.fetchone()[0]

            passed = expected_condition(result)
            status = "✓" if passed else "✗"

            logger.info(f"{status} {check_name}: {result}")
            return passed, result

        finally:
            cursor.close()

    def validate(self):
        """Run all validation checks"""
        checks_passed = 0
        checks_total = 0

        try:
            self.connect()

            # Check 1: Bronze layer has data
            checks_total += 1
            passed, count = self.run_check(
                "Bronze layer record count",
                "SELECT COUNT(*) FROM bronze.raw_transactions;",
                lambda x: x > 0
            )
            if passed:
                checks_passed += 1

            # Check 2: dim_date has data
            checks_total += 1
            passed, count = self.run_check(
                "dim_date record count",
                "SELECT COUNT(*) FROM public_silver.dim_date;",
                lambda x: x > 0
            )
            if passed:
                checks_passed += 1

            # Check 3: dim_product has data
            checks_total += 1
            passed, count = self.run_check(
                "dim_product record count",
                "SELECT COUNT(*) FROM public_silver.dim_product;",
                lambda x: x > 0
            )
            if passed:
                checks_passed += 1

            # Check 4: fact_sales_daily has data
            checks_total += 1
            passed, count = self.run_check(
                "fact_sales_daily record count",
                "SELECT COUNT(*) FROM public_silver.fact_sales_daily;",
                lambda x: x > 0
            )
            if passed:
                checks_passed += 1

            # Check 5: Total revenue is positive
            checks_total += 1
            passed, revenue = self.run_check(
                "Total revenue (should be positive)",
                "SELECT SUM(total_revenue)::NUMERIC(15,2) FROM public_silver.fact_sales_daily;",
                lambda x: x and x > 0
            )
            if passed:
                checks_passed += 1

            # Check 6: No null revenues in fact table
            checks_total += 1
            passed, null_count = self.run_check(
                "Null revenue count (should be 0)",
                "SELECT COUNT(*) FROM public_silver.fact_sales_daily WHERE total_revenue IS NULL;",
                lambda x: x == 0
            )
            if passed:
                checks_passed += 1

            # Summary
            logger.info(f"=" * 50)
            logger.info(f"Validation Summary: {checks_passed}/{checks_total} checks passed")
            logger.info(f"=" * 50)

            if checks_passed == checks_total:
                logger.info("✓ All validation checks passed!")
                return 0
            else:
                logger.warning(f"✗ {checks_total - checks_passed} checks failed")
                return 1

        finally:
            self.disconnect()


def main():
    parser = argparse.ArgumentParser(description='Validate silver layer data')
    parser.add_argument('--db-host', required=True, help='Database host')
    parser.add_argument('--db-port', default='5432', help='Database port')
    parser.add_argument('--db-name', required=True, help='Database name')
    parser.add_argument('--db-user', required=True, help='Database user')
    parser.add_argument('--db-password', required=True, help='Database password')

    args = parser.parse_args()

    try:
        validator = DataValidator(
            db_host=args.db_host,
            db_port=args.db_port,
            db_name=args.db_name,
            db_user=args.db_user,
            db_password=args.db_password,
        )

        exit_code = validator.validate()
        sys.exit(exit_code)

    except Exception as e:
        logger.error(f"Validation failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    main()
