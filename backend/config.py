"""Pydantic Settings — credentials from .env file + environment variables."""

from __future__ import annotations

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # CTFd
    ctfd_url: str = "http://localhost:8000"
    ctfd_user: str = "admin"
    ctfd_pass: str = "admin"
    ctfd_token: str = ""

    # Primary API Keys
    anthropic_api_key: str = ""
    openai_api_key: str = ""
    gemini_api_key: str = ""
    openrouter_api_key: str = ""
    deepseek_api_key: str = ""
    groq_api_key: str = ""

    # Provider & Custom Endpoints
    aws_region: str = "us-east-1"
    aws_bearer_token: str = ""
    azure_openai_endpoint: str = ""
    azure_openai_api_key: str = ""
    opencode_zen_api_key: str = ""
    ollama_base_url: str = "http://localhost:11434/v1"
    custom_openai_base_url: str = ""
    custom_openai_api_key: str = ""

    # Execution & Sandbox Configuration
    sandbox_mode: str = "auto"  # "docker", "local", or "auto"
    sandbox_image: str = "ctf-sandbox"
    max_concurrent_challenges: int = 10
    max_attempts_per_challenge: int = 3
    container_memory_limit: str = "16g"

    # State & Persistence
    state_db_path: str = "ctf_state.sqlite3"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "extra": "ignore"}

