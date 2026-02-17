"""Unit tests for the application use cases.

Uses inline mock implementations of repository ports to avoid any database
dependency. All tests run entirely in memory with no file system or network
access (except where tmp_path is used for upload directory testing).

MockJobRepository and MockRateCardRepository are defined here as they are
specific to these use case tests and not shared with other test modules.
"""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Optional

import pytest

from src.application.use_cases.get_rate_card import GetRateCardUseCase
from src.application.use_cases.process_document import ProcessDocumentUseCase
from src.application.use_cases.upload_document import UploadDocumentUseCase
from src.domain.entities.job import JobStatus, ProcessingJob
from src.domain.entities.rate_card import RateCard, RateEntry, StandardizedRateCard
from src.domain.exceptions import (
    DocumentExtractionError,
    JobNotFoundError,
    RateCardNotFoundError,
    UnsupportedFileFormatError,
)
from src.domain.ports.document_extractor import DocumentExtractorPort, ExtractedTable
from src.domain.ports.job_repository import JobRepositoryPort
from src.domain.ports.rate_card_repository import RateCardRepositoryPort
from src.infrastructure.mappers.mock_mapper import MockLLMMapper


# ---------------------------------------------------------------------------
# Inline test double implementations
# ---------------------------------------------------------------------------

class MockJobRepository(JobRepositoryPort):
    """In-memory job repository for use case testing."""

    def __init__(self) -> None:
        self._jobs: dict[str, ProcessingJob] = {}

    async def save(self, job: ProcessingJob) -> ProcessingJob:
        self._jobs[job.id] = job
        return job

    async def get_by_id(self, job_id: str) -> ProcessingJob:
        if job_id not in self._jobs:
            raise JobNotFoundError(f"Job '{job_id}' not found.")
        return self._jobs[job_id]

    async def update_status(self, job: ProcessingJob) -> ProcessingJob:
        self._jobs[job.id] = job
        return job


class MockRateCardRepository(RateCardRepositoryPort):
    """In-memory rate card repository for use case testing."""

    def __init__(self) -> None:
        self._cards: dict[str, RateCard] = {}

    async def save(self, rate_card: RateCard) -> RateCard:
        self._cards[rate_card.id] = rate_card
        return rate_card

    async def get_by_id(self, rate_card_id: str) -> RateCard:
        if rate_card_id not in self._cards:
            raise RateCardNotFoundError(f"Rate card '{rate_card_id}' not found.")
        return self._cards[rate_card_id]

    async def list_all(self, limit: int = 100, offset: int = 0) -> list[RateCard]:
        return list(self._cards.values())[offset:offset + limit]

    async def delete(self, rate_card_id: str) -> None:
        if rate_card_id not in self._cards:
            raise RateCardNotFoundError(f"Rate card '{rate_card_id}' not found.")
        del self._cards[rate_card_id]


class MockDocumentExtractor(DocumentExtractorPort):
    """Document extractor that returns fixed test tables."""

    def __init__(self, tables: Optional[list[ExtractedTable]] = None, raise_exc: Optional[Exception] = None) -> None:
        self._tables = tables or [
            ExtractedTable(
                headers=["From", "To", "Rate"],
                rows=[["US", "EU", "10.0"]],
                sheet_name="Sheet1",
            )
        ]
        self._raise_exc = raise_exc

    async def extract(self, file_bytes: bytes, filename: str) -> list[ExtractedTable]:
        if self._raise_exc:
            raise self._raise_exc
        return self._tables


# ---------------------------------------------------------------------------
# Helper factory for a session factory mock used in ProcessDocumentUseCase
# ---------------------------------------------------------------------------

def make_mock_session_factory(job_repo: MockJobRepository, rate_card_repo: MockRateCardRepository):
    """Build a mock session factory that injects test repositories into ProcessDocumentUseCase.

    ProcessDocumentUseCase creates its own repositories from the session inside execute().
    We patch the import at test time by monkeypatching the module.
    Instead, we use a simpler approach: subclass ProcessDocumentUseCase to override
    repository creation.
    """
    pass


