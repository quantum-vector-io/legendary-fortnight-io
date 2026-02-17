# System Design: Rate Card Converter

## Data Model

```
ProcessingJob
  id            UUID string         Primary key
  filename      string(512)         Original uploaded filename
  file_format   string(10)          'pdf' or 'excel'
  status        string(20)          'pending' | 'processing' | 'completed' | 'failed'
  error_message text (nullable)     Failure reason when status=failed
  rate_card_id  string(36) (null)   FK to RateCard, set on completion
  created_at    datetime
  updated_at    datetime

RateCard
  id                UUID string     Primary key
  job_id            string(36)      Reference to parent ProcessingJob
  carrier_name      string(256)     Indexed for filtering
  carrier_code      string(50)
  source_format     string(10)      'pdf' or 'excel'
  source_filename   string(512)
  standardized_data JSON            Full StandardizedRateCard serialized as JSON
  created_at        datetime
  updated_at        datetime
```

**Denormalization note:** StandardizedRateCard (with nested rates and surcharges)
is stored as a JSON blob rather than normalized into separate tables. This is
appropriate for the current scope: the primary access pattern is retrieve-by-id
and the full card is always needed together. For production use with filtering or
aggregation requirements, individual rate entries should be extracted to a
rate_entries table with an FK to rate_cards.

---

## Document Processing Sequence Diagram

```
Client          API             UploadUseCase     BackgroundTask    Extractor
  |               |                   |                  |               |
  |--POST /upload->|                   |                  |               |
  |               |--execute()-------->|                  |               |
  |               |                   |--write_file()     |               |
  |               |                   |--job_repo.save()  |               |
  |               |<--ProcessingJob----|                  |               |
  |               |--add_task(--------->ProcessUseCase    |               |
  |               |  process, job_id) |                  |               |
  |<--202+job_id--|                   |                  |               |
  |               |                   |                  |               |
  |               |                   |            (after response sent)  |
  |               |                   |                  |               |
  |               |                   |            --execute(job_id)     |
  |               |                   |            --mark_processing      |
  |               |                   |            --read_file()          |
  |               |                   |            --extract()----------->|
  |               |                   |            <--list[ExtractedTable]|
  |               |                   |            --map_to_schema()      |
  |               |                   |            (LLM call or cache hit)|
  |               |                   |            <--StandardizedRateCard|
  |               |                   |            --rate_card_repo.save()|
  |               |                   |            --mark_completed()     |
  |               |                   |                  |               |
  |--GET /status-->|                   |                  |               |
  |<--{status:completed,rate_card_id}--|                  |               |
  |               |                   |                  |               |
  |--GET /rate-cards/{id}-->|          |                  |               |
  |<--{carrier_name, rates, surcharges}|                  |               |
```

---

## LLM Integration Design

### Prompt Architecture

The system prompt is static (same for every call) and deliberately long (>1024
tokens) to benefit from OpenAI's automatic prompt caching (50% cost reduction on
cached prefix tokens). Variable document content goes in the human message.

```
[System message - static, >1024 tokens, cached after first call]
  "You are a logistics data extraction specialist..."
  Extraction rules (field mapping, unit conversion, normalization)

[Human message - variable, not cached]
  "Source filename: {filename}"
  "Source format: {format}"
  "Extracted document content:"
  "{table_text}"  (truncated to 6000 chars)
```

### Structured Output

`ChatOpenAI.with_structured_output(StandardizedRateCard, method="function_calling")`
binds the LLM to respond with JSON that matches the Pydantic v2 schema. OpenAI's
function calling mechanism validates the response structure. If validation fails,
LangChain raises an exception that is wrapped as `LLMMappingError`.

**Pydantic v2 constraint:** OpenAI's function calling JSON Schema rejects
`minimum`, `maximum`, `minLength`, `maxLength` properties. The `StandardizedRateCard`
schema uses no `ge`/`le`/`min_length` Pydantic field validators for this reason.

### Caching

```
Call 1: table_text="Origin | US..."  -> cache MISS -> API call ($0.0005)
Call 2: table_text="Origin | US..."  -> cache HIT  -> $0.00 (in-process)
Call 3: table_text="Origin | DE..."  -> cache MISS -> API call ($0.0005)
```

`InMemoryCache` is per-process and non-persistent. It prevents redundant API
calls when the same document is re-uploaded within the same server session.
For production, `SQLiteCache` persists across restarts.

### Token Budget Calculation (gpt-4o-mini pricing, 2024)

