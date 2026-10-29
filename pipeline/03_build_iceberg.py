"""Step 3. Put the scored street segments into an Apache Iceberg table on S3 using Amazon Athena.

  work/segments.parquet -> s3://BUCKET/staging/segments/ -> coolwalk.segments (Iceberg)

Needs: COOLWALK_BUCKET set, AWS credentials with S3 + Athena + Glue access.
"""
import sys
import time
from pathlib import Path

import boto3

import config

SQL = Path(__file__).parent / "sql"
athena = boto3.client("athena", region_name=config.REGION)
s3 = boto3.client("s3", region_name=config.REGION)


def run(sql, database=None):
    """Run one Athena statement and wait for it. Returns the query execution id."""
    args = {"QueryString": sql, "WorkGroup": "primary",
            "ResultConfiguration": {"OutputLocation": f"s3://{config.BUCKET}/athena-results/"}}
    if database:
        args["QueryExecutionContext"] = {"Database": database}
    qid = athena.start_query_execution(**args)["QueryExecutionId"]
    while True:
        st = athena.get_query_execution(QueryExecutionId=qid)["QueryExecution"]["Status"]
        if st["State"] in ("SUCCEEDED", "FAILED", "CANCELLED"):
            break
        time.sleep(1.0)
    if st["State"] != "SUCCEEDED":
        raise RuntimeError(f"Athena {st['State']}: {st.get('StateChangeReason', '')}\n{sql[:300]}")
    return qid


def rows(qid):
    """Return result rows as a list of dicts (strings)."""
    out, header = [], None
    for page in athena.get_paginator("get_query_results").paginate(QueryExecutionId=qid):
        for r in page["ResultSet"]["Rows"]:
            vals = [c.get("VarCharValue") for c in r["Data"]]
            if header is None:
                header = vals
            else:
                out.append(dict(zip(header, vals)))
    return out


def clear_prefix(prefix):
    """Iceberg CTAS needs an empty target location, so wipe it before re-running."""
    for page in s3.get_paginator("list_objects_v2").paginate(Bucket=config.BUCKET, Prefix=prefix):
        keys = [{"Key": o["Key"]} for o in page.get("Contents", [])]
        if keys:
            s3.delete_objects(Bucket=config.BUCKET, Delete={"Objects": keys})


def statements(name):
    text = (SQL / name).read_text().replace("${BUCKET}", config.BUCKET)
    return [s.strip() for s in text.split(";") if s.strip()]


def main():
    if not config.BUCKET:
        sys.exit("Set COOLWALK_BUCKET to the data bucket name (stack output DataBucket).")
    parquet = config.WORK / "segments.parquet"
    if not parquet.exists():
        sys.exit("Run pipeline/02_score_segments.py first.")

    print("Uploading segments.parquet ...")
    clear_prefix("staging/segments/")
    s3.upload_file(str(parquet), config.BUCKET, "staging/segments/segments.parquet")

    for f in ("01_database.sql", "02_staging_table.sql"):
        for s in statements(f):
            print("Athena:", s.splitlines()[0])
            run(s)
    clear_prefix("iceberg/segments/")
    for s in statements("03_iceberg_table.sql"):
        print("Athena:", s.splitlines()[0])
        run(s, config.DB)

    n = rows(run("SELECT count(*) AS n FROM coolwalk.segments", config.DB))[0]["n"]
    print(f"Iceberg table coolwalk.segments is ready with {int(n):,} street segments.")


if __name__ == "__main__":
    main()
