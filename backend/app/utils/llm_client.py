"""Unified LLM client using LiteLLM for multi-provider support."""

import json
import re
from typing import Optional, List, Dict, Any

import litellm

from .logger import get_logger

logger = get_logger('foresight.llm')

# Suppress litellm's verbose logging
litellm.suppress_debug_info = True


class LLMClient:
    """Unified LLM client that works with any provider via LiteLLM."""

    def __init__(self, model: str, api_key: str, temperature: float = 0.7, max_tokens: int = 4096):
        self.model = model
        self.api_key = api_key
        self.temperature = temperature
        self.max_tokens = max_tokens

    def chat(
        self,
        messages: List[Dict[str, str]],
        system: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> str:
        """Send a chat completion request. Returns the response text."""
        call_messages = list(messages)
        if system:
            call_messages.insert(0, {"role": "system", "content": system})

        response = litellm.completion(
            model=self.model,
            messages=call_messages,
            api_key=self.api_key,
            temperature=temperature if temperature is not None else self.temperature,
            max_tokens=max_tokens or self.max_tokens,
            num_retries=3,
        )
        return response.choices[0].message.content

    def chat_json(
        self,
        messages: List[Dict[str, str]],
        system: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> Any:
        """Send a chat request expecting JSON response. Returns parsed dict."""
        json_instruction = "\n\nRespond with valid JSON only, no markdown code blocks."
        if system:
            system += json_instruction
        else:
            system = "Respond with valid JSON only, no markdown code blocks."

        raw = self.chat(
            messages=messages,
            system=system,
            temperature=temperature if temperature is not None else 0.3,
            max_tokens=max_tokens,
        )

        cleaned = raw.strip()
        cleaned = re.sub(r'^```(?:json)?\s*\n?', '', cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r'\n?```\s*$', '', cleaned)
        cleaned = cleaned.strip()

        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            raise ValueError(f"Invalid JSON from LLM: {cleaned[:200]}")


def _build_model_string(provider: str, model: str) -> str:
    """Build a LiteLLM model string from provider + model.

    Handles cases like:
      provider=openrouter, model=google/gemini-2.0-flash-exp:free → openrouter/google/gemini-2.0-flash-exp:free
      provider=openrouter, model=openrouter/google/gemini... → openrouter/google/gemini... (no double prefix)
      provider=anthropic, model=claude-sonnet-4-20250514 → anthropic/claude-sonnet-4-20250514
      provider='', model=gpt-4o → gpt-4o (no prefix)
    """
    if not provider:
        return model
    # Don't double-prefix
    if model.startswith(f"{provider}/"):
        return model
    return f"{provider}/{model}"


# Default models per provider (must support tool use for CrewAI agents)
_DEFAULT_MODELS = {
    "openrouter": "openrouter/auto",
    "anthropic": "claude-sonnet-4-20250514",
    "openai": "gpt-4o",
}


def get_llm_client(
    temperature: float = 0.7,
    max_tokens: int = 4096,
) -> LLMClient:
    """Get an LLMClient configured from DB settings."""
    from ..config import Config

    provider = Config.get("llm_provider")
    model = Config.get("llm_model")
    api_key = Config.get("llm_api_key")

    if not api_key:
        raise ValueError("No LLM API key configured. Open Settings to add one.")

    if not model:
        model = _DEFAULT_MODELS.get(provider, "claude-sonnet-4-20250514")

    litellm_model = _build_model_string(provider, model)
    logger.info(f"LLM client: {litellm_model}")

    return LLMClient(
        model=litellm_model,
        api_key=api_key,
        temperature=temperature,
        max_tokens=max_tokens,
    )


def get_llm_model_string() -> str:
    """Get the LiteLLM model string for CrewAI LLM() constructor."""
    from ..config import Config

    provider = Config.get("llm_provider")
    model = Config.get("llm_model")

    if not model:
        model = _DEFAULT_MODELS.get(provider, "claude-sonnet-4-20250514")

    return _build_model_string(provider, model)


def get_llm_api_key() -> str:
    """Get the API key for the configured LLM provider."""
    from ..config import Config
    api_key = Config.get("llm_api_key")
    if not api_key:
        raise ValueError("No LLM API key configured")
    return api_key
