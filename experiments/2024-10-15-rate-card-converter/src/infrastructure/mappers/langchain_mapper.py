"""LangChain + OpenAI GPT-4o-mini semantic mapper for production use.

This adapter implements LLMMapperPort using LangChain's structured output
feature (with_structured_output) to instruct OpenAI's GPT-4o-mini model to
return JSON that matches the StandardizedRateCard Pydantic schema exactly.

Cost controls applied:
- Default model: gpt-4o-mini (~15x cheaper than gpt-4o).
- temperature=0 for deterministic extraction output.
- max_tokens=2048 cap on response tokens.
- InMemoryCache: identical (prompt, model) pairs return cached responses.
- Table text is truncated to 6000 characters to stay within a predictable
  token budget (~1500 input tokens for table content).

LangChain version note: This file uses langchain 0.3.0 import paths.
All model imports come from langchain-openai, not from langchain.chat_models
(which was removed in 0.3.0).

OpenAI structured output note: StandardizedRateCard must not use Pydantic
field validators that generate JSON Schema constraints (ge, le, min_length,
max_length). These are rejected by OpenAI's structured output API.
"""

from __future__ import annotations

import logging
from typing import Any

from langchain.globals import set_llm_cache
from langchain_community.cache import InMemoryCache
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from src.config.settings import Settings
from src.domain.entities.rate_card import StandardizedRateCard
from src.domain.exceptions import LLMMappingError
from src.domain.ports.document_extractor import ExtractedTable
from src.domain.ports.llm_mapper import LLMMapperPort

logger = logging.getLogger(__name__)

# Maximum characters of table text to include in the LLM prompt.
# Keeps input token count predictable and within gpt-4o-mini's context window.
_MAX_TABLE_TEXT_CHARS = 6000

_SYSTEM_PROMPT = """You are a logistics data extraction specialist. You receive raw tabular \
data extracted from freight carrier rate cards and map it to a standardized schema.

Extraction rules:
- carrier_name: Infer from the filename or table content. Use "Unknown Carrier" if not determinable.
- service_level: Normalize to exactly one of: express, standard, economy. \
Map priority/air/overnight -> express, ground/road/standard -> standard, economy/budget -> economy.
- weight_min_kg / weight_max_kg: Always convert to kilograms. If the source uses pounds, \
multiply by 0.453592. If the source uses grams, divide by 1000.
- rate_per_kg: Always output as a float per kilogram. If rate is per pound, divide by 0.453592.
- currency: Output ISO 4217 codes (USD, EUR, KRW, GBP, CNY, etc.).
- effective_from / effective_to: Output as ISO 8601 date strings (YYYY-MM-DD) or null.
- surcharges: Extract all surcharges found (fuel, peak season, residential, dangerous goods, etc.).
- If a required field cannot be determined from the document, use null for Optional fields.
- Do not invent data. If a rate entry is ambiguous, include it with best-effort values and \
add a note in the entry's related surcharge or metadata.
- Extract ALL rate line items found. Do not summarize or omit rows."""

_HUMAN_PROMPT = """Source filename: {source_filename}
Source format: {source_format}

Extracted document content:
{table_text}

Map this carrier rate card data to the StandardizedRateCard schema."""


