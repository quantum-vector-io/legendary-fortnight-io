"""Rate card domain entities and value objects.

This module defines the canonical data schema for freight carrier rate cards.
Pydantic v2 models are used for schema validation and serialization. Field
constraints intentionally avoid ge/le/min_length validators because those
generate JSON Schema properties (minimum, maximum, minLength) that are
incompatible with OpenAI's structured output API.

The RateCard dataclass is the persistence aggregate root, wrapping a
StandardizedRateCard value object with identity (id) and audit timestamps.
The two are kept separate: StandardizedRateCard is produced by the LLM mapper
and validated by Pydantic; RateCard is what the repository stores and retrieves.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class RateEntry(BaseModel):
    """A single billable line item extracted from a freight carrier rate card.

    Weight ranges define the applicability window for the rate. All weights
    are normalized to kilograms and all rates to the per-kg unit by the LLM
    mapper regardless of the source document's original units.
    """

    model_config = ConfigDict(str_strip_whitespace=True)

    origin: str = Field(description="Origin zone, city, country, or region code.")
    destination: str = Field(description="Destination zone, city, country, or region code.")
    service_level: str = Field(
        description=(
            "Normalized service tier. Valid values: 'express', 'standard', 'economy'. "
            "The LLM maps carrier-specific terms (Priority Air -> express, Ground -> standard)."
        )
    )
    weight_min_kg: float = Field(description="Lower bound of the applicable weight range in kilograms.")
    weight_max_kg: float = Field(description="Upper bound of the applicable weight range in kilograms.")
    rate_per_kg: float = Field(description="Freight rate in the specified currency per kilogram.")
    currency: str = Field(description="ISO 4217 currency code, e.g. USD, EUR, KRW.")
    min_charge: Optional[float] = Field(
        default=None,
        description="Minimum billable amount in the specified currency, if applicable.",
    )
    fuel_surcharge_pct: Optional[float] = Field(
        default=None,
        description="Fuel surcharge as a percentage of the base rate, if specified per entry.",
    )
    effective_from: Optional[str] = Field(
        default=None,
        description="Date from which this rate is effective, in ISO 8601 format (YYYY-MM-DD).",
    )
    effective_to: Optional[str] = Field(
        default=None,
        description="Date after which this rate expires, in ISO 8601 format (YYYY-MM-DD).",
    )


class Surcharge(BaseModel):
    """An additional charge applied on top of base freight rates.

    Surcharges may be percentage-based, flat-amount, or both. Common examples
    include fuel surcharges, peak season surcharges, and residential delivery fees.
    """

    model_config = ConfigDict(str_strip_whitespace=True)

    name: str = Field(description="Surcharge name, e.g. 'Fuel Surcharge', 'Peak Season Fee'.")
    percentage: Optional[float] = Field(
        default=None,
        description="Surcharge expressed as a percentage of the base rate.",
    )
    flat_amount: Optional[float] = Field(
        default=None,
        description="Fixed surcharge amount in the associated currency.",
    )
    currency: Optional[str] = Field(
        default=None,
        description="ISO 4217 currency code for flat_amount charges.",
    )
    conditions: Optional[str] = Field(
        default=None,
        description="Conditions or scope under which this surcharge applies.",
    )


class StandardizedRateCard(BaseModel):
    """Canonical representation of a freight carrier rate card.

    This is the primary output schema produced by the LLM semantic mapper.
    It is also the schema used for the OpenAI structured output call, so it
    must remain compatible with OpenAI's JSON Schema constraints (no numeric
    range validators, no string length validators).
    """

    model_config = ConfigDict(str_strip_whitespace=True)

    carrier_name: str = Field(description="Name of the freight carrier or logistics provider.")
    carrier_code: Optional[str] = Field(
        default=None,
        description="Short carrier identifier code, e.g. 'FEDEX', 'DHL', 'UPS'.",
    )
    format_version: str = Field(
        default="1.0",
        description="Schema version of this standardized rate card.",
    )
    source_format: str = Field(
        description="Original document format: 'excel' or 'pdf'.",
    )
    source_filename: str = Field(
        description="Original filename of the uploaded document.",
    )
    rates: list[RateEntry] = Field(
        description="All individual rate line items extracted from the document.",
    )
    surcharges: list[Surcharge] = Field(
        default_factory=list,
        description="Additional surcharges found in the document.",
    )
    metadata: dict = Field(
        default_factory=dict,
        description="Unstructured metadata extracted from the document (e.g. validity notes).",
    )


@dataclass
class RateCard:
    """Persistence aggregate root for a standardized rate card.

    Wraps StandardizedRateCard with a stable identity (UUID) and audit
    timestamps. The ORM layer maps this dataclass to the rate_cards table,
    storing standardized_data as a JSON column to avoid premature normalization.

    Attributes:
        id: Unique identifier (UUID4 string) assigned at creation time.
        job_id: ID of the ProcessingJob that produced this rate card.
        standardized_data: The validated canonical rate card value object.
        created_at: Timestamp when this rate card was first persisted.
        updated_at: Timestamp of the most recent update.
    """

    id: str
    job_id: str
    standardized_data: StandardizedRateCard
    created_at: datetime
    updated_at: datetime

    @classmethod
    def create(cls, job_id: str, standardized_data: StandardizedRateCard) -> "RateCard":
        """Create a new RateCard aggregate with a generated identity.

        Args:
            job_id: ID of the processing job that produced this rate card.
            standardized_data: The validated StandardizedRateCard value object.

        Returns:
            A new RateCard instance with a generated UUID and current timestamps.
        """
        now = datetime.utcnow()
        return cls(
            id=str(uuid.uuid4()),
            job_id=job_id,
            standardized_data=standardized_data,
            created_at=now,
            updated_at=now,
        )
