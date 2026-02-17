"""Dependency injection container wiring settings to concrete adapter implementations.

This is the only module in the codebase where ENVIRONMENT is read to select
infrastructure adapters. All adapter selection logic lives here, keeping use
cases and API routes free of environment-specific conditionals.

The LocalDocumentExtractorDispatcher is a thin router that selects between
PDFExtractor and XLSXExtractor based on the file extension at extraction time.
This avoids the need to know the file format until extraction is actually called.

All factory functions are stateless. They accept Settings (or read the singleton)
and return the appropriate adapter instance. Singleton behavior for expensive
objects (like LangChain models) is achieved by using lru_cache on the factory
functions where the Settings object is stable.
"""

from __future__ import annotations

import logging

from src.config.settings import Settings, get_settings
from src.domain.exceptions import UnsupportedFileFormatError
from src.domain.ports.document_extractor import DocumentExtractorPort, ExtractedTable
from src.domain.ports.llm_mapper import LLMMapperPort

logger = logging.getLogger(__name__)


class LocalDocumentExtractorDispatcher(DocumentExtractorPort):
    """Routes document extraction to the appropriate local adapter by file extension.

    Holds a PDFExtractor and XLSXExtractor instance and delegates to the
    correct one when extract() is called. This avoids requiring the caller to
    know the file format in advance.
    """

    def __init__(self) -> None:
        from src.infrastructure.extractors.pdf_extractor import PDFExtractor
        from src.infrastructure.extractors.xlsx_extractor import XLSXExtractor

        self._pdf_extractor = PDFExtractor()
        self._xlsx_extractor = XLSXExtractor()

    async def extract(self, file_bytes: bytes, filename: str) -> list[ExtractedTable]:
        """Dispatch to PDF or XLSX extractor based on filename extension.

        Args:
            file_bytes: Raw document bytes.
            filename: Original filename used to determine the extractor.

        Returns:
            A list of ExtractedTable instances from the appropriate extractor.

        Raises:
            UnsupportedFileFormatError: If the extension is not .pdf or .xlsx.
        """
        lower_name = filename.lower()
        if lower_name.endswith(".pdf"):
            return await self._pdf_extractor.extract(file_bytes, filename)
        if lower_name.endswith(".xlsx"):
            return await self._xlsx_extractor.extract(file_bytes, filename)
        raise UnsupportedFileFormatError(
            f"No extractor registered for file '{filename}'.",
            detail={"filename": filename},
        )


def get_document_extractor(settings: Settings | None = None) -> DocumentExtractorPort:
    """Return the document extractor adapter appropriate for the current environment.

    In local mode: returns a LocalDocumentExtractorDispatcher (pdfplumber + openpyxl).
    In Azure mode: returns an AzureDocumentExtractor (Azure Document Intelligence).

    Args:
        settings: Application settings. Reads the singleton if None.

    Returns:
        A DocumentExtractorPort implementation.
    """
    s = settings or get_settings()
    if s.use_azure_document_extractor:
        from src.infrastructure.extractors.azure_extractor import AzureDocumentExtractor

        logger.info("Using AzureDocumentExtractor (ENVIRONMENT=azure).")
        return AzureDocumentExtractor(
            endpoint=s.azure_document_intelligence_endpoint,
            key=s.azure_document_intelligence_key,
        )
    logger.info("Using LocalDocumentExtractorDispatcher (ENVIRONMENT=local).")
    return LocalDocumentExtractorDispatcher()


def get_llm_mapper(settings: Settings | None = None) -> LLMMapperPort:
    """Return the LLM mapper adapter.

    Currently always returns LangChainLLMMapper, which works in both local and
    Azure environments as long as OPENAI_API_KEY is configured. In tests,
    MockLLMMapper is injected via FastAPI's dependency_overrides mechanism.

    Args:
        settings: Application settings. Reads the singleton if None.

    Returns:
        A LLMMapperPort implementation.
    """
    s = settings or get_settings()
    from src.infrastructure.mappers.langchain_mapper import LangChainLLMMapper

    return LangChainLLMMapper(settings=s)
