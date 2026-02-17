"""Use case orchestrating the full document processing pipeline.

This is the core use case. It coordinates the complete transformation from a
stored uploaded document to a persisted StandardizedRateCard:

    1. Load the processing job from the repository.
    2. Transition job status to PROCESSING.
    3. Read the raw document bytes from disk.
    4. Extract tables using the document extractor port.
    5. Map extracted data to StandardizedRateCard using the LLM mapper port.
    6. Persist the RateCard aggregate via the repository port.
    7. Transition job status to COMPLETED.

On any error in steps 3-7, the job is transitioned to FAILED with the error
message recorded. This ensures the job's final state always reflects the
processing outcome regardless of where the failure occurred.

IMPORTANT - Session lifecycle: This use case receives a session_factory
(async_sessionmaker) rather than an open AsyncSession. This is required because
ProcessDocumentUseCase runs inside FastAPI's BackgroundTasks, which executes
after the HTTP response has been sent and the request-scoped session has been
closed. Creating a fresh session inside execute() ensures the session is valid
for the full duration of background processing.
"""

from __future__ import annotations

import asyncio
import logging
from pathlib import Path
from typing import Any

from src.domain.entities.job import ProcessingJob
from src.domain.entities.rate_card import RateCard
from src.domain.exceptions import (
    DocumentExtractionError,
    JobNotFoundError,
    LLMMappingError,
    StorageError,
)
from src.domain.ports.document_extractor import DocumentExtractorPort
from src.domain.ports.llm_mapper import LLMMapperPort

logger = logging.getLogger(__name__)


