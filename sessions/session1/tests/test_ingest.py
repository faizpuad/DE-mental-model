import pytest
import pandas as pd
import psycopg2
import os
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent / 'code'))

from ingest import DataIngestor


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
def sample_dataframe():
    data = {
        'InvoiceNo': ['536365', '536366', '536367', 'C536368', '536369'],
        'StockCode': ['85123A', '71053', '84406B', '85123A', '71053'],
        'Description': ['WHITE HANGING HEART T-LIGHT HOLDER', 'WHITE METAL LANTERN', None, 'WHITE HANGING HEART T-LIGHT HOLDER', 'WHITE METAL LANTERN'],
        'Quantity': [6, 6, 8, -6, 6],
        'InvoiceDate': pd.to_datetime(['2010-12-01 08:26:00', '2010-12-01 08:28:00', '2010-12-01 08:34:00', '2010-12-01 09:00:00', '2010-12-01 09:15:00']),
        'UnitPrice': [3.39, 7.65, 5.85, 3.39, 7.65],
        'CustomerID': [17850.0, 17850.0, 17850.0, 17850.0, 17850.0],
        'Country': ['United Kingdom', 'United Kingdom', 'United Kingdom', 'United Kingdom', 'United Kingdom']
    }
    return pd.DataFrame(data)


@pytest.fixture
def data_ingestor():
    ingestor = DataIngestor()
    ingestor.connect()
    yield ingestor
    ingestor.disconnect()


