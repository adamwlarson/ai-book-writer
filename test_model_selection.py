#!/usr/bin/env python3
"""
Test script to verify the new model selection system works properly.
"""
import os
from config import get_config
from model_presets import POPULAR_MODELS, get_model_by_preset_key


def test_model_presets():
    """Test that model presets work correctly."""
    print("Testing model presets...")

    for preset_key, model_info in POPULAR_MODELS.items():
        resolved_model = get_model_by_preset_key(preset_key)
        print(f"  {preset_key} -> {resolved_model}")
        assert resolved_model == model_info["id"], f"Failed to resolve {preset_key}"

    # Test non-preset key (should return as-is)
    custom_model = "my/custom-model"
    resolved_custom = get_model_by_preset_key(custom_model)
    assert resolved_custom == custom_model, "Custom model should return as-is"
    print(f"  Custom model: {custom_model} -> {resolved_custom}")

    print("All preset tests passed!\n")


def test_config_with_presets():
    """Test that the config system resolves presets correctly."""
    print("Testing config system with presets...")

    # Test with environment variable containing a preset key
    os.environ["OPENROUTER_API_KEY"] = "test-key"  # Required to avoid errors
    os.environ["OPENROUTER_MODEL"] = "gpt-4o-mini"  # A preset key

    config = get_config(use_openrouter=True, model=None)
    model_used = config["config_list"][0]["model"]
    expected_model = "openai/gpt-4o-mini"

    print(f"  Config with preset 'gpt-4o-mini' -> actual model: {model_used}")
    assert model_used == expected_model, f"Expected {expected_model}, got {model_used}"

    # Test with environment variable containing a full model ID
    os.environ["OPENROUTER_MODEL"] = "anthropic/claude-3-sonnet"

    config = get_config(use_openrouter=True, model=None)
    model_used = config["config_list"][0]["model"]
    expected_model = "anthropic/claude-3-sonnet"

    print(
        f"  Config with full ID 'anthropic/claude-3-sonnet' -> actual model: {model_used}"
    )
    assert model_used == expected_model, f"Expected {expected_model}, got {model_used}"

    # Test with model override parameter
    config = get_config(use_openrouter=True, model="gpt-4o")  # Using preset key
    model_used = config["config_list"][0]["model"]
    expected_model = "openai/gpt-4o"

    print(f"  Config with override 'gpt-4o' -> actual model: {model_used}")
    assert model_used == expected_model, f"Expected {expected_model}, got {model_used}"

    print("All config tests passed!\n")


if __name__ == "__main__":
    print("Testing the new user-friendly model selection system...\n")

    test_model_presets()
    test_config_with_presets()

    print("All tests passed! The model selection system works correctly.")
