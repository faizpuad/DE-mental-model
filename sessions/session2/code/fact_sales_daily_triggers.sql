-- Create function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_fact_sales_daily_updated_at
    BEFORE UPDATE ON silver.fact_sales_daily
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();