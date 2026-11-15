"""Prepared AgentCore entrypoint. Running this module is LOCAL; it never deploys.

The future runtime is a candidate-only demo entrypoint behind IAM. Employer
actions remain in FastAPI until an authenticated identity handoff is designed.
"""
from bedrock_agentcore.runtime import BedrockAgentCoreApp
from backend.api import app as api
from backend.config import Settings
from backend.models import ChatRequest
from backend.orchestrator import chat

app = BedrockAgentCoreApp()


@app.entrypoint
def invoke(payload):
    request = ChatRequest.model_validate(payload)
    service = api.state.service
    service.seed()
    result, _ = chat(service, Settings(), "candidate-demo", "candidate", request.message)
    return result.model_dump(mode="json")


if __name__ == "__main__":
    app.run()
