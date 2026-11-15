# Local AWS and model configuration

Verified on **November 14, 2026, America/Detroit**. No AWS infrastructure was created or deployed.

The initial machine had Python, Node, npm, `uv`, and Java, but no AWS CLI on PATH and no AWS credential files. The AWS CLI was installed in the repository virtual environment. After the user supplied a private `.env`, its standard AWS assignments were normalized, its permissions restricted to owner read/write, and credential values were kept out of tool output and source files.

| Check | Observed result |
| --- | --- |
| AWS CLI STS identity | Verified; account identifiers intentionally omitted |
| Boto3 STS identity | Verified |
| Configured region | `us-east-1` |
| Read-only Bedrock catalog | Listed active Amazon Nova text-capable models |
| Nova Lite Converse | Passed for `amazon.nova-lite-v1:0` |
| Nova Pro Converse | Passed for `amazon.nova-pro-v1:0` |
| Nova 2 Lite Converse | Passed for `us.amazon.nova-2-lite-v1:0` |
| Selected application model | `us.amazon.nova-2-lite-v1:0` |
| Live nested delegation | Job Market, Assessment, Coach, and Marketplace each passed focused checks with Nova 2 Lite |
| Storage | DynamoDB Local 3.3.2 at `http://127.0.0.1:8001`; table `SkillPilot` |

The `us.` model ID is a Bedrock inference profile; it can route inference across supported US regions. Availability in the catalog alone is not proof of invoke permission. Only the model IDs listed as passed above were verified by inference. The selected model completed the four-specialist routing checks; initial Nova Lite/Pro runs exposed inconsistent task completion, which also led to adding deterministic evidence-before-summary steering.

Current settings:

```dotenv
AWS_DEFAULT_REGION=us-east-1
SKILLPILOT_AI_MODE=bedrock
SKILLPILOT_MODEL_ID=us.amazon.nova-2-lite-v1:0
SKILLPILOT_REPOSITORY=dynamodb-local
SKILLPILOT_DYNAMODB_ENDPOINT=http://127.0.0.1:8001
SKILLPILOT_TABLE_NAME=SkillPilot
```

All credentials remain in the user's ignored `.env` or standard AWS credential chain. Never put them in `VITE_*` variables. Temporary credentials may expire; rerun `uv run python -m scripts.aws_preflight` after renewal. The preflight report in `.local/aws-preflight.json` contains only status, region, model IDs, usage, and safe error codes. It never creates infrastructure or attempts to grant model access.

To use a particular model in the preflight without editing `.env`:

```bash
SKILLPILOT_MODEL_ID=us.amazon.nova-2-lite-v1:0 uv run python -m scripts.aws_preflight
```

For offline development, explicitly set `SKILLPILOT_AI_MODE=mock`. The UI labels this mode. A Bedrock error does not silently turn into a mock response.

DynamoDB Local uses fixed dummy credentials only for its loopback endpoint; those are separate from the real Bedrock credentials. The table-setup script refuses non-loopback endpoints. Selecting remote `dynamodb` mode uses an already-existing table and never creates one.

Versions installed and verified: Strands Agents 1.65.0, Boto3 1.44.3, FastAPI 0.163.0, Bedrock AgentCore SDK 1.26.0, AWS CLI 1.46.3. Exact dependencies are locked in `uv.lock` and `frontend/package-lock.json`.

References: [AWS workshop](https://github.com/aws-samples/sample-strands-agents-hands-on-workshop), [Bedrock Converse](https://docs.aws.amazon.com/bedrock/latest/APIReference/API_runtime_Converse.html), [DynamoDB Local](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/DynamoDBLocal.DownloadingAndRunning.html).
