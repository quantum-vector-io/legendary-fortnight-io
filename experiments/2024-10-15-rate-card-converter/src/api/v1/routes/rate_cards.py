"""Route handlers for rate card retrieval endpoints.

GET /v1/rate-cards/{rate_card_id}
    Returns the complete standardized rate card including all rate entries
    and surcharges. Only available once the corresponding job reaches
    COMPLETED status.

GET /v1/rate-cards/
    Returns a paginated list of all stored rate cards.
"""

from __future__ import annotations

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel

from src.api.dependencies import get_rate_card_use_case
from src.application.use_cases.get_rate_card import GetRateCardUseCase
from src.domain.exceptions import RateCardNotFoundError

logger = logging.getLogger(__name__)

router = APIRouter()


class RateEntrySchema(BaseModel):
    """Serialized representation of a single rate line item."""

    origin: str
    destination: str
    service_level: str
    weight_min_kg: float
    weight_max_kg: float
    rate_per_kg: float
    currency: str
    min_charge: Optional[float] = None
    fuel_surcharge_pct: Optional[float] = None
    effective_from: Optional[str] = None
    effective_to: Optional[str] = None


class SurchargeSchema(BaseModel):
    """Serialized representation of an additional surcharge."""

    name: str
    percentage: Optional[float] = None
    flat_amount: Optional[float] = None
    currency: Optional[str] = None
    conditions: Optional[str] = None


class RateCardResponseSchema(BaseModel):
    """Full rate card response including all extracted rate entries and surcharges.

    Attributes:
        id: UUID of the rate card.
        job_id: UUID of the processing job that produced this rate card.
        carrier_name: Name of the freight carrier.
        carrier_code: Short carrier identifier, if available.
        format_version: Schema version string.
        source_format: Original document format ('pdf' or 'excel').
        source_filename: Original uploaded filename.
        rates: All extracted rate line items.
        surcharges: All extracted surcharges.
        metadata: Unstructured metadata from the document.
        created_at: ISO 8601 timestamp of rate card creation.
        updated_at: ISO 8601 timestamp of most recent update.
    """

    id: str
    job_id: str
    carrier_name: str
    carrier_code: Optional[str] = None
    format_version: str
    source_format: str
    source_filename: str
    rates: list[RateEntrySchema]
    surcharges: list[SurchargeSchema]
    metadata: dict
    created_at: str
    updated_at: str


class RateCardSummarySchema(BaseModel):
    """Abbreviated rate card representation for list responses."""

    id: str
    job_id: str
    carrier_name: str
    source_format: str
    source_filename: str
    rate_count: int
    created_at: str


@router.get(
    "/",
    response_model=list[RateCardSummarySchema],
    summary="List all stored rate cards.",
)
async def list_rate_cards(
    limit: int = Query(default=50, ge=1, le=200, description="Maximum number of results."),
    offset: int = Query(default=0, ge=0, description="Number of records to skip."),
    use_case: GetRateCardUseCase = Depends(get_rate_card_use_case),
) -> list[RateCardSummarySchema]:
    """Return a paginated list of all stored rate cards.

    Args:
        limit: Maximum number of results to return.
        offset: Number of records to skip for pagination.
        use_case: Injected retrieval use case.

    Returns:
        A list of RateCardSummarySchema objects.
    """
    rate_cards = await use_case.list_rate_cards(limit=limit, offset=offset)
    return [
        RateCardSummarySchema(
            id=rc.id,
            job_id=rc.job_id,
            carrier_name=rc.standardized_data.carrier_name,
            source_format=rc.standardized_data.source_format,
            source_filename=rc.standardized_data.source_filename,
            rate_count=len(rc.standardized_data.rates),
            created_at=rc.created_at.isoformat(),
        )
        for rc in rate_cards
    ]


@router.get(
    "/{rate_card_id}",
    response_model=RateCardResponseSchema,
    summary="Retrieve a fully processed rate card by ID.",
)
async def get_rate_card(
    rate_card_id: str,
    use_case: GetRateCardUseCase = Depends(get_rate_card_use_case),
) -> RateCardResponseSchema:
    """Return a complete rate card with all rate entries and surcharges.

    Args:
        rate_card_id: UUID string identifying the rate card.
        use_case: Injected retrieval use case.

    Returns:
        A RateCardResponseSchema with the full standardized data.

    Raises:
        HTTPException 404: If no rate card with the given ID exists.
    """
    try:
        rate_card = await use_case.get_rate_card(rate_card_id)
    except RateCardNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=exc.message,
        )

    data = rate_card.standardized_data
    return RateCardResponseSchema(
        id=rate_card.id,
        job_id=rate_card.job_id,
        carrier_name=data.carrier_name,
        carrier_code=data.carrier_code,
        format_version=data.format_version,
        source_format=data.source_format,
        source_filename=data.source_filename,
        rates=[RateEntrySchema(**entry.model_dump()) for entry in data.rates],
        surcharges=[SurchargeSchema(**s.model_dump()) for s in data.surcharges],
        metadata=data.metadata,
        created_at=rate_card.created_at.isoformat(),
        updated_at=rate_card.updated_at.isoformat(),
    )