class ProcessDocumentUseCase:
    """Orchestrates document extraction, LLM mapping, and rate card persistence.

    Args:
        document_extractor: Port adapter for extracting tables from documents.
        llm_mapper: Port adapter for semantic mapping to StandardizedRateCard.
        session_factory: SQLAlchemy async_sessionmaker for creating DB sessions.
                         Receives the factory (not an open session) to support
                         execution in FastAPI BackgroundTasks.
        upload_dir: Root directory where uploaded files are stored.
    """

    def __init__(
        self,
        document_extractor: DocumentExtractorPort,
        llm_mapper: LLMMapperPort,
        session_factory: Any,
        upload_dir: str,
    ) -> None:
        self._extractor = document_extractor
        self._mapper = llm_mapper
        self._session_factory = session_factory
        self._upload_dir = Path(upload_dir)

    async def execute(self, job_id: str) -> RateCard:
        """Run the full processing pipeline for a given job.

        Creates its own database session to support background task execution.
        All pipeline stages are enclosed in a try/except so that job failure
        is always recorded before the exception propagates.

        Args:
            job_id: UUID of the ProcessingJob created during upload.

        Returns:
            The persisted RateCard aggregate produced by the pipeline.

        Raises:
            JobNotFoundError: If the job does not exist.
            DocumentExtractionError: If document parsing fails.
            LLMMappingError: If LLM structured output fails.
            StorageError: If file I/O or database operations fail.
        """
        async with self._session_factory() as session:
            from src.infrastructure.repositories.sqlite_repository import (
                SQLiteJobRepository,
                SQLiteRateCardRepository,
            )
            job_repo = SQLiteJobRepository(session)
            rate_card_repo = SQLiteRateCardRepository(session)

            job = await self._load_and_start_job(job_id, job_repo)

            try:
                rate_card = await self._run_pipeline(job, rate_card_repo)
                job.mark_completed(rate_card_id=rate_card.id)
                await job_repo.update_status(job)
                await session.commit()
                logger.info("Job '%s' completed. RateCard '%s' saved.", job_id, rate_card.id)
                return rate_card

            except (DocumentExtractionError, LLMMappingError, StorageError) as exc:
                await self._handle_pipeline_failure(job, job_repo, session, exc)
                raise

            except Exception as exc:
                await self._handle_pipeline_failure(
                    job, job_repo, session,
                    StorageError(f"Unexpected error during processing: {exc}")
                )
                raise

    async def _load_and_start_job(
        self, job_id: str, job_repo: Any
    ) -> ProcessingJob:
        """Load the job from the repository and transition it to PROCESSING.

        Args:
            job_id: UUID of the job to load.
            job_repo: Job repository instance bound to the current session.

        Returns:
            The ProcessingJob with PROCESSING status.

        Raises:
            JobNotFoundError: If the job does not exist.
        """
        job = await job_repo.get_by_id(job_id)
        job.mark_processing()
        await job_repo.update_status(job)
        logger.info("Job '%s' started processing file '%s'.", job_id, job.filename)
        return job

    async def _run_pipeline(self, job: ProcessingJob, rate_card_repo: Any) -> RateCard:
        """Execute extraction, mapping, and persistence in sequence.

        Args:
            job: The processing job with filename and file_format details.
            rate_card_repo: Rate card repository bound to the current session.

        Returns:
            The persisted RateCard aggregate.
        """
        file_bytes = await self._read_file(job)
        extracted_tables = await self._extract_document(file_bytes, job)
        standardized = await self._map_to_schema(extracted_tables, job)
        rate_card = RateCard.create(job_id=job.id, standardized_data=standardized)
        return await rate_card_repo.save(rate_card)

    async def _read_file(self, job: ProcessingJob) -> bytes:
        """Read the uploaded file bytes from disk.

        File I/O runs in a thread pool to avoid blocking the event loop.

        Args:
            job: The processing job with id and filename.

        Returns:
            Raw bytes of the uploaded document.

        Raises:
            StorageError: If the file cannot be read.
        """
        file_path = self._upload_dir / job.id / job.filename
        try:
            return await asyncio.to_thread(file_path.read_bytes)
        except OSError as exc:
            raise StorageError(
                f"Cannot read uploaded file '{file_path}': {exc}",
                detail={"job_id": job.id, "file_path": str(file_path)},
            ) from exc

    async def _extract_document(self, file_bytes: bytes, job: ProcessingJob) -> list:
        """Extract tabular content from the document bytes.

        Args:
            file_bytes: Raw document bytes.
            job: The processing job for filename context.

        Returns:
            List of ExtractedTable instances from the document extractor port.
        """
        logger.debug("Extracting tables from '%s' (%d bytes).", job.filename, len(file_bytes))
        return await self._extractor.extract(file_bytes, job.filename)

    async def _map_to_schema(
        self, extracted_tables: list, job: ProcessingJob
    ) -> object:
        """Invoke the LLM mapper to produce a StandardizedRateCard.

        Args:
            extracted_tables: Tables from the extraction step.
            job: The processing job for filename and format context.

        Returns:
            A StandardizedRateCard value object.
        """
        logger.debug(
            "Mapping %d tables from '%s' via LLM.", len(extracted_tables), job.filename
        )
        return await self._mapper.map_to_standard_schema(
            extracted_tables=extracted_tables,
            source_filename=job.filename,
            source_format=job.file_format,
        )

    async def _handle_pipeline_failure(
        self, job: ProcessingJob, job_repo: Any, session: Any, exc: Exception
    ) -> None:
        """Record a pipeline failure on the job and commit the status update.

        This method is called in the exception handler to ensure the job's FAILED
        status is always persisted, even if the failure occurred mid-pipeline.

        Args:
            job: The job to mark as failed.
            job_repo: Job repository bound to the current session.
            session: The current AsyncSession for committing the status update.
            exc: The exception that caused the failure.
        """
        error_message = str(exc)
        logger.error("Job '%s' failed: %s", job.id, error_message)
        job.mark_failed(error_message=error_message)
        try:
            await job_repo.update_status(job)
            await session.commit()
        except Exception as commit_exc:
            logger.critical(
                "Failed to persist FAILED status for job '%s': %s", job.id, commit_exc
            )
