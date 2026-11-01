"""Deploy the frontend directory to AWS Amplify Hosting via manual zip deployment."""
import io
import os
import sys
import time
import urllib.request
import zipfile
import boto3

REGION = os.getenv("AMPLIFY_REGION", "us-east-2").strip()
BRANCH = os.getenv("AMPLIFY_BRANCH", "main").strip()
FRONTEND_DIR = os.path.join(os.path.dirname(__file__), "..", "frontend")


def get_app_id(amp):
    app_id = os.getenv("AMPLIFY_APP_ID")
    if app_id:
        return app_id
    print("AMPLIFY_APP_ID is not set; checking for existing app or creating a new Amplify app...")
    apps = amp.list_apps().get("apps", [])
    matches = [a for a in apps if a.get("name") == "coolwalk"]
    if matches:
        app_id = matches[0]["appId"]
        print(f"Found existing Amplify app 'coolwalk' with ID: {app_id}")
    else:
        created = amp.create_app(name="coolwalk", platform="WEB")
        app_id = created["app"]["appId"]
        print(f"Created new Amplify app 'coolwalk' with ID: {app_id}")

    try:
        amp.get_branch(appId=app_id, branchName=BRANCH)
    except Exception:
        print(f"Creating branch '{BRANCH}' on app {app_id}...")
        amp.create_branch(appId=app_id, branchName=BRANCH)

    print(f"AMPLIFY_APP_ID={app_id}")
    return app_id


def main():
    print(f"Packaging {FRONTEND_DIR}...")
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        for root, _, files in os.walk(FRONTEND_DIR):
            for f in files:
                path = os.path.join(root, f)
                arcname = os.path.relpath(path, FRONTEND_DIR)
                z.write(path, arcname)
    zip_bytes = buf.getvalue()
    print(f"Created zip ({len(zip_bytes):,} bytes).")

    amp = boto3.client("amplify", region_name=REGION)
    app_id = get_app_id(amp)

    print(f"Creating deployment on Amplify App {app_id} ({BRANCH})...")
    dep = amp.create_deployment(appId=app_id, branchName=BRANCH)
    job_id = dep["jobId"]
    upload_url = dep["zipUploadUrl"]

    print("Uploading zip archive...")
    req = urllib.request.Request(upload_url, data=zip_bytes, method="PUT")
    req.add_header("Content-Type", "application/zip")
    with urllib.request.urlopen(req) as resp:
        if resp.status not in (200, 204):
            sys.exit(f"Upload failed: {resp.status}")

    print(f"Starting deployment job {job_id}...")
    amp.start_deployment(appId=app_id, branchName=BRANCH, jobId=job_id)

    print("Waiting for deployment to succeed...")
    for _ in range(30):
        time.sleep(3)
        job = amp.get_job(appId=app_id, branchName=BRANCH, jobId=job_id)
        status = job["job"]["summary"]["status"]
        print(f"Job {job_id} status: {status}")
        if status == "SUCCEED":
            url = f"https://{BRANCH}.{app_id}.amplifyapp.com"
            print(f"\nSuccessfully deployed to Amplify: {url}")
            return
        if status in ("FAILED", "CANCELLED"):
            sys.exit(f"Deployment {status}")
    sys.exit("Deployment timed out.")


if __name__ == "__main__":
    main()
