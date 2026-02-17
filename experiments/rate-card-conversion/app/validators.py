from datetime import datetime
import pandas as pd


REQUIRED_CANONICAL_FIELDS = ("lane_origin", "lane_destination", "rate_value")


def to_date_or_none(value):
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    if isinstance(value, str) and not value.strip():
        return None
    return pd.to_datetime(value, errors="coerce").date()


def validate_required_columns(column_map: dict[str, str]) -> list[str]:
    missing = [field for field in REQUIRED_CANONICAL_FIELDS if field not in column_map]
    return [f"Missing required canonical field mapping: {field}" for field in missing]


def normalize_value(v):
    if isinstance(v, str):
        return v.strip()
    return v


def enforce_row_quality(row: dict) -> tuple[bool, str | None]:
    if row.get("rate_value") is None:
        return False, "Missing rate_value"
    try:
        value = float(row["rate_value"])
    except (TypeError, ValueError):
        return False, "rate_value is not numeric"
    if value < 0:
        return False, "rate_value must be non-negative"

    for date_field in ("effective_from", "effective_to"):
        if row.get(date_field) is not None and not hasattr(row[date_field], "year"):
            return False, f"{date_field} is invalid"

    if row.get("effective_from") and row.get("effective_to"):
        if row["effective_from"] > row["effective_to"]:
            return False, "effective_from is after effective_to"

    return True, None
