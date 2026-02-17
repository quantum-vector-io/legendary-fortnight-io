# Architecture: Rate Card Converter

## Hexagonal Architecture Overview

The system is organized in concentric rings. Each ring depends only on rings
closer to the center. The domain layer has zero external dependencies.

Arrows point **inward only**: Infrastructure imports from Application and
Domain. Application imports from Domain. Domain imports nothing external.

```mermaid
flowchart TD
    subgraph INFRA["Infrastructure / API (outermost ring)"]
        direction TB
        ROUTES["FastAPI routes\n(documents, rate_cards)"]
        PDF["PDFExtractor\n(pdfplumber)"]
        XLSX["XLSXExtractor\n(openpyxl)"]
        AZURE["AzureDocumentExtractor\n(httpx REST)"]
        LC["LangChainLLMMapper\n(gpt-4o-mini)"]
        MOCK["MockLLMMapper\n(tests only)"]
        SQLREPO["SQLAlchemy repositories\n(SQLite / PostgreSQL)"]
        DOCKER["Uvicorn / Docker"]

        subgraph APP["Application (use cases)"]
            UPLOAD["UploadDocumentUseCase"]
            PROCESS["ProcessDocumentUseCase"]
            GETRC["GetRateCardUseCase"]

            subgraph DOMAIN["Domain (no external dependencies)"]
                direction LR
                subgraph ENTITIES["Entities"]
                    E1["RateEntry"]
                    E2["Surcharge"]
                    E3["StandardizedRateCard"]
                    E4["RateCard"]
                    E5["ProcessingJob"]
                end
                subgraph PORTS["Ports (ABCs)"]
                    P1["DocumentExtractorPort"]
                    P2["LLMMapperPort"]
                    P3["RateCardRepositoryPort"]
                    P4["JobRepositoryPort"]
                end
                subgraph EXCEPTIONS["Exceptions"]
                    X1["DocumentExtractionError"]
                    X2["LLMMappingError"]
                    X3["RateCardNotFoundError"]
                    X4["JobNotFoundError"]
                end
            end
        end
    end

    PDF --> P1
    XLSX --> P1
    AZURE --> P1
    LC --> P2
    MOCK --> P2
    SQLREPO --> P3
    SQLREPO --> P4
    ROUTES --> UPLOAD
    ROUTES --> PROCESS
    ROUTES --> GETRC
    UPLOAD --> P4
    PROCESS --> P1
    PROCESS --> P2
    PROCESS --> P3
    PROCESS --> P4
    GETRC --> P3
    GETRC --> P4
```

---

## Port Definitions and Adapters

| Port (ABC)             | Methods                         | Local Adapter                                             | Azure Adapter              |
|------------------------|---------------------------------|-----------------------------------------------------------|----------------------------|
| DocumentExtractorPort  | extract(bytes, filename)        | LocalDocumentExtractorDispatcher (routes to PDF / XLSX)   | AzureDocumentExtractor     |
| LLMMapperPort          | map_to_standard_schema(...)     | LangChainLLMMapper (gpt-4o-mini) / MockLLMMapper (tests)  | LangChainLLMMapper (same)  |
| RateCardRepositoryPort | save, get_by_id, list_all       | SQLiteRateCardRepository                                  | PostgresRateCardRepository |
| JobRepositoryPort      | save, get_by_id, update_status  | SQLiteJobRepository                                       | PostgresJobRepository      |

---

## Adapter Selection by Environment

The `src/config/container.py` module is the **only** place in the codebase where
`settings.environment` is read to select adapters. All other code depends only on
port abstractions.

```mermaid
flowchart LR
    ENV{ENVIRONMENT\nvariable}

    ENV -->|local| LOCAL_EXT["LocalDocumentExtractorDispatcher\n(PDFExtractor + XLSXExtractor)"]
    ENV -->|azure| AZURE_EXT["AzureDocumentExtractor\n(Document Intelligence REST)"]

    ENV -->|local| LOCAL_DB["SQLite\n(aiosqlite)"]
    ENV -->|azure| AZURE_DB["PostgreSQL\n(asyncpg)"]

    ENV -->|local| LOCAL_TASK["FastAPI BackgroundTasks"]
    ENV -->|azure| AZURE_TASK["Celery + Redis\n(future)"]

    ENV -->|local| LOCAL_CACHE["InMemoryCache\n(per-process)"]
    ENV -->|azure| AZURE_CACHE["SQLiteCache\n(persistent)"]

    LOCAL_EXT --> P1["DocumentExtractorPort"]
    AZURE_EXT --> P1
    LOCAL_DB --> P3["RepositoryPorts"]
    AZURE_DB --> P3
```

| Component           | ENVIRONMENT=local                      | ENVIRONMENT=azure                      |
|---------------------|----------------------------------------|----------------------------------------|
| Document extraction | LocalDocumentExtractorDispatcher       | AzureDocumentExtractor                 |
| LLM mapping         | LangChainLLMMapper (gpt-4o-mini)       | LangChainLLMMapper (gpt-4o-mini)       |
| LLM caching         | InMemoryCache (per process)            | SQLiteCache (persistent)               |
| Database            | SQLite via aiosqlite                   | PostgreSQL via asyncpg                 |
| Task processing     | FastAPI BackgroundTasks                | Celery + Redis (future)                |
| Repositories        | SQLiteJobRepository                    | PostgresJobRepository                  |
|                     | SQLiteRateCardRepository               | PostgresRateCardRepository             |

---

## Dependency Injection Flow

