DROP TABLE IF EXISTS coolwalk.segments_raw;
CREATE EXTERNAL TABLE coolwalk.segments_raw (
  edge_id bigint, u bigint, v bigint, length_m double,
  mid_lon double, mid_lat double, lst_c double, ndvi double,
  heat_index double, highway string, name string
)
STORED AS PARQUET
LOCATION 's3://${BUCKET}/staging/segments/';
