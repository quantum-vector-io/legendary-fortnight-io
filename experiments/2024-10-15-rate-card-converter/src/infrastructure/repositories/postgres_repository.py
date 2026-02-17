"""PostgreSQL repository adapters for Azure production deployments.

These classes are structurally identical to the SQLite variants because both
use SQLAlchemy async sessions with the same ORM models. The only functional
difference is that the AsyncEngine is created with a PostgreSQL URL and no
check_same_thread connect argument.

Keeping them as separate classes makes the infrastructure adapter boundary
explicit: the dependency injection container selects these when ENVIRONMENT=azure,
ensuring no SQLite-specific connect_args or workarounds leak into the Azure path.

In a production codebase, these classes would also add:
- Connection pool configuration (pool_size, max_overflow).
- Read replicas for list_all queries.
- Advisory locks for concurrent rate card processing.
"""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from src.infrastructure.repositories.sqlite_repository import (
    SQLiteJobRepository,
    SQLiteRateCardRepository,
)


class PostgresJobRepository(SQLiteJobRepository):
    """ProcessingJob persistence adapter for PostgreSQL (Azure production).

    Inherits all implementation from SQLiteJobRepository. The distinction is
    in the AsyncSession injected at construction time: in Azure mode, the
    session is bound to a PostgreSQL engine created from POSTGRES_URL.

    Args:
        session: An active AsyncSession bound to a PostgreSQL engine.
    """

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session)


class PostgresRateCardRepository(SQLiteRateCardRepository):
    """RateCard persistence adapter for PostgreSQL (Azure production).

    Inherits all implementation from SQLiteRateCardRepository. The distinction
    is in the AsyncSession bound to the PostgreSQL engine in Azure mode.

    Args:
        session: An active AsyncSession bound to a PostgreSQL engine.
    """

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session)
