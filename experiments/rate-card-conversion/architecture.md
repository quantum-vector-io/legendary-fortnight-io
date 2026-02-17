# Architecture

## Context
Samsung SDS receives diverse carrier rate cards with non-standard schemas. Manual onboarding causes delays and errors.

## Target
Build a conversion service that transforms rate cards into a canonical schema with high trust and auditability.

## Components

- **FastAPI API Layer**
  - Upload endpoint and health endpoint.
  - Returns canonical output + mapping evidence.

- **Extraction Layer**
  - CSV: `pandas.read_csv`
  - Excel: `pandas.read_excel`
  - PDF: `pdfplumber` table extraction (optional dependency)

- **Semantic Mapping Layer (Deterministic RAG-style)**
  - Canonical field definitions + synonyms knowledge base.
  - Retriever returns best field candidates for each input column.
  - Similarity scoring computes confidence and mapping evidence.

- **Validation Layer**
  - Required fields enforced.
  - Numeric/date/range checks.
  - Logical date ordering checks.
  - Rejection pipeline for unsafe records.

- **Canonical Data Contract**
  - `CanonicalRateCardRow` Pydantic model.
  - Explicit types for rates, dates, percentages, and transit days.

## Data flow

1. User uploads file.
2. Extractor parses tabular rows.
3. Mapper builds source-to-canonical mapping with confidence.
4. Transformer normalizes values.
5. Validator enforces quality rules.
6. API returns valid rows + rejected count + warnings + mapping evidence.

## Enterprise deployment recommendation

- API service behind gateway + authn/authz.
- Async worker for large documents.
- Object store for raw files and converted payload.
- Audit DB for evidence and decisions.
- Monitoring: reject-rate, low-confidence-rate, processing SLA.
