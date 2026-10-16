from backend.config import Settings
from backend.models import (
    auto_detect_default_models,
    context_window,
    effort_from_spec,
    model_id_from_spec,
    provider_from_spec,
    resolve_model,
    supports_vision,
)


def test_spec_parsers():
    assert provider_from_spec("google/gemini-2.0-flash") == "google"
    assert model_id_from_spec("google/gemini-2.0-flash") == "gemini-2.0-flash"
    assert effort_from_spec("claude-sdk/claude-opus-4-6/max") == "max"
    assert effort_from_spec("google/gemini-2.0-flash") is None


def test_vision_and_context_windows():
    assert supports_vision("google/gemini-2.0-flash") is True
    assert supports_vision("openai/gpt-4o") is True
    assert context_window("google/gemini-1.5-pro") == 2_000_000
    assert context_window("openai/gpt-4o") == 128_000


def test_auto_detect_default_models():
    s = Settings(
        gemini_api_key="test-gemini",
        openai_api_key="test-openai",
        anthropic_api_key="test-anthropic",
    )
    models = auto_detect_default_models(s)
    assert any("google/" in m for m in models)
    assert any("openai/" in m for m in models)
    assert any("anthropic/" in m for m in models)


def test_resolve_model_instances():
    s = Settings(
        gemini_api_key="test-gemini",
        openai_api_key="test-openai",
        anthropic_api_key="test-anthropic",
        deepseek_api_key="test-deepseek",
        groq_api_key="test-groq",
    )
    m_google = resolve_model("google/gemini-2.0-flash", s)
    assert m_google is not None

    m_openai = resolve_model("openai/gpt-4o", s)
    assert m_openai is not None

    m_anthropic = resolve_model("anthropic/claude-3-5-haiku-latest", s)
    assert m_anthropic is not None

    m_deepseek = resolve_model("deepseek/deepseek-chat", s)
    assert m_deepseek is not None

    m_groq = resolve_model("groq/llama-3.3-70b-versatile", s)
    assert m_groq is not None
