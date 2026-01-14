import pytest
import psycopg2
import os
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent / 'code'))

from transform import DataTransformer


@pytest.fixture
def db_config():
    return {
        'host': os.getenv('DB_HOST', 'localhost'),
        'port': os.getenv('DB_PORT', '5432'),
        'database': os.getenv('DB_NAME', 'retail_db'),
        'user': os.getenv('DB_USER', 'postgres'),
        'password': os.getenv('DB_PASSWORD', 'postgres')
    }


@pytest.fixture
def db_connection(db_config):
    conn = psycopg2.connect(**db_config)
    yield conn
    conn.close()


@pytest.fixture
def data_transformer():
    transformer = DataTransformer()
    transformer.connect()
    yield transformer
    transformer.disconnect()


class TestDataTransformer:
    def test_connect(self, data_transformer):
        assert data_transformer.conn is not None
        assert data_transformer.conn.closed == 0

    def test_create_silver_schema(self, data_transformer):
        data_transformer.create_silver_schema()
        cursor = data_transformer.conn.cursor()
        cursor.execute("SELECT schema_name FROM information_schema.schemata WHERE schema_name = 'silver';")
        result = cursor.fetchone()
        cursor.close()
        assert result is not None

    def test_dim_date_table_exists(self, data_transformer, db_connection):
        cursor = db_connection.cursor()
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'silver' 
                AND table_name = 'dim_date'
            );
        """)
        result = cursor.fetchone()[0]
        cursor.close()
        assert result is True

    def test_dim_product_table_exists(self, data_transformer, db_connection):
        cursor = db_connection.cursor()
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'silver' 
                AND table_name = 'dim_product'
            );
        """)
        result = cursor.fetchone()[0]
        cursor.close()
        assert result is True

    def test_fact_sales_daily_table_exists(self, data_transformer, db_connection):
        cursor = db_connection.cursor()
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'silver' 
                AND table_name = 'fact_sales_daily'
            );
        """)
        result = cursor.fetchone()[0]
        cursor.close()
        assert result is True

    def test_dim_date_has_data(self, data_transformer, db_connection):
        cursor = db_connection.cursor()
        cursor.execute("SELECT COUNT(*) FROM silver.dim_date;")
        count = cursor.fetchone()[0]
        cursor.close()
        assert count > 0

    def test_dim_product_has_data(self, data_transformer, db_connection):
        cursor = db_connection.cursor()
        cursor.execute("SELECT COUNT(*) FROM silver.dim_product;")
        count = cursor.fetchone()[0]
        cursor.close()
        assert count > 0

    def test_fact_sales_daily_has_data(self, data_transformer, db_connection):
        cursor = db_connection.cursor()
        cursor.execute("SELECT COUNT(*) FROM silver.fact_sales_daily;")
        count = cursor.fetchone()[0]
        cursor.close()
        assert count > 0

    def test_fact_sales_daily_metrics_positive(self, data_transformer, db_connection):
        cursor = db_connection.cursor()
        cursor.execute("""
            SELECT COUNT(*) 
            FROM silver.fact_sales_daily 
            WHERE total_transactions < 0 OR total_quantity < 0 OR total_revenue < 0;
        """)
        count = cursor.fetchone()[0]
        cursor.close()
        assert count == 0

    def test_fact_sales_daily_foreign_keys(self, data_transformer, db_connection):
        cursor = db_connection.cursor()
        cursor.execute("""
            SELECT COUNT(*)
            FROM silver.fact_sales_daily fsd
            LEFT JOIN silver.dim_date dd ON fsd.date_id = dd.date_id
            WHERE dd.date_id IS NULL;
        """)
        orphan_date_count = cursor.fetchone()[0]
        
        cursor.execute("""
            SELECT COUNT(*)
            FROM silver.fact_sales_daily fsd
            LEFT JOIN silver.dim_product dp ON fsd.product_id = dp.product_id
            WHERE dp.product_id IS NULL;
        """)
        orphan_product_count = cursor.fetchone()[0]
        cursor.close()
        assert orphan_date_count == 0
        assert orphan_product_count == 0

    def test_dim_date_columns(self, data_transformer, db_connection):
        cursor = db_connection.cursor()
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_schema = 'silver' AND table_name = 'dim_date'
            ORDER BY ordinal_position;
        """)
        columns = [row[0] for row in cursor.fetchall()]
        cursor.close()
        expected_columns = [
            'date_id', 'date', 'day', 'day_name', 'day_of_week',
            'month', 'month_name', 'quarter', 'year', 'is_weekend',
            'is_holiday', 'created_at'
        ]
        assert columns == expected_columns

    def test_dim_product_columns(self, data_transformer, db_connection):
        cursor = db_connection.cursor()
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_schema = 'silver' AND table_name = 'dim_product'
            ORDER BY ordinal_position;
        """)
        columns = [row[0] for row in cursor.fetchall()]
        cursor.close()
        expected_columns = [
            'product_id', 'stock_code', 'description', 'category', 'created_at', 'updated_at'
        ]
        assert columns == expected_columns

    def test_fact_sales_daily_columns(self, data_transformer, db_connection):
        cursor = db_connection.cursor()
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_schema = 'silver' AND table_name = 'fact_sales_daily'
            ORDER BY ordinal_position;
        """)
        columns = [row[0] for row in cursor.fetchall()]
        cursor.close()
        expected_columns = [
            'id', 'date_id', 'product_id', 'country', 'total_transactions',
            'total_quantity', 'total_revenue', 'avg_unit_price', 'created_at', 'updated_at'
        ]
        assert columns == expected_columns

    def test_fact_sales_daily_indexes_exist(self, data_transformer, db_connection):
        cursor = db_connection.cursor()
        cursor.execute("""
            SELECT indexname 
            FROM pg_indexes 
            WHERE schemaname = 'silver' AND tablename = 'fact_sales_daily';
        """)
        indexes = [row[0] for row in cursor.fetchall()]
        cursor.close()
        expected_indexes = [
            'fact_sales_daily_pkey',
            'idx_fact_sales_daily_date_id',
            'idx_fact_sales_daily_product_id',
            'idx_fact_sales_daily_country',
            'idx_fact_sales_daily_date_country',
            'idx_fact_sales_daily_revenue'
        ]
        for expected_index in expected_indexes:
            assert expected_index in indexes

    def test_total_revenue_aggregation(self, data_transformer, db_connection):
        cursor = db_connection.cursor()
        cursor.execute("""
            SELECT SUM(total_revenue) FROM silver.fact_sales_daily;
        """)
        silver_revenue = cursor.fetchone()[0]
        
        cursor.execute("""
            SELECT SUM(quantity * unitprice) FROM bronze.raw_transactions 
            WHERE quantity > 0 AND unitprice >= 0;
        """)
        bronze_revenue = cursor.fetchone()[0]
        cursor.close()
        assert round(silver_revenue, 2) == round(bronze_revenue, 2)

    def test_total_quantity_aggregation(self, data_transformer, db_connection):
        cursor = db_connection.cursor()
        cursor.execute("""
            SELECT SUM(total_quantity) FROM silver.fact_sales_daily;
        """)
        silver_quantity = cursor.fetchone()[0]
        
        cursor.execute("""
            SELECT SUM(quantity) FROM bronze.raw_transactions 
            WHERE quantity > 0;
        """)
        bronze_quantity = cursor.fetchone()[0]
        cursor.close()
        assert silver_quantity == bronze_quantity

    def test_dim_date_unique_constraint(self, data_transformer, db_connection):
        cursor = db_connection.cursor()
        cursor.execute("""
            SELECT COUNT(*) FROM silver.dim_date 
            GROUP BY date 
            HAVING COUNT(*) > 1;
        """)
        duplicate_count = cursor.fetchone()[0]
        cursor.close()
        assert duplicate_count is None

    def test_dim_product_unique_constraint(self, data_transformer, db_connection):
        cursor = db_connection.cursor()
        cursor.execute("""
            SELECT COUNT(*) FROM silver.dim_product 
            GROUP BY stock_code 
            HAVING COUNT(*) > 1;
        """)
        duplicate_count = cursor.fetchone()[0]
        cursor.close()
        assert duplicate_count is None

    def test_fact_sales_daily_unique_constraint(self, data_transformer, db_connection):
        cursor = db_connection.cursor()
        cursor.execute("""
            SELECT COUNT(*) FROM silver.fact_sales_daily 
            GROUP BY date_id, product_id, country 
            HAVING COUNT(*) > 1;
        """)
        duplicate_count = cursor.fetchone()[0]
        cursor.close()
        assert duplicate_count is None


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--cov=../code', '--cov-report=html'])
