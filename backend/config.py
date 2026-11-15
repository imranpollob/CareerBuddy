from typing import Literal
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="SKILLPILOT_", env_file=".env", extra="ignore")
    ai_mode: Literal["mock", "bedrock"] = "mock"
    repository: Literal["memory", "dynamodb-local", "dynamodb"] = "memory"
    model_id: str = "us.amazon.nova-2-lite-v1:0"
    table_name: str = "SkillPilot"
    dynamodb_endpoint: str = "http://localhost:8001"
    seed_accounts: bool = False
    actor_credentials_path: str = ".local/actor-accounts.json"
    secure_cookies: bool = False
    session_seconds: int = 14400
    # When set, /api/chat runs the agent on this Amazon Bedrock AgentCore Runtime instead of in-process.
    agent_runtime_arn: str = ""

