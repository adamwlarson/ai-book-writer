"""Configuration helpers for the book generation system."""

import os
from typing import Dict, Optional

from pathlib import Path

try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None  # Optional dependency

from model_presets import get_model_by_preset_key


DEFAULT_LOCAL_URL = "http://localhost:1234/v1"
DEFAULT_LOCAL_MODEL = "Mistral-Nemo-Instruct-2407"
DEFAULT_OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
DEFAULT_OPENROUTER_MODEL = "openai/gpt-4o-mini"


# Load environment variables from .env if present without overriding existing values.
if load_dotenv is not None:
    project_root_env = Path(__file__).resolve().parent / ".env"
    load_dotenv(dotenv_path=project_root_env, override=False)
    # Allow python-dotenv to fall back to its default search (covers parent directories).
    load_dotenv(override=False)


def _build_local_config(url: str, model: Optional[str]) -> Dict:
    """Return a config entry targeting a local OpenAI-compatible endpoint."""

    raw_model = model or os.getenv("LOCAL_LLM_MODEL", DEFAULT_LOCAL_MODEL)

    # For local models, try to resolve using presets but fall back to raw value
    # to maintain compatibility with custom local model names
    resolved_model = get_model_by_preset_key(raw_model)

    return {
        "model": resolved_model,
        "base_url": url,
        "api_key": os.getenv("LOCAL_LLM_API_KEY", "not-needed"),
    }


def _build_openrouter_config(model_override: Optional[str]) -> Dict:
    """Return a config entry configured for OpenRouter."""

    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        raise ValueError(
            "OPENROUTER_API_KEY is required to use OpenRouter. "
            "Set the environment variable and try again."
        )

    base_url = os.getenv("OPENROUTER_BASE_URL", DEFAULT_OPENROUTER_BASE_URL)

    # Resolve model using presets if applicable
    raw_model = model_override or os.getenv(
        "OPENROUTER_MODEL", DEFAULT_OPENROUTER_MODEL
    )
    model = get_model_by_preset_key(raw_model)

    # Optional headers recommended by OpenRouter
    headers = {}
    referer = os.getenv("OPENROUTER_HTTP_REFERER")
    if referer:
        headers["HTTP-Referer"] = referer

    title = os.getenv("OPENROUTER_APP_TITLE")
    if title:
        headers["X-Title"] = title

    config: Dict = {
        "model": model,
        "base_url": base_url,
        "api_key": api_key,
    }

    if headers:
        config["headers"] = headers

    return config


def get_config(
    local_url: Optional[str] = None,
    *,
    use_openrouter: Optional[bool] = None,
    model: Optional[str] = None,
) -> Dict:
    """Construct the shared AutoGen configuration.

    Args:
        local_url: Explicit local endpoint URL. If ``None`` the value from the
            ``LOCAL_LLM_URL`` environment variable or the default localhost
            endpoint is used.
        use_openrouter: Force enabling or disabling OpenRouter. When ``None``
            the function automatically prefers OpenRouter if an API key is
            available and no explicit local URL was supplied.
        model: Optional model name override applied to whichever provider is
            selected.
    """

    resolved_local_url = local_url or os.getenv("LOCAL_LLM_URL", DEFAULT_LOCAL_URL)
    openrouter_key_present = bool(os.getenv("OPENROUTER_API_KEY"))

    if use_openrouter is None:
        use_openrouter = openrouter_key_present and not local_url

    if use_openrouter:
        config_list = [_build_openrouter_config(model)]
    else:
        config_list = [_build_local_config(resolved_local_url, model)]

    return {
        "seed": 42,
        "temperature": 0.7,
        "config_list": config_list,
        "timeout": int(os.getenv("LLM_TIMEOUT", "600")),
        "cache_seed": None,
    }
