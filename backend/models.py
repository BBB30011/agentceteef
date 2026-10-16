"""Model resolution — Multi-provider routing supporting OpenAI, Anthropic, Google, DeepSeek, Groq, OpenRouter, Ollama, Bedrock, Azure, Claude SDK, and Codex."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING

import boto3
from pydantic_ai.models import Model
from pydantic_ai.models.anthropic import AnthropicModel, AnthropicModelSettings
from pydantic_ai.models.bedrock import BedrockConverseModel, BedrockModelSettings
from pydantic_ai.models.google import GoogleModel, GoogleModelSettings
from pydantic_ai.models.openai import OpenAIChatModel, OpenAIChatModelSettings
from pydantic_ai.providers.anthropic import AnthropicProvider
from pydantic_ai.providers.bedrock import BedrockProvider
from pydantic_ai.providers.google import GoogleProvider
from pydantic_ai.providers.openai import OpenAIProvider
from pydantic_ai.settings import ModelSettings

if TYPE_CHECKING:
    from backend.config import Settings

logger = logging.getLogger(__name__)

# Compatibility alias
OpenAIModel = OpenAIChatModel
OpenAIModelSettings = OpenAIChatModelSettings

# Default baseline models across providers
DEFAULT_MODELS: list[str] = [
    "claude-sdk/claude-opus-4-6/medium",
    "claude-sdk/claude-opus-4-6/max",
    "codex/gpt-5.4",
    "codex/gpt-5.4-mini",
    "codex/gpt-5.3-codex",
]

# Context window sizes (tokens)
CONTEXT_WINDOWS: dict[str, int] = {
    # Anthropic
    "us.anthropic.claude-opus-4-6-v1": 1_000_000,
    "claude-opus-4-6": 1_000_000,
    "claude-3-7-sonnet-latest": 200_000,
    "claude-3-7-sonnet-20250219": 200_000,
    "claude-3-5-sonnet-latest": 200_000,
    "claude-3-5-sonnet-20241022": 200_000,
    "claude-3-5-haiku-latest": 200_000,
    # OpenAI & Codex
    "gpt-5.4": 1_000_000,
    "gpt-5.4-mini": 400_000,
    "gpt-5.3-codex": 1_000_000,
    "gpt-5.3-codex-spark": 128_000,
    "gpt-4o": 128_000,
    "gpt-4o-mini": 128_000,
    "o1": 200_000,
    "o3-mini": 200_000,
    "gpt-4.5-preview": 128_000,
    # Google
    "gemini-2.5-pro": 1_000_000,
    "gemini-2.0-flash": 1_000_000,
    "gemini-2.0-flash-thinking-exp": 1_000_000,
    "gemini-1.5-pro": 2_000_000,
    "gemini-1.5-flash": 1_000_000,
    "gemini-3-flash-preview": 1_000_000,
    # DeepSeek & others
    "deepseek-chat": 64_000,
    "deepseek-reasoner": 64_000,
}

# Models that support image vision
VISION_MODELS: set[str] = {
    "us.anthropic.claude-opus-4-6-v1",
    "claude-opus-4-6",
    "claude-3-7-sonnet-latest",
    "claude-3-7-sonnet-20250219",
    "claude-3-5-sonnet-latest",
    "claude-3-5-sonnet-20241022",
    "gpt-5.4",
    "gpt-5.4-mini",
    "gpt-4o",
    "gpt-4o-mini",
    "gpt-4.5-preview",
    "gemini-2.5-pro",
    "gemini-2.0-flash",
    "gemini-2.0-flash-thinking-exp",
    "gemini-1.5-pro",
    "gemini-1.5-flash",
    "gemini-3-flash-preview",
}


def auto_detect_default_models(settings: Settings) -> list[str]:
    """Detect available credentials and return a tailored swarm roster."""
    models: list[str] = []

    # Direct Google AI Studio
    if settings.gemini_api_key:
        models.append("google/gemini-2.5-pro")
        models.append("google/gemini-2.0-flash")

    # Direct Anthropic API
    if settings.anthropic_api_key:
        models.append("anthropic/claude-3-7-sonnet-latest")
        models.append("anthropic/claude-3-5-haiku-latest")

    # Direct OpenAI API
    if settings.openai_api_key:
        models.append("openai/gpt-4o")
        models.append("openai/o3-mini")

    # OpenRouter
    if settings.openrouter_api_key:
        models.append("openrouter/anthropic/claude-3.7-sonnet")

    # DeepSeek
    if settings.deepseek_api_key:
        models.append("deepseek/deepseek-chat")

    # Groq
    if settings.groq_api_key:
        models.append("groq/llama-3.3-70b-versatile")

    # Bedrock
    if settings.aws_bearer_token:
        models.append("bedrock/us.anthropic.claude-opus-4-6-v1")

    # Azure OpenAI
    if settings.azure_openai_endpoint and settings.azure_openai_api_key:
        models.append("azure/gpt-4o")

    # Zen
    if settings.opencode_zen_api_key:
        models.append("zen/gpt-5.3-codex-spark")

    # Antigravity CLI (Tokenless Host Execution)
    import shutil
    if shutil.which("agy") or Path("/home/kali/.local/bin/agy").exists():
        models.append("agy/default")

    # If nothing detected, return original default models (may rely on claude-sdk or codex cli)
    if not models:
        return list(DEFAULT_MODELS)

    return models



def resolve_model(spec: str, settings: Settings) -> Model:
    """Resolve a 'provider/model_id' spec to a Pydantic AI Model."""
    provider = provider_from_spec(spec)
    model_id = model_id_from_spec(spec)

    match provider:
        case "google":
            if not settings.gemini_api_key:
                logger.warning("GEMINI_API_KEY is not set in settings or environment.")
            return GoogleModel(
                model_id,
                provider=GoogleProvider(api_key=settings.gemini_api_key or "missing_key"),
            )

        case "openai":
            if not settings.openai_api_key:
                logger.warning("OPENAI_API_KEY is not set in settings or environment.")
            return OpenAIChatModel(
                model_id,
                provider=OpenAIProvider(api_key=settings.openai_api_key or "missing_key"),
            )

        case "anthropic":
            if not settings.anthropic_api_key:
                logger.warning("ANTHROPIC_API_KEY is not set in settings or environment.")
            return AnthropicModel(
                model_id,
                provider=AnthropicProvider(api_key=settings.anthropic_api_key or "missing_key"),
            )

        case "openrouter":
            return OpenAIChatModel(
                model_id,
                provider=OpenAIProvider(
                    base_url="https://openrouter.ai/api/v1",
                    api_key=settings.openrouter_api_key or "missing_key",
                ),
            )

        case "deepseek":
            return OpenAIChatModel(
                model_id,
                provider=OpenAIProvider(
                    base_url="https://api.deepseek.com/v1",
                    api_key=settings.deepseek_api_key or "missing_key",
                ),
            )

        case "groq":
            return OpenAIChatModel(
                model_id,
                provider=OpenAIProvider(
                    base_url="https://api.groq.com/openai/v1",
                    api_key=settings.groq_api_key or "missing_key",
                ),
            )

        case "ollama" | "local":
            return OpenAIChatModel(
                model_id,
                provider=OpenAIProvider(
                    base_url=settings.ollama_base_url,
                    api_key="ollama",
                ),
            )

        case "custom":
            return OpenAIChatModel(
                model_id,
                provider=OpenAIProvider(
                    base_url=settings.custom_openai_base_url,
                    api_key=settings.custom_openai_api_key or "custom",
                ),
            )

        case "azure":
            return OpenAIChatModel(
                model_id,
                provider=OpenAIProvider(
                    base_url=settings.azure_openai_endpoint,
                    api_key=settings.azure_openai_api_key,
                ),
            )

        case "zen":
            return OpenAIChatModel(
                model_id,
                provider=OpenAIProvider(
                    base_url="https://opencode.ai/zen/v1",
                    api_key=settings.opencode_zen_api_key,
                ),
            )

        case "bedrock":
            if settings.aws_bearer_token:
                return BedrockConverseModel(
                    model_id,
                    provider=BedrockProvider(
                        api_key=settings.aws_bearer_token,
                        region_name=settings.aws_region,
                    ),
                )
            else:
                session = boto3.Session()
                client = session.client("bedrock-runtime", region_name=settings.aws_region)
                return BedrockConverseModel(
                    model_id,
                    provider=BedrockProvider(bedrock_client=client),
                )

        case "claude-sdk" | "codex" | "agy" | "antigravity":
            raise ValueError(
                f"Provider '{provider}' uses its own native runner backend, not Pydantic AI. "
                f"resolve_model() should not be called for {spec}."
            )


        case _:
            # Fallback to OpenAI-compatible provider if unrecognized
            logger.info("Unrecognized provider %r, attempting OpenAI-compatible resolution", provider)
            return OpenAIChatModel(
                model_id,
                provider=OpenAIProvider(
                    api_key=settings.openai_api_key or "missing_key",
                ),
            )


def resolve_model_settings(spec: str) -> ModelSettings:
    """Get provider-specific model settings with caching or thinking enabled."""
    provider = spec.split("/", 1)[0]
    match provider:
        case "google":
            return GoogleModelSettings(
                max_tokens=64_000,
                google_thinking_config={
                    "thinking_level": "high",
                    "include_thoughts": True,
                },
            )
        case "anthropic":
            return AnthropicModelSettings(
                max_tokens=64_000,
            )
        case "bedrock":
            return BedrockModelSettings(
                max_tokens=128_000,
                bedrock_cache_instructions=True,
                bedrock_cache_tool_definitions=True,
                bedrock_cache_messages=True,
            )
        case "azure" | "zen" | "openai" | "openrouter" | "deepseek" | "groq" | "ollama" | "local" | "custom":
            return OpenAIChatModelSettings(
                max_tokens=64_000,
            )
        case _:
            return ModelSettings(max_tokens=64_000)


def model_id_from_spec(spec: str) -> str:
    """Extract just the model ID from a spec (strips effort suffix)."""
    parts = spec.split("/")
    return parts[1] if len(parts) >= 2 else spec


def provider_from_spec(spec: str) -> str:
    """Extract the provider from a spec."""
    return spec.split("/", 1)[0]


def effort_from_spec(spec: str) -> str | None:
    """Extract effort level from a spec like 'claude-sdk/claude-opus-4-6/max'."""
    parts = spec.split("/")
    if len(parts) >= 3 and parts[2] in ("low", "medium", "high", "max"):
        return parts[2]
    return None


def supports_vision(spec: str) -> bool:
    """Check if a model spec supports vision."""
    return model_id_from_spec(spec) in VISION_MODELS


def context_window(spec: str) -> int:
    """Get context window size for a model spec."""
    return CONTEXT_WINDOWS.get(model_id_from_spec(spec), 200_000)
