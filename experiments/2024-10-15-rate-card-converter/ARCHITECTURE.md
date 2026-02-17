# Architecture: Rate Card Converter

## Hexagonal Architecture Overview

The system is organized in concentric rings. Each ring depends only on rings
closer to the center. The domain layer has zero external dependencies.

```
+------------------------------------------------------------------+
|  Infrastructure / API (outermost ring)                           |
|  - FastAPI routes                  - pdfplumber extractor        |
|  - httpx Azure adapter             - openpyxl extractor          |
|  - LangChain + OpenAI mapper       - SQLAlchemy repositories     |
|  - Uvicorn / Docker                - MockLLMMapper (tests)       |
|                                                                  |
|  +------------------------------------------------------------+  |
|  |  Application (use cases)                                   |  |
|  |  - UploadDocumentUseCase                                   |  |
|  |  - ProcessDocumentUseCase                                  |  |
|  |  - GetRateCardUseCase                                      |  |
|  |                                                            |  |
|  |  +------------------------------------------------------+  |  |
|  |  |  Domain (innermost ring - no external dependencies)  |  |  |
|  |  |                                                      |  |  |
|  |  |  Entities:          Ports (ABCs):                   |  |  |
|  |  |  - RateEntry        - DocumentExtractorPort         |  |  |
|  |  |  - Surcharge        - LLMMapperPort                 |  |  |
|  |  |  - StandardizedRC   - RateCardRepositoryPort        |  |  |
|  |  |  - RateCard         - JobRepositoryPort             |  |  |
|  |  |  - ProcessingJob                                    |  |  |
|  |  |                                                      |  |  |
|  |  |  Exceptions:                                         |  |  |
|  |  |  - DocumentExtractionError                          |  |  |
|  |  |  - LLMMappingError                                  |  |  |
|  |  |  - RateCardNotFoundError                            |  |  |
|  |  |  - JobNotFoundError                                 |  |  |
|  |  +------------------------------------------------------+  |  |
|  +------------------------------------------------------------+  |
+------------------------------------------------------------------+
```

**Key rule:** Arrows point inward only. Infrastructure imports from Application
and Domain. Application imports from Domain. Domain imports nothing external.

---

## Port Definitions and Adapters

| Port (ABC)                  | Methods                           | Local Adapter                        | Azure Adapter                  |
|-----------------------------|-----------------------------------|--------------------------------------|--------------------------------|
| DocumentExtractorPort       | extract(bytes, filename)          | LocalDocumentExtractorDispatcher     | AzureDocumentExtractor         |
|                             |                                   | (routes to PDFExtractor/XLSXExtractor)|                               |
| LLMMapperPort               | map_to_standard_schema(...)       | LangChainLLMMapper (gpt-4o-mini)     | LangChainLLMMapper (same)      |
|                             |                                   | MockLLMMapper (tests only)           |                                |
| RateCardRepositoryPort      | save, get_by_id, list_all, delete | SQLiteRateCardRepository             | PostgresRateCardRepository     |
| JobRepositoryPort           | save, get_by_id, update_status    | SQLiteJobRepository                  | PostgresJobRepository          |

---

## Adapter Selection by Environment

The `src/config/container.py` module is the **only** place in the codebase where
`settings.environment` is read to select adapters. All other code depends only on
port abstractions.

| Component             | ENVIRONMENT=local                      | ENVIRONMENT=azure                      |
|-----------------------|----------------------------------------|----------------------------------------|
| Document extraction   | LocalDocumentExtractorDispatcher       | AzureDocumentExtractor                 |
|                       | PDFExtractor (pdfplumber)              | (Azure Document Intelligence REST API) |
|                       | XLSXExtractor (openpyxl)               |                                        |
| LLM mapping           | LangChainLLMMapper (gpt-4o-mini)       | LangChainLLMMapper (gpt-4o-mini)       |
| LLM caching           | InMemoryCache (per process)            | SQLiteCache (persistent)               |
| Database              | SQLite via aiosqlite                   | PostgreSQL via asyncpg                 |
| Task processing       | FastAPI BackgroundTasks                | Celery + Redis (future)                |
| Repository classes    | SQLiteJobRepository                    | PostgresJobRepository                  |
|                       | SQLiteRateCardRepository               | PostgresRateCardRepository             |

