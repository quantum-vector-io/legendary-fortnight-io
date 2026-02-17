"""Domain-level exceptions for the Rate Card Converter application.

All exceptions inherit from RateCardConverterError so callers can catch the
entire exception hierarchy with a single except clause when needed. Each
exception carries an optional detail dictionary for structured error context
that API error handlers can serialize into HTTP responses.

Exception Hierarchy:
    RateCardConverterError
    ├── DocumentExtractionError
    │   └── UnsupportedFileFormatError
    ├── LLMMappingError
    ├── RateCardNotFoundError
    ├── JobNotFoundError
    ├── DomainValidationError
    └── StorageError
"""

from __future__ import annotations


class RateCardConverterError(Exception):
    """Base exception for all Rate Card Converter domain errors.

    Args:
        message: Human-readable description of the error.
        detail: Optional dictionary with structured error context for
                serialization in API responses.
    """

    def __init__(self, message: str, detail: dict | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.detail = detail or {}


class DocumentExtractionError(RateCardConverterError):
    """Raised when a document cannot be parsed by the extraction adapter.

    This exception wraps low-level parsing errors from pdfplumber, openpyxl,
    or the Azure Document Intelligence SDK into a domain-level error that the
    application layer can handle without depending on specific library internals.
    """


class UnsupportedFileFormatError(DocumentExtractionError):
    """Raised when the uploaded file format is not supported.

    Valid formats are PDF (.pdf) and Excel (.xlsx). This exception is raised
    before any extraction attempt if the file extension or magic bytes do not
    match a supported format.
    """


class LLMMappingError(RateCardConverterError):
    """Raised when the LLM adapter fails to produce a valid structured response.

    This exception covers cases such as API timeouts, authentication failures,
    or malformed LLM output that cannot be parsed into the StandardizedRateCard
    schema.
    """


class RateCardNotFoundError(RateCardConverterError):
    """Raised when a rate card cannot be found in the repository by its ID."""


class JobNotFoundError(RateCardConverterError):
    """Raised when a processing job cannot be found in the repository by its ID."""


class DomainValidationError(RateCardConverterError):
    """Raised when extracted data fails domain business rule validation.

    Unlike Pydantic validation errors (which catch schema mismatches), this
    exception covers semantic violations such as an empty rates list or
    logically inconsistent weight ranges.
    """


class StorageError(RateCardConverterError):
    """Raised when a database or file system I/O operation fails.

    Wraps lower-level SQLAlchemy or OS errors into a domain exception so
    the application layer does not depend on infrastructure-specific error
    types.
    """
