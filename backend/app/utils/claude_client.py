"""Anthropic Claude SDK wrapper"""

import json
import re
from typing import Optional, Dict, Any, List

from anthropic import Anthropic

from ..config import Config
from .retry import retry_with_backoff


class ClaudeClient:
    def __init__(self, api_key=None, model=None):
        self.api_key = api_key or Config.CLAUDE_API_KEY
        self.model = model or Config.CLAUDE_MODEL_NAME

        if not self.api_key:
            raise ValueError("CLAUDE_API_KEY not configured")

        self.client = Anthropic(api_key=self.api_key)

    @retry_with_backoff(max_retries=3, exceptions=(Exception,))
    def chat(self, messages, system=None, temperature=0.7, max_tokens=4096):
        kwargs = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if system:
            kwargs["system"] = system

        response = self.client.messages.create(**kwargs)
        return response.content[0].text

    def chat_json(self, messages, system=None, temperature=0.3, max_tokens=4096):
        if system:
            system += "\n\nRespond with valid JSON only, no markdown code blocks."
        else:
            system = "Respond with valid JSON only, no markdown code blocks."

        response = self.chat(
            messages=messages,
            system=system,
            temperature=temperature,
            max_tokens=max_tokens,
        )

        cleaned = response.strip()
        cleaned = re.sub(r'^```(?:json)?\s*\n?', '', cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r'\n?```\s*$', '', cleaned)
        cleaned = cleaned.strip()

        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            raise ValueError(f"Invalid JSON from Claude: {cleaned[:200]}")
