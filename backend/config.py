from typing import Literal
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="SKILLPILOT_", env_file=".env", extra="ignore")
    ai_mode: Literal["mock", "bedrock"] = "mock"
    repository: Literal["memory", "dynamodb-local", "dynamodb"] = "memory"
    model_id: str = "us.amazon.nova-2-lite-v1:0"
    table_name: str = "SkillPilot"
    dynamodb_endpoint: str = "http://localhost:8001"

