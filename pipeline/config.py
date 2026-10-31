"""Shared settings. Change BBOX and DATE_RANGE to reuse CoolWalk for another city."""
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WORK = ROOT / "work"
FRONT_DATA = ROOT / "frontend" / "data"
WORK.mkdir(exist_ok=True)
FRONT_DATA.mkdir(parents=True, exist_ok=True)

REGION = os.getenv("AWS_REGION", "us-east-1")
BUCKET = os.getenv("COOLWALK_BUCKET", "")          # data bucket from the CloudFormation stack
if not BUCKET:
    try:
        import boto3
        cf = boto3.client("cloudformation", region_name=REGION)
        st = cf.describe_stacks(StackName="coolwalk")["Stacks"][0]
        for o in st.get("Outputs", []):
            if o.get("OutputKey") == "DataBucket":
                BUCKET = o["OutputValue"]
                break
    except Exception:
        pass
DB = "coolwalk"

# west, south, east, north (central Delhi: Old Delhi to Lodhi Garden)
BBOX = (77.19, 28.585, 77.26, 28.668)
DATE_RANGE = os.getenv("COOLWALK_DATES", "2026-04-15/2026-06-20")   # pre-monsoon, hottest and clearest
LANDSAT_MAX_CLOUD = 15
S2_MAX_CLOUD = 20

STEP_M = 15                 # sample spacing along each street segment
W_LST, W_VEG = 0.6, 0.4     # heat index = W_LST * surface temperature + W_VEG * lack of vegetation
HOT_T = 0.66                # keep in sync with backend/router/app.py
