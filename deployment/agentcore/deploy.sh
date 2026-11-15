#!/usr/bin/env bash
# Deploy the CareerBuddy agent to Amazon Bedrock AgentCore Runtime with the AgentCore CLI
# (direct code deploy, CDK-managed). Run where the AgentCore CLI and deploy permissions exist,
# e.g. the workshop Code Editor. Safe to re-run: later runs redeploy the updated code.
#   bash deploy.sh            # uses SKILLPILOT_TABLE_NAME (default workshop-skillpilot)
set -euo pipefail
BUNDLE="$(cd "$(dirname "$0")" && pwd)"
DEFAULT_WORK="$HOME/careerbuddy-agentcore"; [ -d /workshop ] && DEFAULT_WORK=/workshop/careerbuddy-agentcore
WORK="${CAREERBUDDY_WORKDIR:-$DEFAULT_WORK}"
TABLE="${SKILLPILOT_TABLE_NAME:-workshop-skillpilot}"
MODEL="${SKILLPILOT_MODEL_ID:-us.amazon.nova-2-lite-v1:0}"
RUNTIME=CareerBuddyAgent

mkdir -p "$WORK" && cd "$WORK"
[ -d careerbuddy ] || agentcore create --name careerbuddy --template empty
cd careerbuddy
grep -q "\"$RUNTIME\"" agentcore/agentcore.json || agentcore add runtime --name "$RUNTIME" --language python

APP="app/$RUNTIME"
mkdir -p "$APP"
rm -rf "$APP/backend"
cp -r "$BUNDLE/backend" "$APP/backend"
cp "$BUNDLE/main.py" "$APP/main.py"
(
  cd "$APP"
  [ -f pyproject.toml ] || uv init --bare --python 3.13
  uv add strands-agents bedrock-agentcore boto3 pydantic pydantic-settings email-validator \
         python-dotenv "pwdlib[argon2]" aws-opentelemetry-distro
)
python3 "$BUNDLE/patch_cdk.py" agentcore/cdk/lib/cdk-stack.ts "$TABLE" "$RUNTIME" "$MODEL"
agentcore deploy --yes
agentcore status
