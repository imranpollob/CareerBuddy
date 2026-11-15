"""Amazon Bedrock AgentCore Runtime entrypoint for the CareerBuddy agent.

The FastAPI app forwards each chat message here with the user's opaque session token
(see backend/api.py, SKILLPILOT_AGENT_RUNTIME_ARN). The runtime itself re-validates that
token against the sessions in DynamoDB, so identity is never taken from the caller;
then it runs the Strands orchestrator + specialists and persists the conversation.

Configuration comes from runtime environment variables (SKILLPILOT_REPOSITORY=dynamodb,
SKILLPILOT_TABLE_NAME, SKILLPILOT_AI_MODE=bedrock, SKILLPILOT_MODEL_ID). No FastAPI here.
"""
from bedrock_agentcore.runtime import BedrockAgentCoreApp

from backend import conversation
from backend.auth import Auth
from backend.config import Settings
from backend.db import DynamoRepository, MemoryRepository
from backend.models import RuntimeRequest
from backend.orchestrator import chat
from backend.service import Service

app = BedrockAgentCoreApp()
_state = None  # (settings, service, auth), built on first invocation and reused by the warm microVM


def state():
    global _state
    if _state is None:
        settings = Settings()
        repo = (DynamoRepository(settings.table_name) if settings.repository == "dynamodb" else
                DynamoRepository(settings.table_name, settings.dynamodb_endpoint) if settings.repository == "dynamodb-local" else
                MemoryRepository())
        service = Service(repo, settings)
        _state = (settings, service, Auth(service, settings))
    return _state


@app.entrypoint
def invoke(payload):
    request = RuntimeRequest.model_validate(payload)  # extra fields such as "uid" are rejected
    settings, service, auth = state()
    account = auth.session(request.session_token.get_secret_value())
    uid = account["uid"]
    role = service.profile(uid)["role"]
    saved = conversation.history(service.repo, uid)
    result, _ = chat(service, settings, uid, role, request.message, conversation.model_messages(saved))
    conversation.append(service.repo, uid, saved, request.message, result)
    return result.model_dump(mode="json")


if __name__ == "__main__":
    app.run()
