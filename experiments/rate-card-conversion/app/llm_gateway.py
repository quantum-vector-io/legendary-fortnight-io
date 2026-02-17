from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Protocol


class LLMProvider(Protocol):
    """Provider contract used by the semantic mapping agent."""

    provider_name: str

    def map_headers(self, headers: list[str], sample_rows: list[dict]) -> dict[str, str | None]:
        """Return mapping from source header to canonical field or None."""


@dataclass
class ProviderConfig:
    provider: str = "openai"
    model: str = "gpt-4o-mini"


class DeterministicFallbackProvider:
    """No-network fallback for interview demos and local development.

    This keeps the pipeline operational when no API keys are present.
    """

    provider_name = "deterministic-fallback"

    def map_headers(self, headers: list[str], sample_rows: list[dict]) -> dict[str, str | None]:
        del sample_rows
        mapping: dict[str, str | None] = {}
        for header in headers:
            h = header.lower()
            if "origin" in h:
                mapping[header] = "lane_origin"
            elif "dest" in h:
                mapping[header] = "lane_destination"
            elif "rate" in h or "price" in h:
                mapping[header] = "rate_value"
            elif "curr" in h:
                mapping[header] = "currency"
            else:
                mapping[header] = None
        return mapping


class OpenAIProvider(DeterministicFallbackProvider):
    provider_name = "openai"


class ClaudeProvider(DeterministicFallbackProvider):
    provider_name = "claude"


class GeminiProvider(DeterministicFallbackProvider):
    provider_name = "gemini"


def build_provider(config: ProviderConfig) -> LLMProvider:
    """Factory that is intentionally simple and interview-friendly.

    In production replace stub providers with real SDK/API clients.
    """

    provider = config.provider.lower()
    if provider == "openai" and os.getenv("OPENAI_API_KEY"):
        return OpenAIProvider()
    if provider == "claude" and os.getenv("ANTHROPIC_API_KEY"):
        return ClaudeProvider()
    if provider == "gemini" and os.getenv("GOOGLE_API_KEY"):
        return GeminiProvider()
    return DeterministicFallbackProvider()
