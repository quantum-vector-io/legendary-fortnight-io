"""Use case for validating and storing an uploaded rate card document.

This use case is responsible only for the upload phase: validating the file
format, saving the raw bytes to disk, creating a ProcessingJob in PENDING state,
and returning the job to the API layer. It intentionally does NOT start the
processing pipeline — that is triggered separately by ProcessDocumentUseCase
via FastAPI's BackgroundTasks mechanism.

This separation allows the upload endpoint to respond immediately with a job ID
while processing runs asynchronously. The client polls the job status endpoint
until COMPLETED or FAILED.
"""

from __future__ import annotations

import asyncio
import logging
from pathlib import Path

from src.domain.entities.job import ProcessingJob
from src.domain.exceptions import UnsupportedFileFormatError
from src.domain.ports.job_repository import JobRepositoryPort

logger = logging.getLogger(__name__)

# Supported file extensions and their normalized format identifiers.
_SUPPORTED_FORMATS: dict[str, str] = {
    ".pdf": "pdf",
    ".xlsx": "excel",
}


class UploadDocumentUseCase:
    """Validates, stores, and registers a document upload as a processing job.

    Args:
        job_repository: Port for persisting ProcessingJob entities.
        upload_dir: Filesystem directory where uploaded files are stored.
                    Each job gets its own subdirectory: {upload_dir}/{job_id}/
    """

    def __init__(self, job_repository: JobRepositoryPort, upload_dir: str) -> None:
        self._job_repository = job_repository
        self._upload_dir = Path(upload_dir)

    async def execute(self, file_bytes: bytes, filename: str) -> ProcessingJob:
        """Validate and store an uploaded document, creating a PENDING job.

        Args:
            file_bytes: Raw bytes of the uploaded document.
            filename: Original filename from the multipart upload.

        Returns:
            A newly created ProcessingJob in PENDING status with a generated UUID.

        Raises:
            UnsupportedFileFormatError: If the file extension is not .pdf or .xlsx.
            StorageError: If the file cannot be written to disk or the job cannot
                          be persisted to the database.
        """
        file_format = self._resolve_format(filename)
        job = ProcessingJob.create(filename=filename, file_format=file_format)

        await self._save_file_to_disk(file_bytes, job.id, filename)
        saved_job = await self._job_repository.save(job)

        logger.info("Job '%s' created for file '%s' (format: %s).", job.id, filename, file_format)
        return saved_job

    def _resolve_format(self, filename: str) -> str:
        """Determine the file format from the filename extension.

        Args:
            filename: The original filename including extension.

        Returns:
            The normalized format string: 'pdf' or 'excel'.

        Raises:
            UnsupportedFileFormatError: If the extension is not in the supported set.
        """
        suffix = Path(filename).suffix.lower()
        if suffix not in _SUPPORTED_FORMATS:
            raise UnsupportedFileFormatError(
                f"Unsupported file format '{suffix}'. Accepted formats: .pdf, .xlsx",
                detail={"filename": filename, "suffix": suffix},
            )
        return _SUPPORTED_FORMATS[suffix]

    async def _save_file_to_disk(
        self, file_bytes: bytes, job_id: str, filename: str
    ) -> None:
        """Write the file bytes to the job-specific upload directory.

        Creates the directory {upload_dir}/{job_id}/ and writes the file bytes.
        File I/O runs in a thread pool to avoid blocking the event loop.

        Args:
            file_bytes: Raw file bytes to write.
            job_id: UUID of the job, used as the subdirectory name.
            filename: Original filename, used as the stored filename.

        Raises:
            StorageError: If the directory cannot be created or the file write fails.
        """
        await asyncio.to_thread(self._write_file_sync, file_bytes, job_id, filename)

    def _write_file_sync(self, file_bytes: bytes, job_id: str, filename: str) -> None:
        """Synchronous file write operation for thread pool execution.

        Args:
            file_bytes: File content to write.
            job_id: Job UUID for the storage subdirectory.
            filename: Target filename.
        """
        job_dir = self._upload_dir / job_id
        job_dir.mkdir(parents=True, exist_ok=True)
        file_path = job_dir / filename
        file_path.write_bytes(file_bytes)
        logger.debug("File saved to '%s' (%d bytes).", file_path, len(file_bytes))
