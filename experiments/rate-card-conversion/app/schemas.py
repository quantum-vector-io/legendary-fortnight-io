from datetime import date
from pydantic import BaseModel, Field


class CanonicalRateCardRow(BaseModel):
    carrier_name: str | None = None
    lane_origin: str
    lane_destination: str
    equipment_type: str | None = None
    service_level: str | None = None
    currency: str = "USD"
    rate_value: float = Field(ge=0)
    surcharge_fuel_pct: float | None = Field(default=None, ge=0, le=100)
    min_charge: float | None = Field(default=None, ge=0)
    transit_days: int | None = Field(default=None, ge=0)
    effective_from: date | None = None
    effective_to: date | None = None
    notes: str | None = None


class MappingEvidence(BaseModel):
    canonical_field: str
    source_column: str
    confidence: float = Field(ge=0, le=1)
    strategy: str
    rationale: str


class ConversionResponse(BaseModel):
    rows: list[CanonicalRateCardRow]
    mapping_evidence: list[MappingEvidence]
    rejected_rows: int = 0
    warnings: list[str] = []