class LangChainLLMMapper(LLMMapperPort):
    """Semantic rate card mapper using LangChain structured output with GPT-4o-mini.

    Uses LangChain's with_structured_output() to bind the LLM to the
    StandardizedRateCard Pydantic schema. OpenAI's function calling mechanism
    guarantees that the response conforms to the schema or raises an error.

    InMemoryCache is registered globally so that repeated identical prompts
    (same table text, same source) return cached results without additional
    API calls. This is particularly useful during development and testing.

    Args:
        settings: Application settings providing OpenAI credentials and model config.
    """

    def __init__(self, settings: Settings) -> None:
        set_llm_cache(InMemoryCache())

        self._llm = ChatOpenAI(
            model=settings.openai_model,
            temperature=settings.openai_temperature,
            max_tokens=settings.openai_max_tokens,
            api_key=settings.openai_api_key,
        )
        # Bind the LLM to produce structured output matching StandardizedRateCard.
        # method="function_calling" uses OpenAI function calling, which is more
        # reliably supported across gpt-4o-mini versions than json_schema mode.
        self._structured_llm = self._llm.with_structured_output(
            StandardizedRateCard,
            method="function_calling",
        )
        self._prompt = ChatPromptTemplate.from_messages([
            ("system", _SYSTEM_PROMPT),
            ("human", _HUMAN_PROMPT),
        ])
        self._chain = self._prompt | self._structured_llm

    async def map_to_standard_schema(
        self,
        extracted_tables: list[ExtractedTable],
        source_filename: str,
        source_format: str,
    ) -> StandardizedRateCard:
        """Map extracted document tables to the StandardizedRateCard schema via LLM.

        Args:
            extracted_tables: Raw tables from the document extractor.
            source_filename: Used to populate the schema's source_filename field
                             and to help the LLM infer the carrier name.
            source_format: Either 'pdf' or 'excel'.

        Returns:
            A validated StandardizedRateCard populated by the LLM.

        Raises:
            LLMMappingError: If the LLM invocation fails or returns invalid output.
        """
        table_text = self._serialize_tables(extracted_tables)
        logger.info(
            "Invoking LLM mapper for '%s' (%d chars of table text).",
            source_filename,
            len(table_text),
        )
        return await self._invoke_llm(table_text, source_filename, source_format)

    def _serialize_tables(self, extracted_tables: list[ExtractedTable]) -> str:
        """Convert extracted tables into a text representation for the LLM prompt.

        Tables with structured headers are formatted as pipe-delimited Markdown.
        Tables with only raw_text are included as-is. The combined output is
        truncated to _MAX_TABLE_TEXT_CHARS to control token consumption.

        Args:
            extracted_tables: List of tables from the document extractor.

        Returns:
            A single string containing all table content, truncated if necessary.
        """
        parts: list[str] = []
        for table in extracted_tables:
            if table.headers:
                parts.append(self._format_table_markdown(table))
            elif table.raw_text:
                label = f"[{table.sheet_name or 'page'}]"
                parts.append(f"{label}\n{table.raw_text}")

        combined = "\n\n".join(parts)
        if len(combined) > _MAX_TABLE_TEXT_CHARS:
            combined = combined[:_MAX_TABLE_TEXT_CHARS]
            combined += f"\n\n[Truncated at {_MAX_TABLE_TEXT_CHARS} characters. Extract from the above only.]"

        return combined or "No structured content found in document."

    def _format_table_markdown(self, table: ExtractedTable) -> str:
        """Format an ExtractedTable as a Markdown table string.

        Args:
            table: The ExtractedTable to format.

        Returns:
            A Markdown-formatted table string with a sheet name label.
        """
        label = f"[{table.sheet_name or 'table'}]"
        header_row = " | ".join(table.headers)
        separator = " | ".join("---" for _ in table.headers)
        data_rows = [" | ".join(row) for row in table.rows]
        lines = [label, header_row, separator] + data_rows
        return "\n".join(lines)

    async def _invoke_llm(
        self,
        table_text: str,
        source_filename: str,
        source_format: str,
    ) -> StandardizedRateCard:
        """Invoke the LangChain chain and validate the response.

        Args:
            table_text: Serialized table content for the prompt.
            source_filename: Document filename for the prompt.
            source_format: Document format string for the prompt.

        Returns:
            The validated StandardizedRateCard from the LLM.

        Raises:
            LLMMappingError: If the chain raises an exception or returns None.
        """
        try:
            result: Any = await self._chain.ainvoke({
                "table_text": table_text,
                "source_filename": source_filename,
                "source_format": source_format,
            })
        except Exception as exc:
            raise LLMMappingError(
                f"LLM invocation failed for '{source_filename}': {exc}",
                detail={"filename": source_filename, "error": str(exc)},
            ) from exc

        if result is None:
            raise LLMMappingError(
                f"LLM returned None for '{source_filename}'. "
                "This may indicate a content policy rejection.",
                detail={"filename": source_filename},
            )

        if not isinstance(result, StandardizedRateCard):
            raise LLMMappingError(
                f"LLM returned unexpected type {type(result).__name__} for '{source_filename}'.",
                detail={"filename": source_filename, "result_type": type(result).__name__},
            )

        logger.info(
            "LLM mapping complete for '%s': %d rate entries, %d surcharges.",
            source_filename,
            len(result.rates),
            len(result.surcharges),
        )
        return result
