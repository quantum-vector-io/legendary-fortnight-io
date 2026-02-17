"""Processing job entity tracking the asynchronous document processing lifecycle.

A ProcessingJob represents the state machine for a single document upload
through the conversion pipeline. The allowed state transitions are:

    PENDING -> PROCESSING -> COMPLETED
    PENDING -> PROCESSING -> FAILED

State mutation methods (mark_processing, mark_completed, mark_failed) are the
only valid way to change job status. Direct field assignment is intentionally
left possible (dataclass is not frozen) to support ORM reconstruction.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional


class JobStatus(str, Enum):
    """Processing job lifecycle states.

    Inherits from str so that JobStatus values serialize directly to their
    string representation in JSON without requiring a custom encoder.
    """

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class ProcessingJob:
    """An asynchronous document processing job.

    Tracks the lifecycle of converting an uploaded document from raw bytes
    through extraction, LLM mapping, and persistence into a RateCard aggregate.

    Attributes:
        id: Unique identifier (UUID4 string).
        filename: Original filename of the uploaded document.
        file_format: Detected document format: 'pdf' or 'xlsx'.
        status: Current processing state (see JobStatus enum).
        error_message: Human-readable failure description, set on FAILED status.
        rate_card_id: ID of the resulting RateCard once processing completes.
        created_at: Timestamp when the job was first created.
        updated_at: Timestamp of the most recent status change.
    """

    id: str
    filename: str
    file_format: str
    status: JobStatus
    error_message: Optional[str]
    rate_card_id: Optional[str]
    created_at: datetime
    updated_at: datetime

    @classmethod
    def create(cls, filename: str, file_format: str) -> "ProcessingJob":
        """Create a new job in the PENDING state with a generated identity.

        Args:
            filename: Original filename of the document to be processed.
            file_format: Document format identifier, either 'pdf' or 'xlsx'.

        Returns:
            A new ProcessingJob with PENDING status and current timestamps.
        """
        now = datetime.utcnow()
        return cls(
            id=str(uuid.uuid4()),
            filename=filename,
            file_format=file_format,
            status=JobStatus.PENDING,
            error_message=None,
            rate_card_id=None,
            created_at=now,
            updated_at=now,
        )

    def mark_processing(self) -> None:
        """Transition the job to PROCESSING status.

        Called at the start of the document processing pipeline after the
        file bytes have been loaded and before extraction begins.
        """
        self.status = JobStatus.PROCESSING
        self.updated_at = datetime.utcnow()

    def mark_completed(self, rate_card_id: str) -> None:
        """Transition the job to COMPLETED status and record the resulting rate card.

        Args:
            rate_card_id: ID of the RateCard aggregate produced by this job.
        """
        self.status = JobStatus.COMPLETED
        self.rate_card_id = rate_card_id
        self.updated_at = datetime.utcnow()

    def mark_failed(self, error_message: str) -> None:
        """Transition the job to FAILED status and record the failure reason.

        Args:
            error_message: Human-readable description of the failure cause.
        """
        self.status = JobStatus.FAILED
        self.error_message = error_message
        self.updated_at = datetime.utcnow()