class TestDataIngestor:
    def test_connect(self, data_ingestor):
        assert data_ingestor.conn is not None
        assert data_ingestor.conn.closed == 0

    def test_create_bronze_schema(self, data_ingestor, db_connection):
        cursor = db_connection.cursor()
        cursor.execute("SELECT schema_name FROM information_schema.schemata WHERE schema_name = 'bronze';")
        result = cursor.fetchone()
        cursor.close()
        assert result is not None

    def test_raw_transactions_table_exists(self, data_ingestor, db_connection):
        cursor = db_connection.cursor()
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'bronze' 
                AND table_name = 'raw_transactions'
            );
        """)
        result = cursor.fetchone()[0]
        cursor.close()
        assert result is True

    def test_raw_transactions_columns(self, data_ingestor, db_connection):
        cursor = db_connection.cursor()
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_schema = 'bronze' AND table_name = 'raw_transactions'
            ORDER BY ordinal_position;
        """)
        columns = [row[0] for row in cursor.fetchall()]
        cursor.close()
        expected_columns = [
            'id', 'invoiceno', 'stockcode', 'description', 'quantity',
            'invoicedate', 'unitprice', 'customerid', 'country', 'ingested_at', 'source_file'
        ]
        assert columns == expected_columns

    def test_clean_data_removes_nulls(self, data_ingestor, sample_dataframe):
        df_cleaned = data_ingestor.clean_data(sample_dataframe)
        assert df_cleaned['description'].isna().sum() == 0

    def test_clean_data_preserves_valid_records(self, data_ingestor, sample_dataframe):
        df_cleaned = data_ingestor.clean_data(sample_dataframe)
        assert len(df_cleaned) > 0

    def test_clean_data_convert_dates(self, data_ingestor, sample_dataframe):
        df_cleaned = data_ingestor.clean_data(sample_dataframe)
        assert pd.api.types.is_datetime64_any_dtype(df_cleaned['invoicedate'])

    def test_raw_transactions_has_data(self, data_ingestor, db_connection):
        cursor = db_connection.cursor()
        cursor.execute("SELECT COUNT(*) FROM bronze.raw_transactions;")
        count = cursor.fetchone()[0]
        cursor.close()
        assert count > 0

    def test_invoiceno_not_null(self, data_ingestor, db_connection):
        cursor = db_connection.cursor()
        cursor.execute("SELECT COUNT(*) FROM bronze.raw_transactions WHERE invoiceno IS NULL;")
        null_count = cursor.fetchone()[0]
        cursor.close()
        assert null_count == 0

    def test_stockcode_not_null(self, data_ingestor, db_connection):
        cursor = db_connection.cursor()
        cursor.execute("SELECT COUNT(*) FROM bronze.raw_transactions WHERE stockcode IS NULL;")
        null_count = cursor.fetchone()[0]
        cursor.close()
        assert null_count == 0

    def test_invoicedate_not_null(self, data_ingestor, db_connection):
        cursor = db_connection.cursor()
        cursor.execute("SELECT COUNT(*) FROM bronze.raw_transactions WHERE invoicedate IS NULL;")
        null_count = cursor.fetchone()[0]
        cursor.close()
        assert null_count == 0

    def test_unitprice_valid_range(self, data_ingestor, db_connection):
        cursor = db_connection.cursor()
        cursor.execute("SELECT COUNT(*) FROM bronze.raw_transactions WHERE unitprice < 0 OR unitprice > 10000;")
        invalid_count = cursor.fetchone()[0]
        cursor.close()
        assert invalid_count == 0

    def test_unique_invoices_exist(self, data_ingestor, db_connection):
        cursor = db_connection.cursor()
        cursor.execute("SELECT COUNT(DISTINCT invoiceno) FROM bronze.raw_transactions;")
        unique_invoices = cursor.fetchone()[0]
        cursor.close()
        assert unique_invoices > 0

    def test_unique_products_exist(self, data_ingestor, db_connection):
        cursor = db_connection.cursor()
        cursor.execute("SELECT COUNT(DISTINCT stockcode) FROM bronze.raw_transactions;")
        unique_products = cursor.fetchone()[0]
        cursor.close()
        assert unique_products > 0

    def test_unique_countries_exist(self, data_ingestor, db_connection):
        cursor = db_connection.cursor()
        cursor.execute("SELECT COUNT(DISTINCT country) FROM bronze.raw_transactions;")
        unique_countries = cursor.fetchone()[0]
        cursor.close()
        assert unique_countries > 0

    def test_index_on_invoiceno(self, data_ingestor, db_connection):
        cursor = db_connection.cursor()
        cursor.execute("""
            SELECT indexname 
            FROM pg_indexes 
            WHERE schemaname = 'bronze' AND tablename = 'raw_transactions' AND indexname = 'idx_raw_transactions_invoiceno';
        """)
        result = cursor.fetchone()
        cursor.close()
        assert result is not None

    def test_index_on_stockcode(self, data_ingestor, db_connection):
        cursor = db_connection.cursor()
        cursor.execute("""
            SELECT indexname 
            FROM pg_indexes 
            WHERE schemaname = 'bronze' AND tablename = 'raw_transactions' AND indexname = 'idx_raw_transactions_stockcode';
        """)
        result = cursor.fetchone()
        cursor.close()
        assert result is not None

    def test_index_on_customerid(self, data_ingestor, db_connection):
        cursor = db_connection.cursor()
        cursor.execute("""
            SELECT indexname 
            FROM pg_indexes 
            WHERE schemaname = 'bronze' AND tablename = 'raw_transactions' AND indexname = 'idx_raw_transactions_customerid';
        """)
        result = cursor.fetchone()
        cursor.close()
        assert result is not None

    def test_index_on_invoicedate(self, data_ingestor, db_connection):
        cursor = db_connection.cursor()
        cursor.execute("""
            SELECT indexname 
            FROM pg_indexes 
            WHERE schemaname = 'bronze' AND tablename = 'raw_transactions' AND indexname = 'idx_raw_transactions_invoicedate';
        """)
        result = cursor.fetchone()
        cursor.close()
        assert result is not None

    def test_date_range_exists(self, data_ingestor, db_connection):
        cursor = db_connection.cursor()
        cursor.execute("SELECT MIN(invoicedate), MAX(invoicedate) FROM bronze.raw_transactions;")
        min_date, max_date = cursor.fetchone()
        cursor.close()
        assert min_date is not None
        assert max_date is not None
        assert min_date <= max_date

    def test_sample_query_performance(self, data_ingestor, db_connection):
        cursor = db_connection.cursor()
        cursor.execute("""
            SELECT 
                COUNT(*) as total_records,
                COUNT(DISTINCT invoiceno) as unique_invoices,
                SUM(quantity * unitprice) as total_revenue
            FROM bronze.raw_transactions;
        """)
        result = cursor.fetchone()
        cursor.close()
        total_records, unique_invoices, total_revenue = result
        assert total_records > 0
        assert unique_invoices > 0
        assert total_revenue is not None


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--cov=../code', '--cov-report=html'])
