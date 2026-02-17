"""SQLAlchemy-based repository adapters for local (SQLite) development.

Despite the name, these repositories use generic SQLAlchemy 2.0 async sessions
and will work with any database supported by SQLAlchemy (SQLite, PostgreSQL,
MySQL). The 'sqlite' prefix reflects the local-default configuration, not a
SQLite-specific implementation.

Each repository accepts an AsyncSession injected by the FastAPI dependency
system. Transaction control (commit/rollback) is handled by the session provider
(get_session in session.py), not by the repositories themselves. This keeps
repositories focused on data access without transaction management concerns.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.entities.job import JobStatus, ProcessingJob
from src.domain.entities.rate_card import RateCard, StandardizedRateCard
from src.domain.exceptions import JobNotFoundError, RateCardNotFoundError, StorageError
from src.domain.ports.job_repository import JobRepositoryPort
from src.domain.ports.rate_card_repository import RateCardRepositoryPort
from src.infrastructure.database.models import JobModel, RateCardModel


class SQLiteJobRepository(JobRepositoryPort):
    """ProcessingJob persistence adapter using SQLAlchemy async sessions.

    Args:
        session: An active AsyncSession for database interaction.
    """

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def save(self, job: ProcessingJob) -> ProcessingJob:
        """Insert a new ProcessingJob record into the database.

        Args:
            job: The job to persist. Its id must not already exist.

        Returns:
            The persisted job (identical to the input on success).

        Raises:
            StorageError: If the database operation fails.
        """
        try:
            model = self._entity_to_model(job)
            self._session.add(model)
            await self._session.flush()
            return job
        except Exception as exc:
            raise StorageError(f"Failed to save job '{job.id}': {exc}") from exc

    async def get_by_id(self, job_id: str) -> ProcessingJob:
        """Retrieve a ProcessingJob by its UUID.

        Args:
            job_id: The UUID string of the job to retrieve.

        Returns:
            The ProcessingJob with the given id.

        Raises:
            JobNotFoundError: If no job with the given id exists.
            StorageError: If the database operation fails.
        """
        try:
            result = await self._session.execute(
                select(JobModel).where(JobModel.id == job_id)
            )
            model = result.scalar_one_or_none()
        except Exception as exc:
            raise StorageError(f"Failed to retrieve job '{job_id}': {exc}") from exc

        if model is None:
            raise JobNotFoundError(f"Job '{job_id}' not found.")

        return self._model_to_entity(model)

    async def update_status(self, job: ProcessingJob) -> ProcessingJob:
        """Persist status changes on an existing job record.

        Uses session.merge() to update only the mutable status fields without
        re-inserting the full record.

        Args:
            job: The job with mutated status to persist.

        Returns:
            The updated job.

        Raises:
            StorageError: If the database operation fails.
        """
        try:
            model = self._entity_to_model(job)
            await self._session.merge(model)
            await self._session.flush()
            return job
        except Exception as exc:
            raise StorageError(f"Failed to update job '{job.id}': {exc}") from exc

    def _entity_to_model(self, job: ProcessingJob) -> JobModel:
        """Convert a ProcessingJob domain entity to a JobModel ORM instance.

        Args:
            job: The domain entity to convert.

        Returns:
            A JobModel instance ready for SQLAlchemy operations.
        """
        return JobModel(
            id=job.id,
            filename=job.filename,
            file_format=job.file_format,
            status=job.status.value,
            error_message=job.error_message,
            rate_card_id=job.rate_card_id,
            created_at=job.created_at,
            updated_at=job.updated_at,
        )

    def _model_to_entity(self, model: JobModel) -> ProcessingJob:
        """Convert a JobModel ORM instance to a ProcessingJob domain entity.

        Args:
            model: The ORM model instance from a database query.

        Returns:
            A ProcessingJob domain entity.
        """
        return ProcessingJob(
            id=model.id,
            filename=model.filename,
            file_format=model.file_format,
            status=JobStatus(model.status),
            error_message=model.error_message,
            rate_card_id=model.rate_card_id,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )


class SQLiteRateCardRepository(RateCardRepositoryPort):
    """RateCard persistence adapter using SQLAlchemy async sessions.

    Args:
        session: An active AsyncSession for database interaction.
    """

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def save(self, rate_card: RateCard) -> RateCard:
        """Persist a RateCard aggregate (upsert by id).

        Args:
            rate_card: The RateCard to persist.

        Returns:
            The persisted RateCard.

        Raises:
            StorageError: If the database operation fails.
        """
        try:
            model = self._entity_to_model(rate_card)
            await self._session.merge(model)
            await self._session.flush()
            return rate_card
        except Exception as exc:
            raise StorageError(f"Failed to save rate card '{rate_card.id}': {exc}") from exc

    async def get_by_id(self, rate_card_id: str) -> RateCard:
        """Retrieve a RateCard by its UUID.

        Args:
            rate_card_id: The UUID string of the rate card to retrieve.

        Returns:
            The RateCard aggregate.

        Raises:
            RateCardNotFoundError: If no rate card with the given id exists.
            StorageError: If the database operation fails.
        """
        try:
            result = await self._session.execute(
                select(RateCardModel).where(RateCardModel.id == rate_card_id)
            )
            model = result.scalar_one_or_none()
        except Exception as exc:
            raise StorageError(f"Failed to retrieve rate card '{rate_card_id}': {exc}") from exc

        if model is None:
            raise RateCardNotFoundError(f"Rate card '{rate_card_id}' not found.")

        return self._model_to_entity(model)

    async def list_all(self, limit: int = 100, offset: int = 0) -> list[RateCard]:
        """Retrieve a paginated list of all stored rate cards.

        Args:
            limit: Maximum number of records to return.
            offset: Number of records to skip.

        Returns:
            A list of RateCard aggregates.

        Raises:
            StorageError: If the database operation fails.
        """
        try:
            result = await self._session.execute(
                select(RateCardModel)
                .order_by(RateCardModel.created_at.desc())
                .limit(limit)
                .offset(offset)
            )
            models = result.scalars().all()
            return [self._model_to_entity(m) for m in models]
        except Exception as exc:
            raise StorageError(f"Failed to list rate cards: {exc}") from exc

    async def delete(self, rate_card_id: str) -> None:
        """Remove a rate card from the repository.

        Args:
            rate_card_id: UUID of the rate card to delete.

        Raises:
            RateCardNotFoundError: If the rate card does not exist.
            StorageError: If the database operation fails.
        """
        try:
            result = await self._session.execute(
                select(RateCardModel).where(RateCardModel.id == rate_card_id)
            )
            model = result.scalar_one_or_none()
            if model is None:
                raise RateCardNotFoundError(f"Rate card '{rate_card_id}' not found.")
            await self._session.delete(model)
            await self._session.flush()
        except RateCardNotFoundError:
            raise
        except Exception as exc:
            raise StorageError(f"Failed to delete rate card '{rate_card_id}': {exc}") from exc

    def _entity_to_model(self, rate_card: RateCard) -> RateCardModel:
        """Convert a RateCard aggregate to a RateCardModel ORM instance.

        The StandardizedRateCard value object is serialized to a dict via
        model_dump() and stored in the JSON column.

        Args:
            rate_card: The domain aggregate to convert.

        Returns:
            A RateCardModel ready for SQLAlchemy operations.
        """
        data = rate_card.standardized_data
        return RateCardModel(
            id=rate_card.id,
            job_id=rate_card.job_id,
            carrier_name=data.carrier_name,
            carrier_code=data.carrier_code,
            source_format=data.source_format,
            source_filename=data.source_filename,
            standardized_data=rate_card.standardized_data.model_dump(),
            created_at=rate_card.created_at,
            updated_at=rate_card.updated_at,
        )

    def _model_to_entity(self, model: RateCardModel) -> RateCard:
        """Convert a RateCardModel ORM instance to a RateCard aggregate.

        Deserializes the JSON standardized_data column back into a
        StandardizedRateCard Pydantic model.

        Args:
            model: The ORM model instance from a database query.

        Returns:
            A RateCard aggregate with a fully populated StandardizedRateCard.
        """
        standardized = StandardizedRateCard.model_validate(model.standardized_data)
        return RateCard(
            id=model.id,
            job_id=model.job_id,
            standardized_data=standardized,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )
