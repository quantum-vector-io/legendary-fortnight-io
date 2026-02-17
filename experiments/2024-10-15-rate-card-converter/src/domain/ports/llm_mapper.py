"""Abstract port defining the contract for LLM-based semantic field mapping.

The LLMMapperPort abstracts the process of converting raw extracted tables
(with carrier-specific column headers and units) into a StandardizedRateCard
using LLM semantic understanding. The concrete implementation uses LangChain
with OpenAI GPT-4o-mini; the mock implementation returns deterministic data
for tests.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from src.domain.entities.rate_card import StandardizedRateCard
from src.domain.ports.document_extractor import ExtractedTable


class LLMMapperPort(ABC):
    """Abstract port for LLM-based semantic mapping of extracted document data.

    Implementations receive raw tabular content from a document extractor and
    produce a fully validated StandardizedRateCard by semantically mapping
    arbitrary column headers to canonical schema fields, normalizing units,
    inferring currency codes, and extracting carrier metadata.
    """

    @abstractmethod
    async def map_to_standard_schema(
        self,
        extracted_tables: list[ExtractedTable],
        source_filename: str,
        source_format: str,
    ) -> StandardizedRateCard:
        """Map extracted document tables to the standardized rate card schema.

        Args:
            extracted_tables: List of raw tables from the document extractor.
                              May include tables with raw_text for unstructured content.
            source_filename: Original filename of the document, used to infer
                             carrier name when not explicitly present in the data.
            source_format: Document format: 'pdf' or 'excel'.

        Returns:
            A validated StandardizedRateCard containing all rate entries and
            surcharges found in the document, with units normalized to kg and
            currency codes in ISO 4217 format.

        Raises:
            LLMMappingError: If the LLM fails to respond, returns invalid output,
                             or if structured output parsing fails.
        """
