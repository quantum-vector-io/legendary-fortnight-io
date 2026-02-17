from dataclasses import dataclass
from difflib import SequenceMatcher
import pandas as pd

from app.rag import retrieve_field_candidates
from app.schemas import MappingEvidence


@dataclass
class MappingResult:
    column_map: dict[str, str]
    evidence: list[MappingEvidence]


def _score_match(column: str, canonical: str) -> float:
    return SequenceMatcher(None, column.lower(), canonical.lower()).ratio()


def build_column_mapping(df: pd.DataFrame) -> MappingResult:
    evidence: list[MappingEvidence] = []
    column_map: dict[str, str] = {}
    for column in df.columns:
        candidates = retrieve_field_candidates(column, top_k=1)
        best_field, rag_score = candidates[0]
        direct_score = _score_match(column, best_field.name)
        confidence = round(max(rag_score, direct_score), 3)
        if confidence >= 0.62:
            column_map[best_field.name] = column
            evidence.append(
                MappingEvidence(
                    canonical_field=best_field.name,
                    source_column=column,
                    confidence=confidence,
                    strategy="retrieval+string_similarity",
                    rationale=f"Matched '{column}' to '{best_field.name}' via synonym retrieval.",
                )
            )
    return MappingResult(column_map=column_map, evidence=evidence)
