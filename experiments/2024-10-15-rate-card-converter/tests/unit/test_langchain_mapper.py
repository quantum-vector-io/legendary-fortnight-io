"""Unit tests for the LLM mapper components.

All tests use MockLLMMapper — no real OpenAI API calls are made. These tests
verify:
- MockLLMMapper returns a valid StandardizedRateCard.
- call_count is incremented on each invocation.
- last_call_args captures the invocation arguments.
- Custom response override works correctly.
- The default mock response populates required schema fields.

Tests for LangChainLLMMapper (with real API) are excluded from the automated
suite to prevent cost accumulation. They are documented below as manual tests.
"""

from __future__ import annotations

import pytest

from src.domain.entities.rate_card import RateEntry, StandardizedRateCard, Surcharge
from src.domain.ports.document_extractor import ExtractedTable
from src.infrastructure.mappers.mock_mapper import MockLLMMapper


@pytest.fixture
def sample_tables() -> list[ExtractedTable]:
    """Return a sample list of ExtractedTable instances for mapper input."""
    return [
        ExtractedTable(
            headers=["Origin", "Destination", "Rate", "Currency"],
            rows=[
                ["US", "EU", "10.50", "USD"],
                ["US", "APAC", "7.80", "USD"],
            ],
            sheet_name="Rates",
        )
    ]


async def test_mock_mapper_returns_standardized_rate_card(
    mock_llm_mapper: MockLLMMapper, sample_tables: list[ExtractedTable]
) -> None:
    """MockLLMMapper must return a StandardizedRateCard on invocation."""
    result = await mock_llm_mapper.map_to_standard_schema(
        extracted_tables=sample_tables,
        source_filename="test.xlsx",
        source_format="excel",
    )
    assert isinstance(result, StandardizedRateCard)


async def test_mock_mapper_populates_carrier_name(
    mock_llm_mapper: MockLLMMapper, sample_tables: list[ExtractedTable]
) -> None:
    """The default mock response must have a non-empty carrier_name."""
    result = await mock_llm_mapper.map_to_standard_schema(
        extracted_tables=sample_tables,
        source_filename="test.xlsx",
        source_format="excel",
    )
    assert result.carrier_name
    assert isinstance(result.carrier_name, str)


async def test_mock_mapper_populates_rates_list(
    mock_llm_mapper: MockLLMMapper, sample_tables: list[ExtractedTable]
) -> None:
    """The default mock response must contain at least one RateEntry."""
    result = await mock_llm_mapper.map_to_standard_schema(
        extracted_tables=sample_tables,
        source_filename="test.xlsx",
        source_format="excel",
    )
    assert len(result.rates) >= 1
    for entry in result.rates:
        assert isinstance(entry, RateEntry)


async def test_mock_mapper_increments_call_count(
    mock_llm_mapper: MockLLMMapper, sample_tables: list[ExtractedTable]
) -> None:
    """call_count must be incremented once for each invocation."""
    assert mock_llm_mapper.call_count == 0

    await mock_llm_mapper.map_to_standard_schema(sample_tables, "test.xlsx", "excel")
    assert mock_llm_mapper.call_count == 1

    await mock_llm_mapper.map_to_standard_schema(sample_tables, "test.xlsx", "excel")
    assert mock_llm_mapper.call_count == 2


async def test_mock_mapper_records_last_call_args(
    mock_llm_mapper: MockLLMMapper, sample_tables: list[ExtractedTable]
) -> None:
    """last_call_args must capture the arguments from the most recent invocation."""
    await mock_llm_mapper.map_to_standard_schema(
        extracted_tables=sample_tables,
        source_filename="carrier.xlsx",
        source_format="excel",
    )
    assert mock_llm_mapper.last_call_args is not None
    assert mock_llm_mapper.last_call_args["source_filename"] == "carrier.xlsx"
    assert mock_llm_mapper.last_call_args["source_format"] == "excel"


async def test_mock_mapper_uses_custom_response() -> None:
    """MockLLMMapper initialized with a custom response must return it on every call."""
    custom_card = StandardizedRateCard(
        carrier_name="Custom Carrier",
        source_format="pdf",
        source_filename="custom.pdf",
        rates=[
            RateEntry(
                origin="A",
                destination="B",
                service_level="express",
                weight_min_kg=1.0,
                weight_max_kg=5.0,
                rate_per_kg=20.0,
                currency="EUR",
            )
        ],
    )
    mapper = MockLLMMapper(response=custom_card)
    result = await mapper.map_to_standard_schema([], "any.pdf", "pdf")
    assert result.carrier_name == "Custom Carrier"
    assert result.rates[0].currency == "EUR"


async def test_mock_mapper_sets_source_filename_from_args(
    mock_llm_mapper: MockLLMMapper, sample_tables: list[ExtractedTable]
) -> None:
    """The response source_filename should match the argument passed in."""
    result = await mock_llm_mapper.map_to_standard_schema(
        extracted_tables=sample_tables,
        source_filename="my_carrier.xlsx",
        source_format="excel",
    )
    assert result.source_filename == "my_carrier.xlsx"


# ---------------------------------------------------------------------------
# Manual integration test (NOT run in automated suite — requires real API key)
# ---------------------------------------------------------------------------
# To manually test LangChainLLMMapper with real OpenAI API:
#
#   from src.config.settings import Settings
#   from src.infrastructure.mappers.langchain_mapper import LangChainLLMMapper
#   from src.domain.ports.document_extractor import ExtractedTable
#   import asyncio
#
#   settings = Settings()  # reads from .env
#   mapper = LangChainLLMMapper(settings)
#   tables = [ExtractedTable(
#       headers=["From", "To", "Service", "Rate USD/kg"],
#       rows=[["US", "EU", "express", "12.5"]],
#       sheet_name="Rates"
#   )]
#   result = asyncio.run(mapper.map_to_standard_schema(tables, "test.xlsx", "excel"))
#   print(result.model_dump_json(indent=2))