---

## Dependency Injection Flow

```
FastAPI startup
     |
     v
create_app() in src/api/app.py
     |
     v
lifespan() context manager
  - mkdir(upload_dir)
  - await init_db()    <-- creates SQLite/PostgreSQL tables
     |
     v
HTTP request arrives at route handler
     |
     v
FastAPI resolves Depends() chain:
  get_settings_dep()          --> Settings singleton (lru_cache)
  get_db_session()            --> yields AsyncSession (commit/rollback on exit)
  get_upload_use_case()       --> UploadDocumentUseCase(job_repo, upload_dir)
  get_process_use_case()      --> ProcessDocumentUseCase(extractor, mapper,
                                    session_factory, upload_dir)
                                  (session_factory passed, not open session)
  get_rate_card_use_case()    --> GetRateCardUseCase(rate_card_repo, job_repo)
     |
     v
Route handler calls use case method
     |
     v
Use case coordinates domain entities through port ABCs
(no direct infrastructure imports in use case code)
```

---

## Data Flow: Upload to Rate Card Retrieval

```
Step 1 - HTTP Upload
  Client  -->  POST /v1/documents/upload (multipart file)
  API     -->  validate size (<= 25MB) and extension (.pdf/.xlsx)
  API     -->  UploadDocumentUseCase.execute(file_bytes, filename)
               - determine file_format from extension
               - ProcessingJob.create() --> status: PENDING
               - write bytes to {upload_dir}/{job_id}/{filename}
               - job_repo.save(job) --> SQL INSERT
  API     -->  BackgroundTasks.add_task(ProcessDocumentUseCase.execute, job_id)
  API     -->  202 Accepted { id, status: "pending" }

Step 2 - Background Processing (after response sent)
  ProcessDocumentUseCase.execute(job_id)
               - creates own AsyncSession from session_factory
               - job_repo.get_by_id(job_id)
               - job.mark_processing() --> SQL UPDATE status=processing
               - file_path.read_bytes()  [asyncio.to_thread]
               - DocumentExtractorPort.extract(bytes, filename)
                   LOCAL:  PDFExtractor (pdfplumber in thread pool)
                           XLSXExtractor (openpyxl in thread pool)
                   AZURE:  AzureDocumentExtractor (httpx REST polling)
               --> list[ExtractedTable]
               - LLMMapperPort.map_to_standard_schema(tables, filename, format)
                   LangChainLLMMapper
                   - check InMemoryCache (cache hit = free)
                   - ChatOpenAI.with_structured_output(StandardizedRateCard)
                   - ainvoke(prompt + table_text)
                   - returns validated StandardizedRateCard
               - RateCard.create(job_id, standardized_data)
               - rate_card_repo.save(rate_card) --> SQL INSERT
               - job.mark_completed(rate_card_id) --> SQL UPDATE status=completed
               - session.commit()

Step 3 - Client Polling
  Client  -->  GET /v1/documents/{job_id}/status
  API     -->  job_repo.get_by_id(job_id)
  API     -->  200 { status: "completed", rate_card_id: "..." }

Step 4 - Rate Card Retrieval
  Client  -->  GET /v1/rate-cards/{rate_card_id}
  API     -->  rate_card_repo.get_by_id(rate_card_id)
               - deserializes JSON column back to StandardizedRateCard
  API     -->  200 { carrier_name, rates: [...], surcharges: [...], ... }
```

---

## Testing Strategy

The test suite is designed to run with zero external service calls:

| Test Layer    | Dependencies Replaced                   | Tests Verify                           |
|---------------|-----------------------------------------|----------------------------------------|
| Unit tests    | MockDocumentExtractor, MockLLMMapper,   | Extractor parsing, mapper invocation,  |
|               | MockJobRepository, MockRateCardRepository| use case state machine logic           |
|               | in-memory SQLite (db_session fixture)   |                                        |
| Integration   | All infrastructure via                  | HTTP status codes, response schemas,   |
|               | dependency_overrides in FastAPI,        | full upload->status->retrieval flow    |
|               | ImmediateProcessUseCase (synchronous)   |                                        |

LangChainLLMMapper with real OpenAI API is tested manually:
```python
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
