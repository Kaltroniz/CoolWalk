"""Upload places.parquet and create the Iceberg table coolwalk.places in Amazon Athena."""
import sys
import time
from pathlib import Path
import boto3

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / "pipeline"))
import config
import importlib

ath = importlib.import_module("03_build_iceberg")


def main():
    bucket = config.BUCKET
    if not bucket:
        sys.exit("Error: config.BUCKET is not set.")
    parquet = config.WORK / "places.parquet"
    if not parquet.exists():
        sys.exit("work/places.parquet does not exist.")

    print(f"Uploading places.parquet to s3://{bucket}/staging/places/...")
    ath.clear_prefix("staging/places/")
    ath.s3.upload_file(str(parquet), bucket, "staging/places/places.parquet")

    # Staging table
    sql_staging = f"""
    CREATE EXTERNAL TABLE IF NOT EXISTS coolwalk.places_staging (
      place_id BIGINT,
      kind STRING,
      name STRING,
      lon DOUBLE,
      lat DOUBLE,
      lst_c DOUBLE,
      ndvi DOUBLE,
      heat_index DOUBLE
    )
    STORED AS PARQUET
    LOCATION 's3://{bucket}/staging/places/'
    """
    print("Athena: Creating staging table coolwalk.places_staging...")
    ath.run(sql_staging.strip(), config.DB)

    # Iceberg table
    print("Athena: Creating Iceberg table coolwalk.places...")
    ath.clear_prefix("iceberg/places/")
    ath.run("DROP TABLE IF EXISTS coolwalk.places", config.DB)
    sql_iceberg = f"""
    CREATE TABLE coolwalk.places
    WITH (
      table_type = 'ICEBERG',
      format = 'PARQUET',
      is_external = false,
      location = 's3://{bucket}/iceberg/places/'
    ) AS
    SELECT * FROM coolwalk.places_staging
    """
    ath.run(sql_iceberg.strip(), config.DB)

    n = ath.rows(ath.run("SELECT count(*) AS n FROM coolwalk.places", config.DB))[0]["n"]
    print(f"Iceberg table coolwalk.places is ready with {int(n):,} places!")


if __name__ == "__main__":
    main()
