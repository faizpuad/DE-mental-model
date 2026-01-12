-- Raw Transactions Table
-- Purpose: Store raw transaction data as-is from source system
-- This is the Bronze layer in medallion architecture

CREATE SCHEMA IF NOT EXISTS bronze;

DROP TABLE IF EXISTS bronze.raw_transactions;

CREATE TABLE bronze.raw_transactions (
    id SERIAL PRIMARY KEY,
    invoiceno VARCHAR(10) NOT NULL,
    stockcode VARCHAR(20) NOT NULL,
    description VARCHAR(255),
    quantity INTEGER,
    invoicedate TIMESTAMP NOT NULL,
    unitprice DECIMAL(10,2),
    customerid VARCHAR(10),
    country VARCHAR(100),
    ingested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    source_file VARCHAR(255)
);

-- Indexes for common query patterns
CREATE INDEX idx_raw_transactions_invoiceno ON bronze.raw_transactions(invoiceno);
CREATE INDEX idx_raw_transactions_stockcode ON bronze.raw_transactions(stockcode);
CREATE INDEX idx_raw_transactions_customerid ON bronze.raw_transactions(customerid);
CREATE INDEX idx_raw_transactions_invoicedate ON bronze.raw_transactions(invoicedate);
CREATE INDEX idx_raw_transactions_country ON bronze.raw_transactions(country);

-- Comment for documentation
COMMENT ON TABLE bronze.raw_transactions IS 'Raw transaction data loaded from source system';
COMMENT ON COLUMN bronze.raw_transactions.invoiceno IS 'Invoice number. Starts with ''c'' for cancellations';
COMMENT ON COLUMN bronze.raw_transactions.stockcode IS 'Product code (5-digit)';
COMMENT ON COLUMN bronze.raw_transactions.quantity IS 'Quantity per transaction (can be negative for cancellations)';
COMMENT ON COLUMN bronze.raw_transactions.unitprice IS 'Unit price in sterling';
COMMENT ON COLUMN bronze.raw_transactions.customerid IS 'Customer ID (5-digit)';
COMMENT ON COLUMN bronze.raw_transactions.ingested_at IS 'Timestamp when record was loaded';
