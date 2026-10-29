DROP TABLE IF EXISTS coolwalk.segments;
CREATE TABLE coolwalk.segments
WITH (table_type = 'ICEBERG', location = 's3://${BUCKET}/iceberg/segments/', is_external = false, format = 'PARQUET')
AS SELECT * FROM coolwalk.segments_raw;
