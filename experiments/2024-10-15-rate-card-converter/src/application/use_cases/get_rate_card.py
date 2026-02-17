"""Use case for retrieving processed rate cards and job status records.

These use cases are thin read-only operations that delegate entirely to
the repository ports. Their value is in maintaining the port abstraction:
the API layer does not import from infrastructure directly.
"""

from __future__ import annotations

import logging

from src.domain.entities.job import ProcessingJob
from src.domain.entities.rate_card import RateCard
from src.domain.ports.job_repository import JobRepositoryPort
from src.domain.ports.rate_card_repository import RateCardRepositoryPort

logger = logging.getLogger(__name__)


class GetRateCardUseCase:
    """Retrieves rate cards and job status records from their respective repositories.

    Args:
        rate_card_repository: Port for RateCard persistence access.
        job_repository: Port for ProcessingJob persistence access.
    """

    def __init__(
        self,
        rate_card_repository: RateCardRepositoryPort,
        job_repository: JobRepositoryPort,
    ) -> None:
        self._rate_card_repository = rate_card_repository
        self._job_repository = job_repository

    async def get_rate_card(self, rate_card_id: str) -> RateCard:
        """Retrieve a RateCard aggregate by its unique identifier.

        Args:
            rate_card_id: UUID string identifying the rate card.

        Returns:
            The RateCard aggregate with the given id.

        Raises:
            RateCardNotFoundError: If no rate card with the given id exists.
        """
        rate_card = await self._rate_card_repository.get_by_id(rate_card_id)
        logger.debug("Retrieved rate card '%s'.", rate_card_id)
        return rate_card

    async def get_job_status(self, job_id: str) -> ProcessingJob:
        """Retrieve a ProcessingJob by its unique identifier.

        Args:
            job_id: UUID string identifying the processing job.

        Returns:
            The ProcessingJob with the given id including current status.

        Raises:
            JobNotFoundError: If no job with the given id exists.
        """
        job = await self._job_repository.get_by_id(job_id)
        logger.debug("Retrieved job '%s' (status: %s).", job_id, job.status.value)
        return job

    async def list_rate_cards(
        self, limit: int = 100, offset: int = 0
    ) -> list[RateCard]:
        """Retrieve a paginated list of all stored rate cards.

        Args:
            limit: Maximum number of records to return. Defaults to 100.
            offset: Number of records to skip before returning results.

        Returns:
            A list of RateCard aggregates ordered by creation time descending.
        """
        return await self._rate_card_repository.list_all(limit=limit, offset=offset)
