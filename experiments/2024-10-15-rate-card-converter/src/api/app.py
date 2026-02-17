"""FastAPI application factory for the Rate Card Converter service.

The create_app() function constructs and configures the FastAPI application:
- Registers all API v1 routers.
- Attaches domain exception handlers for clean HTTP error responses.
- Manages the database engine lifecycle via the lifespan context manager.

The module-level app = create_app() line creates the application instance
that Uvicorn discovers when running:
    uvicorn src.api.app:app --reload

The lifespan context manager is preferred over the deprecated on_event
decorators (removed in FastAPI 0.95+ in favor of lifespan) for startup
and shutdown hooks.
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncGenerator

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from src.config.settings import get_settings
from src.domain.exceptions import (
    DocumentExtractionError,
    DomainValidationError,
    JobNotFoundError,
    LLMMappingError,
    RateCardNotFoundError,
    StorageError,
    UnsupportedFileFormatError,
)
from src.infrastructure.database.session import dispose_engine, init_db

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Manage application startup and shutdown lifecycle.

    Startup: Creates the upload directory and initializes database tables.
    Shutdown: Disposes the database engine and releases connection pool resources.

    Args:
        app: The FastAPI application instance (unused but required by signature).

    Yields:
        Control to the application during its running phase.
    """
    settings = get_settings()
    upload_path = Path(settings.upload_dir)
    upload_path.mkdir(parents=True, exist_ok=True)
    logger.info("Upload directory initialized at '%s'.", upload_path.resolve())

    await init_db()
    logger.info("Database tables initialized (URL: %s).", settings.effective_database_url)

    yield

    await dispose_engine()
    logger.info("Database engine disposed. Application shutdown complete.")


def create_app() -> FastAPI:
    """Construct and configure the FastAPI application instance.

    Registers API routers, exception handlers, and the lifespan context.
    This factory pattern allows test code to create isolated app instances
    with overridden dependencies.

    Returns:
        A fully configured FastAPI application instance.
    """
    from src.api.v1.routes.documents import router as documents_router
    from src.api.v1.routes.rate_cards import router as rate_cards_router

    app = FastAPI(
        title="Rate Card Converter",
        description=(
            "Convert freight carrier rate cards from PDF and Excel formats "
            "to a standardized canonical schema using LLM-assisted semantic field mapping."
        ),
        version="0.1.0",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )

    app.include_router(
        documents_router,
        prefix="/v1/documents",
        tags=["Documents"],
    )
    app.include_router(
        rate_cards_router,
        prefix="/v1/rate-cards",
        tags=["Rate Cards"],
    )

    _register_exception_handlers(app)

    return app


def _register_exception_handlers(app: FastAPI) -> None:
    """Attach domain exception handlers that convert errors to HTTP responses.

    Domain exceptions are not HTTP-aware, so this mapping layer translates
    them into appropriate status codes and structured JSON error bodies.
    All handlers follow the same format: {"detail": "<message>"}.

    Args:
        app: The FastAPI application to attach handlers to.
    """

    @app.exception_handler(RateCardNotFoundError)
    async def rate_card_not_found(request: Request, exc: RateCardNotFoundError) -> JSONResponse:
        return JSONResponse(status_code=404, content={"detail": exc.message})

    @app.exception_handler(JobNotFoundError)
    async def job_not_found(request: Request, exc: JobNotFoundError) -> JSONResponse:
        return JSONResponse(status_code=404, content={"detail": exc.message})

    @app.exception_handler(UnsupportedFileFormatError)
    async def unsupported_format(request: Request, exc: UnsupportedFileFormatError) -> JSONResponse:
        return JSONResponse(status_code=400, content={"detail": exc.message})

    @app.exception_handler(DocumentExtractionError)
    async def extraction_error(request: Request, exc: DocumentExtractionError) -> JSONResponse:
        return JSONResponse(status_code=422, content={"detail": exc.message})

    @app.exception_handler(LLMMappingError)
    async def mapping_error(request: Request, exc: LLMMappingError) -> JSONResponse:
        return JSONResponse(status_code=422, content={"detail": exc.message})

    @app.exception_handler(DomainValidationError)
    async def validation_error(request: Request, exc: DomainValidationError) -> JSONResponse:
        return JSONResponse(status_code=422, content={"detail": exc.message})

    @app.exception_handler(StorageError)
    async def storage_error(request: Request, exc: StorageError) -> JSONResponse:
        logger.error("Storage error: %s", exc.message)
        return JSONResponse(status_code=503, content={"detail": "A storage error occurred. Please retry."})


# Module-level application instance discovered by Uvicorn.
app = create_app()
