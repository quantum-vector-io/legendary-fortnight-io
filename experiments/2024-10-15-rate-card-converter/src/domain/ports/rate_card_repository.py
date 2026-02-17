"""Abstract port defining the contract for rate card persistence adapters.

The RateCardRepositoryPort decouples the application layer from the specific
database technology used (SQLite locally, PostgreSQL in Azure). Both the
SQLiteRateCardRepository and PostgresRateCardRepository implement this interface.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from src.domain.entities.rate_card import RateCard


class RateCardRepositoryPort(ABC):
    """Abstract port for RateCard aggregate persistence.

    Provides CRUD operations for RateCard aggregates. The save() method
    performs an upsert (insert or update) using the rate card's id as the
    natural key.
    """

    @abstractmethod
    async def save(self, rate_card: RateCard) -> RateCard:
        """Persist a RateCard aggregate (insert or update by id).

        Args:
            rate_card: The RateCard aggregate to persist. If a record with
                       the same id already exists, it is updated.

        Returns:
            The persisted RateCard, identical to the input after successful write.

        Raises:
            StorageError: If the database operation fails.
        """

    @abstractmethod
    async def get_by_id(self, rate_card_id: str) -> RateCard:
        """Retrieve a RateCard aggregate by its unique identifier.

        Args:
            rate_card_id: UUID string identifying the rate card.

        Returns:
            The RateCard aggregate with the given id.

        Raises:
            RateCardNotFoundError: If no rate card with the given id exists.
            StorageError: If the database operation fails.
        """

    @abstractmethod
    async def list_all(self, limit: int = 100, offset: int = 0) -> list[RateCard]:
        """Retrieve a paginated list of all stored rate cards.

        Args:
            limit: Maximum number of records to return. Defaults to 100.
            offset: Number of records to skip before returning results.

        Returns:
            A list of RateCard aggregates ordered by creation time descending.

        Raises:
            StorageError: If the database operation fails.
        """

    @abstractmethod
    async def delete(self, rate_card_id: str) -> None:
        """Remove a rate card from the repository.

        Args:
            rate_card_id: UUID string identifying the rate card to delete.

        Raises:
            RateCardNotFoundError: If no rate card with the given id exists.
            StorageError: If the database operation fails.
        """
