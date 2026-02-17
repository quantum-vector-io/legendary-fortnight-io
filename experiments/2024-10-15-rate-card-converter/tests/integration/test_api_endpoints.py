"""Integration tests for the FastAPI HTTP API endpoints.

Uses httpx.AsyncClient with FastAPI's TestClient (ASGI transport) and
dependency_overrides to replace infrastructure components with test doubles.
No real database, file system, or OpenAI API calls are made.

All dependencies are overridden at the test_client fixture level:
- get_db_session -> yields the in-memory db_session fixture session.
- get_settings_dep -> returns the test settings fixture.
- get_process_use_case -> returns a NoOpProcessDocumentUseCase that immediately
  marks the job as completed using a pre-built rate card.
"""

from __future__ import annotations

import asyncio
from pathlib import Path

import httpx
import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.app import create_app
from src.api.dependencies import (
    get_db_session,
    get_process_use_case,
    get_settings_dep,
)
from src.application.use_cases.process_document import ProcessDocumentUseCase
from src.config.settings import Settings
from src.domain.entities.job import ProcessingJob
from src.domain.entities.rate_card import RateCard, RateEntry, StandardizedRateCard
from src.infrastructure.database.models import Base
from src.infrastructure.mappers.mock_mapper import MockLLMMapper
from src.infrastructure.repositories.sqlite_repository import (
    SQLiteJobRepository,
    SQLiteRateCardRepository,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

class ImmediateProcessUseCase:
    """Test double for ProcessDocumentUseCase that processes synchronously.

    When execute() is called in a BackgroundTask, this use case immediately
    marks the job as completed and persists a mock RateCard, allowing integration
    tests to verify the full upload -> status -> rate card retrieval flow.
    """

    def __init__(self, session: AsyncSession, upload_dir: str) -> None:
        self._session = session
        self._upload_dir = Path(upload_dir)

    async def execute(self, job_id: str) -> None:
        """Mark the job as completed with a mock rate card immediately."""
        job_repo = SQLiteJobRepository(self._session)
        rate_card_repo = SQLiteRateCardRepository(self._session)

        job = await job_repo.get_by_id(job_id)
        job.mark_processing()
        await job_repo.update_status(job)

        standard = StandardizedRateCard(
            carrier_name="Integration Test Carrier",
            source_format=job.file_format,
            source_filename=job.filename,
            rates=[
                RateEntry(
                    origin="US",
                    destination="EU",
                    service_level="express",
                    weight_min_kg=1.0,
                    weight_max_kg=10.0,
                    rate_per_kg=12.5,
                    currency="USD",
                )
            ],
        )
        rate_card = RateCard.create(job_id=job_id, standardized_data=standard)
        saved_card = await rate_card_repo.save(rate_card)

        job.mark_completed(rate_card_id=saved_card.id)
        await job_repo.update_status(job)
        await self._session.commit()


@pytest_asyncio.fixture
async def test_client(db_session: AsyncSession, settings: Settings, tmp_path: Path):
    """Provide an httpx.AsyncClient with all dependencies overridden.

    Overrides:
    - get_db_session: yields the in-memory test session.
    - get_settings_dep: returns the test settings instance.
    - get_process_use_case: returns ImmediateProcessUseCase for synchronous completion.

    Args:
        db_session: In-memory SQLite session from conftest.
        settings: Test settings from conftest.
        tmp_path: Pytest temporary directory for file uploads.

    Yields:
        An httpx.AsyncClient configured against the FastAPI ASGI app.
    """
    app = create_app()

    async def override_db_session():
        yield db_session

    async def override_settings():
        return Settings(
            environment="local",
            openai_api_key="sk-test-fake",
            database_url="sqlite+aiosqlite:///:memory:",
            upload_dir=str(tmp_path),
        )

    async def override_process_use_case():
        return ImmediateProcessUseCase(
            session=db_session,
            upload_dir=str(tmp_path),
        )

    app.dependency_overrides[get_db_session] = override_db_session
    app.dependency_overrides[get_settings_dep] = override_settings
    app.dependency_overrides[get_process_use_case] = override_process_use_case

    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        yield client

    app.dependency_overrides.clear()


def _minimal_xlsx_bytes() -> bytes:
    """Return minimal valid XLSX magic bytes for upload testing."""
    import io
    import openpyxl
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.append(["From", "To", "Rate"])
    ws.append(["US", "EU", "10.0"])
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


def _minimal_pdf_bytes() -> bytes:
    """Return minimal valid PDF bytes for upload testing."""
    return b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n%%EOF"


# ---------------------------------------------------------------------------
# Document upload endpoint tests
# ---------------------------------------------------------------------------

async def test_upload_xlsx_returns_202(test_client: httpx.AsyncClient) -> None:
    """POST /v1/documents/upload with a valid XLSX must return HTTP 202."""
    response = await test_client.post(
        "/v1/documents/upload",
        files={"file": ("test.xlsx", _minimal_xlsx_bytes(), "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
    )
    assert response.status_code == 202


async def test_upload_response_has_job_id(test_client: httpx.AsyncClient) -> None:
    """Upload response body must contain a non-empty job id."""
    response = await test_client.post(
        "/v1/documents/upload",
        files={"file": ("test.xlsx", _minimal_xlsx_bytes(), "application/octet-stream")},
    )
    data = response.json()
    assert "id" in data
    assert data["id"]


async def test_upload_response_has_pending_status(test_client: httpx.AsyncClient) -> None:
    """Upload response status field must be 'pending' immediately after upload."""
    response = await test_client.post(
        "/v1/documents/upload",
        files={"file": ("test.xlsx", _minimal_xlsx_bytes(), "application/octet-stream")},
    )
    data = response.json()
    assert data["status"] == "pending"


async def test_upload_unsupported_format_returns_400(test_client: httpx.AsyncClient) -> None:
    """Uploading a .csv file must return HTTP 400."""
    response = await test_client.post(
        "/v1/documents/upload",
        files={"file": ("data.csv", b"a,b,c\n1,2,3", "text/csv")},
    )
    assert response.status_code == 400


async def test_upload_pdf_returns_202(test_client: httpx.AsyncClient) -> None:
    """POST /v1/documents/upload with a valid PDF must return HTTP 202."""
    response = await test_client.post(
        "/v1/documents/upload",
        files={"file": ("rates.pdf", _minimal_pdf_bytes(), "application/pdf")},
    )
    assert response.status_code == 202


# ---------------------------------------------------------------------------
# Job status endpoint tests
# ---------------------------------------------------------------------------

async def test_get_job_status_returns_200_for_existing_job(
    test_client: httpx.AsyncClient,
) -> None:
    """GET /v1/documents/{job_id}/status must return 200 for an existing job."""
    upload_response = await test_client.post(
        "/v1/documents/upload",
        files={"file": ("test.xlsx", _minimal_xlsx_bytes(), "application/octet-stream")},
    )
    job_id = upload_response.json()["id"]

    # Small delay to allow BackgroundTask to complete.
    await asyncio.sleep(0.3)

    status_response = await test_client.get(f"/v1/documents/{job_id}/status")
    assert status_response.status_code == 200


async def test_get_job_status_returns_404_for_unknown_id(
    test_client: httpx.AsyncClient,
) -> None:
    """GET /v1/documents/{job_id}/status must return 404 for an unknown job ID."""
    response = await test_client.get("/v1/documents/non-existent-job-id/status")
    assert response.status_code == 404


async def test_get_job_status_response_has_required_fields(
    test_client: httpx.AsyncClient,
) -> None:
    """Job status response must include id, filename, status, created_at, updated_at."""
    upload_resp = await test_client.post(
        "/v1/documents/upload",
        files={"file": ("test.xlsx", _minimal_xlsx_bytes(), "application/octet-stream")},
    )
    job_id = upload_resp.json()["id"]

    status_resp = await test_client.get(f"/v1/documents/{job_id}/status")
    data = status_resp.json()

    for field in ["id", "filename", "status", "created_at", "updated_at"]:
        assert field in data, f"Missing field: {field}"


# ---------------------------------------------------------------------------
# Rate card retrieval endpoint tests
# ---------------------------------------------------------------------------

async def test_get_rate_card_returns_404_for_unknown_id(
    test_client: httpx.AsyncClient,
) -> None:
    """GET /v1/rate-cards/{id} must return 404 for an unknown rate card ID."""
    response = await test_client.get("/v1/rate-cards/non-existent-id")
    assert response.status_code == 404


async def test_full_upload_and_retrieve_flow(
    test_client: httpx.AsyncClient,
) -> None:
    """Complete flow: upload -> poll status until completed -> retrieve rate card."""
    # Upload
    upload_resp = await test_client.post(
        "/v1/documents/upload",
        files={"file": ("flow_test.xlsx", _minimal_xlsx_bytes(), "application/octet-stream")},
    )
    assert upload_resp.status_code == 202
    job_id = upload_resp.json()["id"]

    # Poll until completed (max 10 iterations, 0.5s apart).
    rate_card_id = None
    for _ in range(10):
        await asyncio.sleep(0.5)
        status_resp = await test_client.get(f"/v1/documents/{job_id}/status")
        status_data = status_resp.json()
        if status_data["status"] == "completed":
            rate_card_id = status_data.get("rate_card_id")
            break

    assert rate_card_id is not None, "Job did not complete within timeout."

    # Retrieve the rate card.
    card_resp = await test_client.get(f"/v1/rate-cards/{rate_card_id}")
    assert card_resp.status_code == 200
    card_data = card_resp.json()
    assert card_data["carrier_name"] == "Integration Test Carrier"
    assert len(card_data["rates"]) >= 1


async def test_rate_cards_list_endpoint(test_client: httpx.AsyncClient) -> None:
    """GET /v1/rate-cards/ must return a list (possibly empty)."""
    response = await test_client.get("/v1/rate-cards/")
    assert response.status_code == 200
    assert isinstance(response.json(), list)
