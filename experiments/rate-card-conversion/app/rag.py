from dataclasses import dataclass
from difflib import SequenceMatcher


@dataclass(frozen=True)
class CanonicalFieldDef:
    name: str
    description: str
    synonyms: tuple[str, ...]


CANONICAL_FIELD_DEFS: tuple[CanonicalFieldDef, ...] = (
    CanonicalFieldDef("carrier_name", "Name of the carrier", ("carrier", "vendor", "provider")),
    CanonicalFieldDef("lane_origin", "Start location of shipment lane", ("origin", "from", "origin city", "pol")),
    CanonicalFieldDef("lane_destination", "End location of shipment lane", ("destination", "to", "dest", "pod")),
    CanonicalFieldDef("equipment_type", "Container or truck type", ("equipment", "container type", "truck type")),
    CanonicalFieldDef("service_level", "Service speed or priority", ("service", "priority", "mode")),
    CanonicalFieldDef("currency", "Rate currency", ("curr", "ccy")),
    CanonicalFieldDef("rate_value", "Main freight rate", ("rate", "base rate", "price", "amount")),
    CanonicalFieldDef("surcharge_fuel_pct", "Fuel surcharge percentage", ("fuel", "fsc", "fuel surcharge")),
    CanonicalFieldDef("min_charge", "Minimum charge", ("minimum", "min", "min charge")),
    CanonicalFieldDef("transit_days", "Transit duration in days", ("transit", "lead time", "days")),
    CanonicalFieldDef("effective_from", "Validity start date", ("effective from", "start date", "valid from")),
    CanonicalFieldDef("effective_to", "Validity end date", ("effective to", "end date", "valid to", "expiry")),
    CanonicalFieldDef("notes", "Any additional comment", ("remark", "comment", "notes")),
)


def retrieve_field_candidates(column_name: str, top_k: int = 3) -> list[tuple[CanonicalFieldDef, float]]:
    text = column_name.lower().strip()
    scored: list[tuple[CanonicalFieldDef, float]] = []
    for field in CANONICAL_FIELD_DEFS:
        best_synonym_score = max(
            SequenceMatcher(None, text, synonym).ratio() for synonym in (field.name, *field.synonyms)
        )
        scored.append((field, best_synonym_score))
    scored.sort(key=lambda x: x[1], reverse=True)
    return scored[:top_k]
