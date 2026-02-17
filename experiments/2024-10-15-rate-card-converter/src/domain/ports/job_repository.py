"""Abstract port defining the contract for processing job persistence adapters."""

from __future__ import annotations

from abc import ABC, abstractmethod

from src.domain.entities.job import ProcessingJob


class JobRepositoryPort(ABC):
    """Abstract port for ProcessingJob entity persistence.

    Tracks the lifecycle of document processing jobs. The update_status()
    method is used for incremental state changes (PENDING -> PROCESSING ->
    COMPLETED/FAILED) without re-persisting the full entity.
    """

    @abstractmethod
    async def save(self, job: ProcessingJob) -> ProcessingJob:
        """Persist a new ProcessingJob (insert only).

        Args:
            job: The ProcessingJob to insert. The job's id must be unique.

        Returns:
            The persisted ProcessingJob, identical to the input after write.

        Raises:
            StorageError: If the database operation fails.
        """

    @abstractmethod
    async def get_by_id(self, job_id: str) -> ProcessingJob:
        """Retrieve a ProcessingJob by its unique identifier.

        Args:
            job_id: UUID string identifying the job.

        Returns:
            The ProcessingJob with the given id.

        Raises:
            JobNotFoundError: If no job with the given id exists.
            StorageError: If the database operation fails.
        """

    @abstractmethod
    async def update_status(self, job: ProcessingJob) -> ProcessingJob:
        """Persist status changes on an existing ProcessingJob.

        Updates the status, error_message, rate_card_id, and updated_at
        fields of the stored job record. Does not replace the full record.

        Args:
            job: The ProcessingJob with mutated state to persist.

        Returns:
            The updated ProcessingJob.

        Raises:
            JobNotFoundError: If no job with the given id exists.
            StorageError: If the database operation fails.
        """
