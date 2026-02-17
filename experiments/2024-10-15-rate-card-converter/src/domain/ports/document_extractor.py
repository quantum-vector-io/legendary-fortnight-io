"""Abstract port defining the contract for document extraction adapters.

The DocumentExtractorPort abstracts the mechanism of pulling raw structured
tabular data from a document (PDF or Excel). Concrete implementations may use
pdfplumber, openpyxl, or Azure Document Intelligence — the application layer
does not know which is active.

ExtractedTable is a plain dataclass (not Pydantic) because it is an internal
transfer object between the extraction and mapping stages; it is never
serialized to JSON or sent over the network.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class ExtractedTable:
    """A raw table extracted from a document, prior to semantic mapping.

    Attributes:
        headers: Column header strings as found in the source document.
                 May contain non-standard names that the LLM mapper normalizes.
        rows: List of data rows, each row being a list of cell strings.
              None cells from the source document are converted to empty strings.
        sheet_name: Name of the Excel sheet or page label from the PDF.
                    Used in logging and LLM prompt context.
        raw_text: Full page text when no structured table was found.
                  The LLM mapper falls back to this for semi-structured content.
    """

    headers: list[str] = field(default_factory=list)
    rows: list[list[str]] = field(default_factory=list)
    sheet_name: Optional[str] = None
    raw_text: Optional[str] = None

    def is_empty(self) -> bool:
        """Return True if this table contains no headers and no raw text.

        Returns:
            True when both headers and raw_text are absent or empty.
        """
        return not self.headers and not self.raw_text


class DocumentExtractorPort(ABC):
    """Abstract port for document content extraction.

    Implementations of this port are responsible for converting raw document
    bytes into a list of ExtractedTable objects. Each concrete adapter handles
    a specific extraction strategy (pdfplumber, openpyxl, Azure Document
    Intelligence) while exposing an identical async interface to the application.

    All concrete implementations must handle the thread-blocking nature of
    synchronous parsing libraries by running CPU-bound work in a thread pool
    via asyncio.to_thread() rather than blocking the event loop directly.
    """

    @abstractmethod
    async def extract(self, file_bytes: bytes, filename: str) -> list[ExtractedTable]:
        """Extract tabular data from document bytes.

        Args:
            file_bytes: Raw bytes of the document to parse.
            filename: Original filename, used for format detection, logging,
                      and error context. Not used for file I/O.

        Returns:
            A list of ExtractedTable instances, one per sheet or page.
            Pages with no detected tables populate raw_text instead of headers.
            An empty list is returned only if the document has no content.

        Raises:
            UnsupportedFileFormatError: If the file type is not supported by
                                        this extractor.
            DocumentExtractionError: If parsing fails for any other reason.
        """