```mermaid
flowchart TD
    START["FastAPI startup\ncreate_app()"]
    LIFE["lifespan() context manager\n- mkdir upload_dir\n- await init_db()"]
    REQ["HTTP request arrives at route handler"]

    DEP1["get_settings_dep()\n→ Settings singleton (lru_cache)"]
    DEP2["get_db_session()\n→ yields AsyncSession\n(commit/rollback on exit)"]
    DEP3["get_upload_use_case()\n→ UploadDocumentUseCase(job_repo, upload_dir)"]
    DEP4["get_process_use_case()\n→ ProcessDocumentUseCase(\n  extractor, mapper,\n  session_factory, upload_dir)\n  note: session_factory, not open session"]
    DEP5["get_rate_card_use_case()\n→ GetRateCardUseCase(rate_card_repo, job_repo)"]

    ROUTE["Route handler calls use_case.execute()"]
    UC["Use case coordinates domain entities\nthrough port ABCs only\n(no infrastructure imports)"]

    START --> LIFE --> REQ
    REQ --> DEP1
    REQ --> DEP2
    REQ --> DEP3
    REQ --> DEP4
    REQ --> DEP5
    DEP1 & DEP2 & DEP3 & DEP4 & DEP5 --> ROUTE --> UC
```

---

## Data Flow: Upload to Rate Card Retrieval

```mermaid
flowchart TD
    S1["Step 1 — HTTP Upload"]
    CLIENT["Client\nPOST /v1/documents/upload\n(multipart file)"]
    VALID["API validates:\n- size ≤ 25 MB\n- extension .pdf / .xlsx\n- magic bytes check"]
    UPLOAD_UC["UploadDocumentUseCase.execute()\n- determine file_format\n- ProcessingJob.create() → PENDING\n- write bytes to upload_dir/job_id/\n- job_repo.save()"]
    BG["BackgroundTasks.add_task(\n  ProcessDocumentUseCase.execute, job_id)"]
    RESP_202["202 Accepted\n{ id, status: 'pending' }"]

    S2["Step 2 — Background Processing\n(after HTTP response sent)"]
    SESSION["ProcessDocumentUseCase creates\nown AsyncSession from session_factory"]
    MARK_P["job.mark_processing() → SQL UPDATE"]
    READ["asyncio.to_thread: read file bytes"]
    EXTRACT["DocumentExtractorPort.extract()\nLOCAL: PDFExtractor / XLSXExtractor\nAZURE: AzureDocumentExtractor (polling)"]
    TABLES["list[ExtractedTable]"]
    LLM["LLMMapperPort.map_to_standard_schema()\nLangChainLLMMapper:\n- InMemoryCache check\n- ChatOpenAI.with_structured_output\n- ainvoke(prompt + table_text)"]
    RC_ENTITY["StandardizedRateCard (validated Pydantic)"]
    SAVE_RC["RateCard.create() → rate_card_repo.save()"]
    MARK_C["job.mark_completed(rate_card_id)\nSQL UPDATE status=completed"]
    COMMIT["session.commit()"]

    S3["Step 3 — Client Polling"]
    POLL["GET /v1/documents/{job_id}/status"]
    STATUS_RESP["200 { status: 'completed', rate_card_id }"]

    S4["Step 4 — Rate Card Retrieval"]
    GET_RC["GET /v1/rate-cards/{rate_card_id}"]
    RC_RESP["200 { carrier_name, rates, surcharges, ... }"]

    CLIENT --> VALID --> UPLOAD_UC --> BG --> RESP_202
    BG --> S2
    S2 --> SESSION --> MARK_P --> READ --> EXTRACT --> TABLES --> LLM --> RC_ENTITY --> SAVE_RC --> MARK_C --> COMMIT
    RESP_202 --> S3
    S3 --> POLL --> STATUS_RESP
    STATUS_RESP --> S4
    S4 --> GET_RC --> RC_RESP
```

---

## Testing Strategy

The test suite is designed to run with zero external service calls:

| Test Layer    | Dependencies Replaced                                          | Tests Verify                                              |
|---------------|----------------------------------------------------------------|-----------------------------------------------------------|
| Unit tests    | MockDocumentExtractor, MockLLMMapper, MockJobRepository,       | Extractor parsing, mapper invocation,                     |
|               | MockRateCardRepository, in-memory SQLite (db_session fixture)  | use case state machine logic                              |
| Integration   | All infrastructure via dependency_overrides in FastAPI,        | HTTP status codes, response schemas,                      |
|               | ImmediateProcessUseCase (synchronous test double)              | full upload → status → retrieval flow                     |

LangChainLLMMapper with a real OpenAI API is tested manually:
```bash
python samples/generate_samples.py
# then upload via curl or the /docs Swagger UI
```

---

## Extension Points

### Adding a New Document Extractor

1. Create `src/infrastructure/extractors/my_extractor.py` implementing `DocumentExtractorPort`.
2. Register in `src/config/container.py` `get_document_extractor()` under the appropriate condition.
3. No changes required in any use case or API code.

### Adding a New LLM Provider

1. Create `src/infrastructure/mappers/my_mapper.py` implementing `LLMMapperPort`.
2. Update `get_llm_mapper()` in `src/config/container.py`.
3. No application or API code changes required.

### Adding a New API Endpoint

1. Add route handler in the appropriate `src/api/v1/routes/*.py` file.
2. Add the corresponding use case method (or new use case class) in `src/application/`.
3. Use cases depend on ports — no infrastructure imports needed.
