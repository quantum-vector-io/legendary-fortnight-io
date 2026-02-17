# Technical Decision Log

## 1) FastAPI over Flask
- **Decision**: Use FastAPI.
- **Reason**: Native request validation, OpenAPI docs, async support, and typed contracts reduce integration risk.

## 2) Deterministic-first mapping vs free-form LLM extraction
- **Decision**: Deterministic retrieval+similarity mapping is primary, LLM optional.
- **Reason**: Logistics pricing is safety-critical; deterministic behavior is easier to audit and less prone to hallucination.

## 3) Pydantic canonical schema
- **Decision**: Strong typed output model.
- **Reason**: Contract stability for downstream systems and predictable validation failure modes.

## 4) Reject-on-uncertainty policy
- **Decision**: Reject rows that violate invariants and emit warnings for low-confidence mappings.
- **Reason**: Better to defer uncertain data to review than inject bad rates into TMS/ERP.

## 5) RAG-like local knowledge base
- **Decision**: Use canonical field definitions and synonyms as retrieval corpus.
- **Reason**: Reduces model/token dependency while preserving semantic matching behavior.

## 6) Extensible strategy
- **Decision**: Keep extractor/mapping/validator modular.
- **Reason**: Enables future plug-ins (OCR, LangGraph human approval step, vector DB retrieval).
