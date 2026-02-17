"""Route handlers for document upload and job status endpoints.

POST /v1/documents/upload
    Accepts a multipart file upload (.pdf or .xlsx), creates a PENDING job,
    and triggers asynchronous processing via FastAPI BackgroundTasks.
    Returns HTTP 202 Accepted with the job ID immediately.

GET /v1/documents/{job_id}/status
    Returns the current processing status of a job, including the rate_card_id
    once processing completes.

File size validation: A maximum of 25 MB is enforced by reading up to
MAX_UPLOAD_BYTES + 1 bytes and checking the actual length before processing.
This prevents large files from consuming excess memory without requiring
streaming upload infrastructure.
"""

from __future__ import annotations

import logging
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, UploadFile, status
from pydantic import BaseModel

from src.api.dependencies import (
    get_process_use_case,
    get_rate_card_use_case,
    get_upload_use_case,
)
from src.application.use_cases.get_rate_card import GetRateCardUseCase
from src.application.use_cases.process_document import ProcessDocumentUseCase
from src.application.use_cases.upload_document import UploadDocumentUseCase
from src.domain.exceptions import JobNotFoundError, UnsupportedFileFormatError

logger = logging.getLogger(__name__)

router = APIRouter()

# Maximum allowed upload size: 25 MB.
MAX_UPLOAD_BYTES = 25 * 1024 * 1024

# Accepted content types for the upload endpoint.
ALLOWED_CONTENT_TYPES = {
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "application/vnd.ms-excel",
    "application/octet-stream",  # Some clients send this for Excel files.
}


class JobResponseSchema(BaseModel):
    """Response schema for job creation and status queries.

    Attributes:
        id: UUID of the processing job.
        filename: Original uploaded filename.
        status: Current job lifecycle status (pending, processing, completed, failed).
        rate_card_id: UUID of the resulting RateCard, populated on completion.
        error_message: Failure description, populated on failed status.
        created_at: ISO 8601 timestamp of job creation.
        updated_at: ISO 8601 timestamp of most recent status change.
    """

    id: str
    filename: str
    status: str
    rate_card_id: Optional[str] = None
    error_message: Optional[str] = None
    created_at: str
    updated_at: str


@router.post(
    "/upload",
    response_model=JobResponseSchema,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Upload a rate card document for processing.",
    description=(
        "Accepts a PDF or Excel rate card file. Creates a processing job "
        "and initiates asynchronous extraction and LLM mapping. "
        "Poll the status endpoint with the returned job ID."
    ),
)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(..., description="Rate card document (.pdf or .xlsx, max 25MB)."),
    upload_use_case: UploadDocumentUseCase = Depends(get_upload_use_case),
    process_use_case: ProcessDocumentUseCase = Depends(get_process_use_case),
) -> JobResponseSchema:
    """Handle a document upload, create a processing job, and enqueue processing.

    Args:
        background_tasks: FastAPI background task runner.
        file: The uploaded multipart file.
        upload_use_case: Injected use case for job creation and file storage.
        process_use_case: Injected use case for background processing.

    Returns:
        A JobResponseSchema with the new job's ID and PENDING status.

    Raises:
        HTTPException 413: If the file exceeds the 25 MB size limit.
        HTTPException 400: If the file format is unsupported.
    """
    file_bytes = await _read_and_validate_file(file)

    try:
        job = await upload_use_case.execute(
            file_bytes=file_bytes,
            filename=file.filename or "upload",
        )
    except UnsupportedFileFormatError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=exc.message,
        )

    # Enqueue background processing. BackgroundTasks runs after the response is sent.
    background_tasks.add_task(process_use_case.execute, job.id)

    logger.info("Upload accepted. Job '%s' enqueued for background processing.", job.id)
    return _job_to_schema(job)


@router.get(
    "/{job_id}/status",
    response_model=JobResponseSchema,
    summary="Get the processing status of an uploaded document.",
)
async def get_job_status(
    job_id: str,
    use_case: GetRateCardUseCase = Depends(get_rate_card_use_case),
) -> JobResponseSchema:
    """Return the current lifecycle status of a processing job.

    Args:
        job_id: UUID of the processing job to query.
        use_case: Injected use case for job status retrieval.

    Returns:
        A JobResponseSchema with the current job state.

    Raises:
        HTTPException 404: If no job with the given ID exists.
    """
    try:
        job = await use_case.get_job_status(job_id)
    except JobNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=exc.message,
        )

    return _job_to_schema(job)


async def _read_and_validate_file(file: UploadFile) -> bytes:
    """Read file bytes and enforce the maximum upload size limit.

    Reads MAX_UPLOAD_BYTES + 1 to detect oversized files with a single read
    call, then checks the actual length against the limit.

    Args:
        file: The uploaded UploadFile from the request.

    Returns:
        The raw file bytes.

    Raises:
        HTTPException 413: If the file exceeds MAX_UPLOAD_BYTES.
    """
    file_bytes = await file.read(MAX_UPLOAD_BYTES + 1)
    if len(file_bytes) > MAX_UPLOAD_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File exceeds the maximum allowed size of {MAX_UPLOAD_BYTES // (1024 * 1024)} MB.",
        )
    return file_bytes


def _job_to_schema(job: object) -> JobResponseSchema:
    """Convert a ProcessingJob domain entity to a JobResponseSchema.

    Args:
        job: A ProcessingJob domain entity.

    Returns:
        The corresponding JobResponseSchema for API serialization.
    """
    return JobResponseSchema(
        id=job.id,
        filename=job.filename,
        status=job.status.value,
        rate_card_id=job.rate_card_id,
        error_message=job.error_message,
        created_at=job.created_at.isoformat(),
        updated_at=job.updated_at.isoformat(),
    )
