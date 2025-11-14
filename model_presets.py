"""Popular model presets for easy selection."""

# Dictionary of popular models organized by category
POPULAR_MODELS = {
    "gpt-4o-mini": {
        "id": "openai/gpt-5-mini",
        "description": "Fast, affordable model for everyday tasks",
        "category": "general",
    },
    "gpt-4o": {
        "id": "openai/gpt-5",
        "description": "Advanced model for complex tasks",
        "category": "advanced",
    },
    "claude-3-haiku": {
        "id": "anthropic/claude-3-haiku",
        "description": "Fast, intelligent model from Anthropic",
        "category": "general",
    },
    "claude-4.5-sonnet": {
        "id": "anthropic/claude-3-sonnet",
        "description": "Balanced model for everyday use",
        "category": "general",
    },
    "claude-4.1-opus": {
        "id": "anthropic/claude-3-opus",
        "description": "Most powerful Claude model",
        "category": "advanced",
    },
    "llama-3.1-70b": {
        "id": "meta-llama/llama-3.1-70b-instruct",
        "description": "Powerful open-source model",
        "category": "general",
    },
    "llama-3.1-405b": {
        "id": "meta-llama/llama-3.1-405b-instruct:free",
        "description": "Most powerful open-source model (free tier)",
        "category": "advanced",
    },
    "gemini-flash-latest": {
        "id": "google/gemini-flash-latest",
        "description": "Google's flagship model",
        "category": "general",
    },
    "command-r-plus": {
        "id": "cohere/command-r-plus",
        "description": "Great for reasoning and complex tasks",
        "category": "advanced",
    },
}


def get_model_by_preset_key(preset_key: str) -> str:
    """
    Get the full model ID by a preset key.

    Args:
        preset_key: A key from POPULAR_MODELS (e.g., 'gpt-4o-mini', 'claude-3-haiku')

    Returns:
        The full model ID string
    """
    model_info = POPULAR_MODELS.get(preset_key)
    if model_info:
        return model_info["id"]
    else:
        # If not a preset key, return as-is (assuming it's already a full model ID)
        return preset_key


def get_preset_key_by_model_id(model_id: str) -> str:
    """
    Get the preset key by the full model ID.

    Args:
        model_id: The full model ID (e.g., 'openai/gpt-4o-mini', 'anthropic/claude-3-haiku')

    Returns:
        The preset key if found, otherwise returns the original model_id
    """
    for preset_key, model_info in POPULAR_MODELS.items():
        if model_info["id"] == model_id:
            return preset_key
    return model_id