class InjectableProcessDocumentUseCase(ProcessDocumentUseCase):
    """ProcessDocumentUseCase subclass that accepts pre-built repositories for testing.

    Overrides _load_and_start_job and _run_pipeline to use injected repositories
    instead of creating them from a session factory.
    """

    def __init__(
        self,
        document_extractor: DocumentExtractorPort,
        llm_mapper: MockLLMMapper,
        job_repo: MockJobRepository,
        rate_card_repo: MockRateCardRepository,
        upload_dir: str,
    ) -> None:
        # Pass None as session_factory — overridden methods bypass it.
        super().__init__(
            document_extractor=document_extractor,
            llm_mapper=llm_mapper,
            session_factory=None,
            upload_dir=upload_dir,
        )
        self._test_job_repo = job_repo
        self._test_rate_card_repo = rate_card_repo

    async def execute(self, job_id: str) -> RateCard:
        """Override execute() to use injected test repositories."""
        job = await self._load_and_start_job(job_id, self._test_job_repo)
        try:
            rate_card = await self._run_pipeline(job, self._test_rate_card_repo)
            job.mark_completed(rate_card_id=rate_card.id)
            await self._test_job_repo.update_status(job)
            return rate_card
        except (DocumentExtractionError, Exception) as exc:
            job.mark_failed(error_message=str(exc))
            await self._test_job_repo.update_status(job)
            raise


# ---------------------------------------------------------------------------
# UploadDocumentUseCase tests
# ---------------------------------------------------------------------------

async def test_upload_creates_pending_job(tmp_path: Path) -> None:
    """Uploading a valid XLSX file must create a ProcessingJob with PENDING status."""
    job_repo = MockJobRepository()
    use_case = UploadDocumentUseCase(job_repository=job_repo, upload_dir=str(tmp_path))

    # Minimal valid XLSX magic bytes.
    fake_xlsx = b"PK\x03\x04" + b"\x00" * 100
    job = await use_case.execute(file_bytes=fake_xlsx, filename="rates.xlsx")

    assert job.status == JobStatus.PENDING
    assert job.filename == "rates.xlsx"
    assert job.file_format == "excel"
    assert job.id is not None


async def test_upload_saves_file_to_disk(tmp_path: Path) -> None:
    """The uploaded file must be written to {upload_dir}/{job_id}/{filename}."""
    job_repo = MockJobRepository()
    use_case = UploadDocumentUseCase(job_repository=job_repo, upload_dir=str(tmp_path))

    fake_xlsx = b"PK\x03\x04" + b"\x00" * 50
    job = await use_case.execute(file_bytes=fake_xlsx, filename="test.xlsx")

    expected_path = tmp_path / job.id / "test.xlsx"
    assert expected_path.exists()
    assert expected_path.read_bytes() == fake_xlsx


async def test_upload_rejects_csv_format(tmp_path: Path) -> None:
    """Uploading a .csv file must raise UnsupportedFileFormatError."""
    job_repo = MockJobRepository()
    use_case = UploadDocumentUseCase(job_repository=job_repo, upload_dir=str(tmp_path))

    with pytest.raises(UnsupportedFileFormatError) as exc_info:
        await use_case.execute(file_bytes=b"a,b,c\n1,2,3", filename="data.csv")
    assert ".csv" in exc_info.value.message


async def test_upload_accepts_pdf_format(tmp_path: Path) -> None:
    """Uploading a .pdf file must be accepted and produce a job with file_format='pdf'."""
    job_repo = MockJobRepository()
    use_case = UploadDocumentUseCase(job_repository=job_repo, upload_dir=str(tmp_path))

    fake_pdf = b"%PDF-1.4" + b"\x00" * 50
    job = await use_case.execute(file_bytes=fake_pdf, filename="rates.pdf")

    assert job.file_format == "pdf"
    assert job.status == JobStatus.PENDING


# ---------------------------------------------------------------------------
# ProcessDocumentUseCase tests
# ---------------------------------------------------------------------------

async def test_process_document_happy_path(tmp_path: Path) -> None:
    """Successful processing must result in a COMPLETED job and persisted RateCard."""
    job_repo = MockJobRepository()
    rate_card_repo = MockRateCardRepository()
    extractor = MockDocumentExtractor()
    mapper = MockLLMMapper()

    # Pre-save a job and write a file to disk.
    job = ProcessingJob.create(filename="test.xlsx", file_format="excel")
    await job_repo.save(job)
    file_dir = tmp_path / job.id
    file_dir.mkdir(parents=True)
    (file_dir / "test.xlsx").write_bytes(b"PK\x03\x04" + b"\x00" * 50)

    use_case = InjectableProcessDocumentUseCase(
        document_extractor=extractor,
        llm_mapper=mapper,
        job_repo=job_repo,
        rate_card_repo=rate_card_repo,
        upload_dir=str(tmp_path),
    )
    rate_card = await use_case.execute(job.id)

    assert isinstance(rate_card, RateCard)
    assert rate_card.standardized_data.carrier_name == "Test Carrier"

    updated_job = await job_repo.get_by_id(job.id)
    assert updated_job.status == JobStatus.COMPLETED
    assert updated_job.rate_card_id == rate_card.id