| Component           | Tokens  | Cost/document        |
|---------------------|---------|----------------------|
| System prompt       | ~400    | cached after 1st call|
| Table text (6000ch) | ~1500   | $0.000225 (input)    |
| Response (2048 max) | ~500    | $0.000300 (output)   |
| Total               | ~2400   | ~$0.0005             |

---

## Scaling Strategies

### Current Architecture (Local / Experiment)

- Single Python process, asyncio cooperative concurrency.
- CPU-bound extraction (pdfplumber, openpyxl) runs on the thread pool via
  `asyncio.to_thread()` so it does not block the event loop.
- FastAPI `BackgroundTasks` for post-response processing (no separate worker process).
- SQLite for persistence (no concurrent writes from multiple processes).
- Suitable for: development, demos, single-user experimentation.
- Limitation: One Uvicorn worker. SQLite locks on concurrent writes.

### Production Path (Azure / Scale)

**Horizontal API scaling:**
- Multiple Uvicorn workers behind a load balancer (Nginx, Azure Application Gateway).
- Replace SQLite with PostgreSQL (`asyncpg` driver, same SQLAlchemy ORM).
- Replace BackgroundTasks with Celery workers pulling from Redis.

**Celery task queue:**
```python
# Replace in container.py:
# BackgroundTasks.add_task(process_use_case.execute, job_id)
# with:
celery_app.send_task("process_document", args=[job_id], queue="document_processing")
```
Workers scale independently of API replicas. `task_acks_late=True` and
`max_retries=3` ensure at-least-once delivery with exponential backoff.

**Azure services:**
- API: Azure Container Apps (auto-scale, managed TLS).
- Worker: Azure Container Instances or AKS pod deployment.
- Database: Azure Database for PostgreSQL Flexible Server.
- Cache/Queue: Azure Cache for Redis.
- Storage: Azure Blob Storage for uploaded files (replace local filesystem).
- Document AI: Azure Document Intelligence for higher-accuracy extraction.
- Secrets: Azure Key Vault for OPENAI_API_KEY, database credentials.

**Estimated capacity (single worker process):**
- LLM call ~3-5s per document (network + model inference).
- Extraction ~0.5-2s per document (CPU-bound, thread pool).
- Total pipeline ~4-7s per document.
- Throughput: ~8-15 documents/minute per worker.
- Scale to 10+ workers for batch processing of hundreds of documents.

---

## Error Handling Matrix

| Error Type                 | Cause                              | HTTP Status | Job Status | Retry? |
|----------------------------|------------------------------------|-------------|------------|--------|
| UnsupportedFileFormatError | .csv or other unsupported extension| 400         | N/A        | No     |
| File too large             | > 25MB upload                      | 413         | N/A        | No     |
| DocumentExtractionError    | pdfplumber/openpyxl parse failure  | 422         | FAILED     | Retry with different file |
| LLMMappingError            | OpenAI API error or invalid output | 422         | FAILED     | Retry (transient)         |
| JobNotFoundError           | Unknown job_id                     | 404         | N/A        | No     |
| RateCardNotFoundError      | Unknown rate_card_id               | 404         | N/A        | No     |
| StorageError               | DB or file I/O failure             | 503         | FAILED     | Yes (infrastructure)      |

---

## Security Considerations

**API key management:**
- OPENAI_API_KEY is read from environment variables, never hardcoded.
- In production, source from Azure Key Vault via Managed Identity.

**File upload security:**
- Maximum upload size enforced at the API layer (25MB).
- File type validation uses magic bytes (first 4-8 bytes), not extension alone.
- Uploaded files stored in a job-specific subdirectory to prevent path traversal.

**No authentication (current scope):**
- This experiment does not implement authentication or authorization.
- In production, add OAuth2 Bearer token validation using FastAPI's
  `OAuth2PasswordBearer` and Azure Active Directory app registration.

---

## Known Limitations

1. No authentication or authorization. All endpoints are publicly accessible.
2. No rate limiting. A single client can flood the upload endpoint.
3. SQLite is not suitable for concurrent writes from multiple processes.
4. LLM output is not fully deterministic despite `temperature=0` (model
   randomness at low probability tokens). InMemoryCache mitigates repeat calls.
5. PDF text extraction quality depends on whether the PDF is text-based or
   scanned (image). Scanned PDFs require OCR (Azure Document Intelligence handles this).
6. No file cleanup: uploaded files in `./uploads/` are never automatically deleted.
