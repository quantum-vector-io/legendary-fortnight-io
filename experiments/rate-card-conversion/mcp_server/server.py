"""Educational MCP server for the Rate Card Conversion project.

Run with:
    python -m mcp_server.server

If you install mcp SDK:
    pip install mcp
"""

from __future__ import annotations

import json
from pathlib import Path

from app.agentic_orchestrator import run_self_improving_mapping_agent
from app.extractors import load_rate_card
from app.llm_gateway import ProviderConfig, build_provider
from app.pipeline import convert_dataframe

try:
    from mcp.server.fastmcp import FastMCP
except Exception as exc:  # pragma: no cover - educational runtime guard
    raise RuntimeError(
        "MCP SDK is required. Install with `pip install mcp` and rerun."
    ) from exc


mcp = FastMCP(name="rate-card-conversion-mcp")


@mcp.tool()
def convert_rate_card(file_path: str) -> str:
    """Convert CSV/XLSX/PDF rate card and return canonical JSON string."""

    path = Path(file_path)
    content = path.read_bytes()
    df = load_rate_card(path.name, content)
    result = convert_dataframe(df)
    return result.model_dump_json(indent=2)


@mcp.tool()
def preview_hybrid_agent(file_path: str, provider: str = "openai") -> str:
    """Show deterministic mapping vs hybrid (self-improving) mapping."""

    path = Path(file_path)
    df = load_rate_card(path.name, path.read_bytes())
    gateway = build_provider(ProviderConfig(provider=provider))
    result = run_self_improving_mapping_agent(df, gateway)
    return json.dumps(
        {
            "initial_mapping": result.initial_mapping,
            "improved_mapping": result.improved_mapping,
            "suggestions": [s.__dict__ for s in result.suggestions],
            "provider_used": gateway.provider_name,
        },
        indent=2,
    )


@mcp.tool()
def architecture_overview() -> str:
    """Return interview-focused architecture summary."""

    return (
        "Layers: ingestion -> extraction -> deterministic RAG mapping -> validation -> canonical output. "
        "MCP exposes conversion and hybrid-agent introspection tools. "
        "Provider abstraction supports OpenAI, Claude, Gemini with deterministic fallback for safe demos."
    )


if __name__ == "__main__":
    mcp.run()
