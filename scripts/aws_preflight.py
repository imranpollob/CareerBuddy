"""Read-only AWS checks plus one tiny, explicitly permitted inference call.

Never prints identity ARNs, account IDs, tokens, or credential values.
"""
import argparse
import json
import os
from pathlib import Path
from datetime import datetime, timezone
import subprocess
import sys

import boto3
from botocore.config import Config
from botocore.exceptions import BotoCoreError, ClientError
from dotenv import load_dotenv


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default=".local/aws-preflight.json")
    args = parser.parse_args()
    load_dotenv(override=False)
    os.environ.setdefault("AWS_EC2_METADATA_DISABLED", "true")
    session = boto3.Session()
    region = session.region_name or os.getenv("AWS_REGION")
    report = {"checked_at": datetime.now(timezone.utc).isoformat(), "region": region,
              "identity": "not_checked", "models": [], "inference": "not_run", "model_id": None}
    config = Config(connect_timeout=8, read_timeout=40, retries={"max_attempts": 0})
    try:
        # Exercise the installed CLI as well as the SDK; discard identity output.
        cli = Path(sys.executable).parent / "aws"
        result = subprocess.run([str(cli), "sts", "get-caller-identity"], capture_output=True, timeout=25)
        report["cli_identity"] = "verified" if result.returncode == 0 else "failed"
        session.client("sts", region_name=region or "us-east-1", config=config).get_caller_identity()
        report["identity"] = "verified"
        if not region:
            report["error"] = "No region configured; set AWS_DEFAULT_REGION or AWS_REGION"
        else:
            control = session.client("bedrock", region_name=region, config=config)
            try:
                models = control.list_foundation_models(byProvider="Amazon")["modelSummaries"]
                report["models"] = [{"id": m["modelId"], "status": m.get("modelLifecycle", {}).get("status"),
                                     "streaming": m.get("responseStreamingSupported", False)} for m in models
                                    if "nova" in m["modelId"] and "TEXT" in m.get("outputModalities", [])]
            except ClientError as exc:
                report["catalog_error"] = exc.response["Error"]["Code"]
            runtime = session.client("bedrock-runtime", region_name=region, config=config)
            requested = os.getenv("SKILLPILOT_MODEL_ID")
            candidates = list(dict.fromkeys(filter(None, [requested, "amazon.nova-lite-v1:0", "us.amazon.nova-lite-v1:0",
                                                         "amazon.nova-micro-v1:0", "us.amazon.nova-micro-v1:0"])))
            report["attempts"] = []
            for model_id in candidates:
                try:
                    response = runtime.converse(modelId=model_id, messages=[{"role": "user", "content": [
                        {"text": "Reply with exactly: SkillPilot ready"}]}],
                        inferenceConfig={"maxTokens": 20, "temperature": 0})
                    text = " ".join(b.get("text", "") for b in response["output"]["message"]["content"])
                    report.update(model_id=model_id, inference="passed" if "SkillPilot" in text else "unexpected_response",
                                  usage=response.get("usage", {}))
                    break
                except ClientError as exc:
                    report["attempts"].append({"model_id": model_id, "error": exc.response["Error"]["Code"]})
            else:
                report["inference"] = "unavailable"
    except (BotoCoreError, ClientError, OSError, subprocess.SubprocessError) as exc:
        report["identity"] = "failed"
        report["error"] = exc.response["Error"]["Code"] if isinstance(exc, ClientError) else type(exc).__name__
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))
    return 0 if report["inference"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
