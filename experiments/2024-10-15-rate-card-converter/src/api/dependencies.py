"""FastAPI dependency factories for use case and database session injection.

These functions are used with FastAPI's Depends() mechanism. Each dependency
function returns or yields the appropriate service instance configured for the
current request. The async session is yielded (not returned) so that commit
and rollback are handled around the full request lifecycle.

Session factory vs session: ProcessDocumentUseCase receives the session_factory
(async_sessionmaker) rather than an open session. This is required because
it runs in FastAPI BackgroundTasks, which executes after the response has been
sent and the request-scoped session closed. The use case creates its own session
internally via the factory.
"""

from __future__ import annotations

from collections.abc import AsyncGenerator

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.application.use_cases.get_rate_card import GetRateCardUseCase
from src.application.use_cases.process_document import ProcessDocumentUseCase
from src.application.use_cases.upload_document import UploadDocumentUseCase
from src.config.container import get_document_extractor, get_llm_mapper
from src.config.settings import Settings, get_settings
from src.infrastructure.database.session import get_session, get_session_factory
from src.infrastructure.repositories.sqlite_repository import (
    SQLiteJobRepository,
    SQLiteRateCardRepository,
)


async def get_settings_dep() -> Settings:
    """Return the application settings singleton.

    Returns:
        The cached Settings instance.
    """
    return get_settings()


async def get_db_session(
    settings: Settings = Depends(get_settings_dep),
) -> AsyncGenerator[AsyncSession, None]:
    """Yield an async database session for the duration of an HTTP request.

    The session is committed on successful handler completion and rolled back
    on exception. The session is always closed after the request.

    Yields:
        An AsyncSession bound to the configured database engine.
    """
    async for session in get_session():
        yield session


async def get_upload_use_case(
    session: AsyncSession = Depends(get_db_session),
    settings: Settings = Depends(get_settings_dep),
) -> UploadDocumentUseCase:
    """Build an UploadDocumentUseCase with the request-scoped database session.

    Args:
        session: Request-scoped AsyncSession from get_db_session.
        settings: Application settings for upload_dir configuration.

    Returns:
        A configured UploadDocumentUseCase instance.
    """
    job_repository = SQLiteJobRepository(session)
    return UploadDocumentUseCase(
        job_repository=job_repository,
        upload_dir=settings.upload_dir,
    )


async def get_process_use_case(
    settings: Settings = Depends(get_settings_dep),
) -> ProcessDocumentUseCase:
    """Build a ProcessDocumentUseCase with a session factory for background execution.

    This dependency does NOT inject a request-scoped session. Instead it passes
    the session factory so the use case can create its own session when running
    in a BackgroundTask after the request session has closed.

    Args:
        settings: Application settings for adapter selection and upload_dir.

    Returns:
        A configured ProcessDocumentUseCase instance.
    """
    return ProcessDocumentUseCase(
        document_extractor=get_document_extractor(settings),
        llm_mapper=get_llm_mapper(settings),
        session_factory=get_session_factory(),
        upload_dir=settings.upload_dir,
    )


async def get_rate_card_use_case(
    session: AsyncSession = Depends(get_db_session),
) -> GetRateCardUseCase:
    """Build a GetRateCardUseCase with the request-scoped database session.

    Args:
        session: Request-scoped AsyncSession from get_db_session.

    Returns:
        A configured GetRateCardUseCase instance.
    """
    rate_card_repository = SQLiteRateCardRepository(session)
    job_repository = SQLiteJobRepository(session)
    return GetRateCardUseCase(
        rate_card_repository=rate_card_repository,
        job_repository=job_repository,
    )
