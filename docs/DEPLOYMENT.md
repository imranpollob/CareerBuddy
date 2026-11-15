# AgentCore preparation — not deployed

No AWS infrastructure has been created. Local Bedrock inference uses the existing hackathon account. The DynamoDB table used during development is on the local Java emulator.

`backend/main.py` wraps the same orchestrator and four specialists in `BedrockAgentCoreApp` with an `@app.entrypoint`. Its input is `{"message":"Prepare a Python assessment"}` and output is the typed chat response. The future runtime entrypoint is fixed to the candidate demo identity and accepts no caller-selected role or user ID. FastAPI currently calls the orchestrator in process; it does not forward requests to a deployed runtime. A real authenticated identity handoff is required before enabling employer operations remotely.

For a local runtime check only:

```bash
uv run python -m backend.main
curl -X POST http://127.0.0.1:8080/invocations \
  -H 'Content-Type: application/json' \
  -d '{"message":"Hello"}'
```

`deployment/Dockerfile` and its pinned requirements prepare a single application image. Build from the repository root, targeting `linux/arm64` for AgentCore, only after Docker is available. The image copies only `backend/` and dependencies; `.env`, `.local`, and credentials are excluded. The image itself has not been built here because Docker is not installed.

Deployment requires the user's explicit approval. Before that approval, prepare a concrete region/model/table selection and minimal execution-role permissions. Do not assume the temporary credentials permit table creation, IAM changes, ECR, or runtime provisioning. The application needs only Bedrock inference and access to the single existing `SkillPilot` table; the deployment mechanism may require packaging resources.

The reference workshop's current AgentCore CLI creates packaging/staging infrastructure when deploying. Its default Strands template also adds Memory, which is outside this MVP. Do not run the default template/deploy workflow unreviewed. Use an empty/by-code runtime configuration or a reviewed container workflow with no extra application services.

Sources reviewed:

- [Workshop Module 5](https://github.com/aws-samples/sample-strands-agents-hands-on-workshop/tree/main/samples/05-deploy)
- [AgentCore CLI workflow](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/runtime-get-started-cli.html)

