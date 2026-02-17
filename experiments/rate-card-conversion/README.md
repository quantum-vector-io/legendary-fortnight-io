# Rate Card Conversion (Samsung SDS / Ciklum style solution)

Production-oriented FastAPI service that converts heterogeneous carrier rate cards (Excel/CSV/PDF) into a canonical logistics schema with strong anti-hallucination controls.

## Why this design

This project prioritizes **deterministic safety over creative generation**:

- LLM behavior is optional and bounded (can be turned off by default).
- Mapping uses retrieval + deterministic similarity scoring.
- Every mapping provides evidence and confidence.
- Output rows are validated by rule guards to reject unsafe records.
- Required business fields are enforced (`lane_origin`, `lane_destination`, `rate_value`).

## Architecture (high level)

1. **Ingestion API** (`POST /v1/convert-rate-card`)
2. **Extractor layer** for CSV/XLSX/PDF table parsing
3. **Semantic mapping (RAG-like)**
   - Canonical field knowledge base + synonym retrieval
   - String similarity scoring
4. **Quality gates**
   - Required field checks
   - Type/date/range/business validation
5. **Canonical output**
   - Standardized JSON rows + mapping evidence + warnings

For full details see [architecture.md](./architecture.md) and [decision-log.md](./decision-log.md).

## Run locally

```bash
cd experiments/rate-card-conversion
python -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'
uvicorn app.main:app --reload
```

Open http://127.0.0.1:8000/docs.

## API example

```bash
curl -X POST 'http://127.0.0.1:8000/v1/convert-rate-card' \
  -F 'file=@data/sample_rate_card.csv'
```


## Educational MCP server (OpenAI/Claude/Gemini-ready)

For interview prep and architecture study, this project now includes a simple MCP server with:

- Provider abstraction for OpenAI, Claude, Gemini (+ deterministic fallback).
- Hybrid agent orchestration (deterministic mapping + safe self-improvement loop).
- MCP tools to run conversion and inspect agent decisions.

See [`mcp_server/README.md`](./mcp_server/README.md) for architecture diagrams, data flow, and study notes.

## Testing

```bash
pytest
```

## Scale & quality strategy

- Add async job queue for large files (Celery/RQ + Redis).
- Persist lineage: source file hash, mapping evidence, rejected-row reasons.
- Introduce human-in-the-loop review for low-confidence mappings.
- Add model risk controls: prompt/version registry, golden test set, drift checks.
- Add domain controls: contract rate ranges, lane whitelist, currency conversion policy.

## Hallucination prevention principles

- Never generate a value if no source cell exists.
- Never accept a mapping without confidence evidence.
- Reject rows that fail numeric/date invariants.
- Default to warning/reject, not guess/fill.
