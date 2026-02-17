import pandas as pd

from app.config import settings
from app.mapping import build_column_mapping
from app.schemas import CanonicalRateCardRow, ConversionResponse
from app.validators import enforce_row_quality, to_date_or_none, validate_required_columns


OPTIONAL_FLOAT_FIELDS = ("surcharge_fuel_pct", "min_charge")
OPTIONAL_INT_FIELDS = ("transit_days",)


def _safe_float(value):
    try:
        if value is None or (isinstance(value, float) and pd.isna(value)):
            return None
        if isinstance(value, str):
            value = value.replace("%", "").replace(",", "").strip()
            if not value:
                return None
        return float(value)
    except (ValueError, TypeError):
        return None


def _safe_int(value):
    number = _safe_float(value)
    return int(number) if number is not None else None


def convert_dataframe(df: pd.DataFrame) -> ConversionResponse:
    mapping_result = build_column_mapping(df)
    warnings = validate_required_columns(mapping_result.column_map)

    rows: list[CanonicalRateCardRow] = []
    rejected_rows = 0

    for _, src_row in df.iterrows():
        transformed: dict = {}
        for canonical_field, source_column in mapping_result.column_map.items():
            transformed[canonical_field] = src_row.get(source_column)

        for field in OPTIONAL_FLOAT_FIELDS:
            transformed[field] = _safe_float(transformed.get(field))
        for field in OPTIONAL_INT_FIELDS:
            transformed[field] = _safe_int(transformed.get(field))

        transformed["rate_value"] = _safe_float(transformed.get("rate_value"))
        transformed["effective_from"] = to_date_or_none(transformed.get("effective_from"))
        transformed["effective_to"] = to_date_or_none(transformed.get("effective_to"))
        transformed["currency"] = transformed.get("currency") or "USD"

        ok, reason = enforce_row_quality(transformed)
        if not ok:
            rejected_rows += 1
            warnings.append(f"Row rejected: {reason}")
            continue

        rows.append(CanonicalRateCardRow.model_validate(transformed))

    if mapping_result.evidence:
        for ev in mapping_result.evidence:
            if ev.confidence < settings.confidence_threshold:
                warnings.append(
                    f"Low-confidence mapping: {ev.source_column} -> {ev.canonical_field} ({ev.confidence})"
                )

    return ConversionResponse(
        rows=rows,
        mapping_evidence=mapping_result.evidence,
        rejected_rows=rejected_rows,
        warnings=warnings,
    )
