"""Prepared AgentCore entrypoint. Running this module is LOCAL; it never deploys.

The future runtime validates an existing application session behind IAM. The
FastAPI-to-runtime forwarding integration is not deployed or enabled yet.
"""
from bedrock_agentcore.runtime import BedrockAgentCoreApp
from backend.api import app as api
from backend.config import Settings
from backend.models import RuntimeRequest
from backend.orchestrator import chat

app = BedrockAgentCoreApp()


@app.entrypoint
def invoke(payload):
    request = RuntimeRequest.model_validate(payload)
    service = api.state.service
    account = api.state.auth.session(request.session_token.get_secret_value())
    profile = service.profile(account["uid"])
    result, _ = chat(service, Settings(), account["uid"], profile["role"], request.message)
    return result.model_dump(mode="json")


if __name__ == "__main__":
    app.run()
