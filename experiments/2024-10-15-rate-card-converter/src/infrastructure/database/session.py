"""Async SQLAlchemy session factory supporting SQLite (local) and PostgreSQL (Azure).

The engine and session factory are module-level singletons created when
settings are first read. The init_db() coroutine must be called once at
application startup to create all tables. The get_session() async generator
is designed for use as a FastAPI Depends() dependency: it opens a session,
yields it to the caller, commits on success, and rolls back on exception.
"""

from __future__ import annotations

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from src.config.settings import get_settings
from src.infrastructure.database.models import Base

# Module-level engine and session factory — initialized lazily on first call to
# _get_engine() so that test code can override settings before the engine is created.
_engine: AsyncEngine | None = None
_session_factory: async_sessionmaker[AsyncSession] | None = None


def _get_engine() -> AsyncEngine:
    """Return the module-level async engine, creating it on first call.

    SQLite requires check_same_thread=False to work correctly with async
    drivers across multiple coroutines. PostgreSQL does not accept this argument.

    Returns:
        The configured AsyncEngine instance.
    """
    global _engine
    if _engine is None:
        settings = get_settings()
        db_url = settings.effective_database_url
        connect_args: dict = {}
        if "sqlite" in db_url:
            connect_args["check_same_thread"] = False
        _engine = create_async_engine(
            db_url,
            connect_args=connect_args,
            echo=settings.log_level == "DEBUG",
        )
    return _engine


def get_session_factory() -> async_sessionmaker[AsyncSession]:
    """Return the module-level async session factory, creating it on first call.

    expire_on_commit=False prevents SQLAlchemy from expiring ORM attributes
    after a commit, which would trigger lazy loads and fail in async context.

    Returns:
        The configured async_sessionmaker instance.
    """
    global _session_factory
    if _session_factory is None:
        _session_factory = async_sessionmaker(
            _get_engine(),
            expire_on_commit=False,
        )
    return _session_factory


async def init_db() -> None:
    """Create all database tables if they do not already exist.

    Must be called once at application startup (in the FastAPI lifespan
    context manager). Safe to call multiple times: CREATE TABLE IF NOT EXISTS
    semantics are used by SQLAlchemy's create_all.

    Raises:
        StorageError: Propagated from SQLAlchemy if the engine cannot connect.
    """
    engine = _get_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Yield an async database session with automatic commit and rollback.

    Intended for use as a FastAPI Depends() dependency. Each HTTP request
    receives its own session. The session is committed on successful handler
    completion or rolled back if an exception propagates.

    Yields:
        An AsyncSession bound to the current database engine.

    Raises:
        Any exception raised inside the with block after rollback.
    """
    factory = get_session_factory()
    async with factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def dispose_engine() -> None:
    """Dispose the database engine and release all connection pool resources.

    Called during application shutdown (FastAPI lifespan teardown) to cleanly
    close all open database connections.
    """
    global _engine, _session_factory
    if _engine is not None:
        await _engine.dispose()
        _engine = None
        _session_factory = None
