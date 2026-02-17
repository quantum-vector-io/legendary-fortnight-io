from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from app.llm_gateway import LLMProvider
from app.mapping import build_column_mapping


@dataclass
class ImprovementSuggestion:
    issue: str
    action: str


@dataclass
class HybridAgentResult:
    initial_mapping: dict[str, str]
    improved_mapping: dict[str, str]
    suggestions: list[ImprovementSuggestion]


def run_self_improving_mapping_agent(df: pd.DataFrame, provider: LLMProvider) -> HybridAgentResult:
    """Hybrid deterministic + LLM planning loop.

    Step 1: deterministic mapping.
    Step 2: provider suggestion for missing columns.
    Step 3: apply safe improvement only for required fields.
    """

    deterministic = build_column_mapping(df)
    improved_mapping = dict(deterministic.column_map)

    llm_mapping = provider.map_headers(
        headers=[str(c) for c in df.columns],
        sample_rows=df.head(3).to_dict(orient="records"),
    )

    suggestions: list[ImprovementSuggestion] = []
    required = {"lane_origin", "lane_destination", "rate_value"}
    for source, target in llm_mapping.items():
        if target in required and target not in improved_mapping:
            improved_mapping[target] = source
            suggestions.append(
                ImprovementSuggestion(
                    issue=f"Missing required field mapping: {target}",
                    action=f"Mapped {source} -> {target} from provider={provider.provider_name}",
                )
            )

    return HybridAgentResult(
        initial_mapping=deterministic.column_map,
        improved_mapping=improved_mapping,
        suggestions=suggestions,
    )
