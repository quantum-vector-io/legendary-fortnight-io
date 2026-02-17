"""Deterministic LLM mapper mock for testing and local development without API calls.

MockLLMMapper implements LLMMapperPort and returns a fixed, pre-defined
StandardizedRateCard. It is used in the automated test suite to verify the
application and API layers without incurring OpenAI API costs or requiring
network connectivity.

The call_count attribute allows tests to assert that the mapper was invoked
the expected number of times. The last_call_args attribute captures the most
recent invocation arguments for assertion-based verification.
"""

from __future__ import annotations

from typing import Optional

from src.domain.entities.rate_card import RateEntry, StandardizedRateCard, Surcharge
from src.domain.ports.document_extractor import ExtractedTable
from src.domain.ports.llm_mapper import LLMMapperPort

# Fixed test data that produces a deterministic StandardizedRateCard response.
_DEFAULT_RATES = [
    RateEntry(
        origin="US-West",
        destination="Asia-Pacific",
        service_level="express",
        weight_min_kg=0.5,
        weight_max_kg=10.0,
        rate_per_kg=12.50,
        currency="USD",
        min_charge=15.0,
        fuel_surcharge_pct=5.5,
        effective_from="2024-10-01",
        effective_to="2024-12-31",
    ),
    RateEntry(
        origin="US-East",
        destination="Europe",
        service_level="standard",
        weight_min_kg=1.0,
        weight_max_kg=30.0,
        rate_per_kg=7.80,
        currency="USD",
        min_charge=10.0,
        fuel_surcharge_pct=5.5,
        effective_from="2024-10-01",
        effective_to="2024-12-31",
    ),
]

_DEFAULT_SURCHARGES = [
    Surcharge(
        name="Fuel Surcharge",
        percentage=5.5,
        currency="USD",
        conditions="Applied to all shipments.",
    )
]


class MockLLMMapper(LLMMapperPort):
    """Deterministic LLM mapper test double.

    Returns a fixed StandardizedRateCard without making any network calls.
    Supports an optional custom response for tests that need specific data.

    Attributes:
        call_count: Number of times map_to_standard_schema has been called.
        last_call_args: Keyword arguments from the most recent invocation.
    """

    def __init__(self, response: Optional[StandardizedRateCard] = None) -> None:
        """Initialize the mock mapper with an optional fixed response.

        Args:
            response: A custom StandardizedRateCard to return on every call.
                      If None, the default test fixture data is returned.
        """
        self._custom_response = response
        self.call_count: int = 0
        self.last_call_args: Optional[dict] = None

    async def map_to_standard_schema(
        self,
        extracted_tables: list[ExtractedTable],
        source_filename: str,
        source_format: str,
    ) -> StandardizedRateCard:
        """Return the configured mock StandardizedRateCard without an API call.

        Args:
            extracted_tables: Ignored by the mock; present to satisfy the port contract.
            source_filename: Used to populate source_filename in the response.
            source_format: Used to populate source_format in the response.

        Returns:
            A deterministic StandardizedRateCard with fixed test data, or the
            custom response provided at construction time.
        """
        self.call_count += 1
        self.last_call_args = {
            "extracted_tables": extracted_tables,
            "source_filename": source_filename,
            "source_format": source_format,
        }

        if self._custom_response is not None:
            return self._custom_response

        return StandardizedRateCard(
            carrier_name="Test Carrier",
            carrier_code="TST",
            source_format=source_format,
            source_filename=source_filename,
            rates=_DEFAULT_RATES,
            surcharges=_DEFAULT_SURCHARGES,
            metadata={"mock": "true"},
        )