async def test_process_document_marks_failed_on_extraction_error(tmp_path: Path) -> None:
    """Extraction failure must result in FAILED job with error_message populated."""
    job_repo = MockJobRepository()
    rate_card_repo = MockRateCardRepository()
    extractor = MockDocumentExtractor(
        raise_exc=DocumentExtractionError("PDF parsing failed")
    )
    mapper = MockLLMMapper()

    job = ProcessingJob.create(filename="bad.pdf", file_format="pdf")
    await job_repo.save(job)
    file_dir = tmp_path / job.id
    file_dir.mkdir(parents=True)
    (file_dir / "bad.pdf").write_bytes(b"%PDF-1.4" + b"\x00" * 20)

    use_case = InjectableProcessDocumentUseCase(
        document_extractor=extractor,
        llm_mapper=mapper,
        job_repo=job_repo,
        rate_card_repo=rate_card_repo,
        upload_dir=str(tmp_path),
    )

    with pytest.raises(DocumentExtractionError):
        await use_case.execute(job.id)

    updated_job = await job_repo.get_by_id(job.id)
    assert updated_job.status == JobStatus.FAILED
    assert updated_job.error_message is not None
    assert "PDF parsing failed" in updated_job.error_message


async def test_process_document_raises_job_not_found() -> None:
    """Calling execute() with a non-existent job_id must raise JobNotFoundError."""
    job_repo = MockJobRepository()
    rate_card_repo = MockRateCardRepository()
    use_case = InjectableProcessDocumentUseCase(
        document_extractor=MockDocumentExtractor(),
        llm_mapper=MockLLMMapper(),
        job_repo=job_repo,
        rate_card_repo=rate_card_repo,
        upload_dir="/tmp",
    )

    with pytest.raises(JobNotFoundError):
        await use_case.execute("non-existent-job-id")


# ---------------------------------------------------------------------------
# GetRateCardUseCase tests
# ---------------------------------------------------------------------------

async def test_get_rate_card_returns_existing_card() -> None:
    """GetRateCardUseCase must return a rate card that exists in the repository."""
    rate_card_repo = MockRateCardRepository()
    job_repo = MockJobRepository()

    standard = StandardizedRateCard(
        carrier_name="Test Carrier",
        source_format="excel",
        source_filename="test.xlsx",
        rates=[
            RateEntry(
                origin="US", destination="EU",
                service_level="express",
                weight_min_kg=1.0, weight_max_kg=10.0,
                rate_per_kg=12.0, currency="USD",
            )
        ],
    )
    card = RateCard.create(job_id="job-123", standardized_data=standard)
    await rate_card_repo.save(card)

    use_case = GetRateCardUseCase(
        rate_card_repository=rate_card_repo,
        job_repository=job_repo,
    )
    result = await use_case.get_rate_card(card.id)

    assert result.id == card.id
    assert result.standardized_data.carrier_name == "Test Carrier"


async def test_get_rate_card_raises_for_missing_id() -> None:
    """get_rate_card() must raise RateCardNotFoundError for an unknown ID."""
    use_case = GetRateCardUseCase(
        rate_card_repository=MockRateCardRepository(),
        job_repository=MockJobRepository(),
    )
    with pytest.raises(RateCardNotFoundError):
        await use_case.get_rate_card("does-not-exist")


async def test_get_job_status_returns_correct_status() -> None:
    """get_job_status() must return the current state of an existing job."""
    job_repo = MockJobRepository()
    job = ProcessingJob.create(filename="test.xlsx", file_format="excel")
    await job_repo.save(job)

    use_case = GetRateCardUseCase(
        rate_card_repository=MockRateCardRepository(),
        job_repository=job_repo,
    )
    result = await use_case.get_job_status(job.id)

    assert result.id == job.id
    assert result.status == JobStatus.PENDING
