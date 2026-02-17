import pandas as pd

from app.agentic_orchestrator import run_self_improving_mapping_agent
from app.llm_gateway import ProviderConfig, build_provider


def test_build_provider_uses_fallback_without_keys(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)

    provider = build_provider(ProviderConfig(provider="openai"))

    assert provider.provider_name == "deterministic-fallback"


def test_hybrid_agent_fixes_missing_required_mapping():
    df = pd.DataFrame(
        [
            {
                "From City": "Seoul",
                "To Port": "Hamburg",
                "Price USD": "1200",
            }
        ]
    )

    provider = build_provider(ProviderConfig(provider="openai"))
    result = run_self_improving_mapping_agent(df, provider)

    assert "lane_origin" in result.improved_mapping
    assert "lane_destination" in result.improved_mapping
    assert "rate_value" in result.improved_mapping
