"""Package the backend for AgentCore Runtime and upload it to S3.

Run after changing anything under backend/ (including backend/data/jobs.json), then paste
the printed command into the workshop Code Editor terminal to redeploy the runtime.
The bucket name is remembered in .local/agentcore-bundle-bucket (created on first run;
sandbox accounts may require the workshop- prefix). Never packages .env or .local.
"""
import argparse
import io
import os
import secrets
import tarfile
from pathlib import Path

import boto3
from botocore.exceptions import ClientError
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
BUCKET_FILE = ROOT / ".local" / "agentcore-bundle-bucket"
KEY = "careerbuddy-agentcore.tgz"


def build_bundle():
    buffer = io.BytesIO()
    with tarfile.open(fileobj=buffer, mode="w:gz") as tar:
        tar.add(ROOT / "backend", arcname="backend", filter=lambda t: None if "__pycache__" in t.name else t)
        for name in ("main.py", "patch_cdk.py", "deploy.sh"):
            tar.add(ROOT / "deployment" / "agentcore" / name, arcname=name)
    return buffer.getvalue()


def main():
    load_dotenv(ROOT / ".env")
    parser = argparse.ArgumentParser()
    parser.add_argument("--bucket", default=BUCKET_FILE.read_text().strip() if BUCKET_FILE.exists() else None)
    parser.add_argument("--region", default=os.getenv("AWS_DEFAULT_REGION") or os.getenv("AWS_REGION") or "us-east-1")
    args = parser.parse_args()
    s3 = boto3.client("s3", region_name=args.region)
    bucket = args.bucket or f"workshop-careerbuddy-{secrets.token_hex(4)}"
    try:
        s3.head_bucket(Bucket=bucket)
    except ClientError:
        s3.create_bucket(Bucket=bucket)
        print(f"Created bucket {bucket}")
    BUCKET_FILE.parent.mkdir(exist_ok=True)
    BUCKET_FILE.write_text(bucket + "\n")
    data = build_bundle()
    s3.put_object(Bucket=bucket, Key=KEY, Body=data)
    print(f"Uploaded {len(data) // 1024} KB to s3://{bucket}/{KEY}\n")
    print("Now run this in the workshop Code Editor terminal:\n")
    print(f"mkdir -p /workshop/careerbuddy-bundle && cd /workshop/careerbuddy-bundle && "
          f"aws s3 cp s3://{bucket}/{KEY} . && tar xzf {KEY} && bash deploy.sh")


if __name__ == "__main__":
    main()
