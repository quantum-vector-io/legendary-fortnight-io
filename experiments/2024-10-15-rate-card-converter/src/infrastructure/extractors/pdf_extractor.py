"""PDF document extractor using pdfplumber for local and test environments.

pdfplumber is a synchronous library built on top of pdfminer.six. All parsing
work runs inside asyncio.to_thread() to avoid blocking the event loop. This
preserves the async interface defined by DocumentExtractorPort while allowing
the CPU-bound extraction to complete on a thread pool worker.
"""

from __future__ import annotations

import asyncio
import io

import pdfplumber

from src.domain.exceptions import DocumentExtractionError, UnsupportedFileFormatError
from src.domain.ports.document_extractor import DocumentExtractorPort, ExtractedTable

# PDF magic bytes prefix present in all valid PDF files.
_PDF_MAGIC_BYTES = b"%PDF-"


class PDFExtractor(DocumentExtractorPort):
    """Extracts tabular data from PDF documents using pdfplumber.

    Each page of the PDF is scanned for tables. When tables are detected,
    the first row is treated as column headers. Pages with no detected tables
    fall back to full text extraction, populating ExtractedTable.raw_text
    so the LLM mapper can still attempt semantic parsing.
    """

    async def extract(self, file_bytes: bytes, filename: str) -> list[ExtractedTable]:
        """Extract tabular data from a PDF document.

        Runs synchronous pdfplumber parsing in a thread pool executor to
        preserve event loop responsiveness.

        Args:
            file_bytes: Raw PDF document bytes.
            filename: Original filename for logging and error context.

        Returns:
            A list of ExtractedTable instances, one per page that contains
            either a structured table or extractable text.

        Raises:
            UnsupportedFileFormatError: If file_bytes does not begin with PDF magic bytes.
            DocumentExtractionError: If pdfplumber fails to parse the document.
        """
        return await asyncio.to_thread(self._extract_sync, file_bytes, filename)

    def _extract_sync(self, file_bytes: bytes, filename: str) -> list[ExtractedTable]:
        """Synchronous PDF extraction logic executed on a thread pool worker.

        Args:
            file_bytes: Raw PDF document bytes.
            filename: Original filename for error context.

        Returns:
            List of ExtractedTable instances.

        Raises:
            UnsupportedFileFormatError: If file format is invalid.
            DocumentExtractionError: If any pdfplumber error occurs.
        """
        self._validate_magic_bytes(file_bytes, filename)
        try:
            return self._parse_pdf(file_bytes, filename)
        except (UnsupportedFileFormatError, DocumentExtractionError):
            raise
        except Exception as exc:
            raise DocumentExtractionError(
                f"Failed to parse PDF '{filename}': {exc}",
                detail={"filename": filename, "error": str(exc)},
            ) from exc

    def _validate_magic_bytes(self, file_bytes: bytes, filename: str) -> None:
        """Verify the file begins with the PDF magic byte sequence.

        Args:
            file_bytes: File bytes to check.
            filename: Filename for error message context.

        Raises:
            UnsupportedFileFormatError: If the magic bytes are absent.
        """
        if not file_bytes.startswith(_PDF_MAGIC_BYTES):
            raise UnsupportedFileFormatError(
                f"File '{filename}' does not appear to be a valid PDF (missing %PDF- header).",
                detail={"filename": filename},
            )

    def _parse_pdf(self, file_bytes: bytes, filename: str) -> list[ExtractedTable]:
        """Open the PDF and extract tables and text from each page.

        Args:
            file_bytes: Validated PDF bytes.
            filename: Filename for sheet_name labeling.

        Returns:
            List of ExtractedTable instances, one per page.
        """
        results: list[ExtractedTable] = []
        with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
            for page_number, page in enumerate(pdf.pages, start=1):
                table = self._extract_page_table(page, page_number)
                if table is not None:
                    results.append(table)
        return results

    def _extract_page_table(self, page: object, page_number: int) -> ExtractedTable | None:
        """Extract content from a single PDF page.

        Attempts table extraction first. If no table is found, falls back to
        raw text extraction. Returns None only if the page has no content at all.

        Args:
            page: A pdfplumber Page object.
            page_number: 1-based page index for labeling.

        Returns:
            An ExtractedTable with table data or raw text, or None if the page
            is entirely empty.
        """
        sheet_name = f"page_{page_number}"
        tables = page.extract_tables()

        if tables:
            return self._build_table_from_rows(tables[0], sheet_name)

        raw_text = page.extract_text(x_tolerance=3, y_tolerance=3)
        if raw_text and raw_text.strip():
            return ExtractedTable(sheet_name=sheet_name, raw_text=raw_text.strip())

        return None

    def _build_table_from_rows(
        self, raw_rows: list[list[str | None]], sheet_name: str
    ) -> ExtractedTable:
        """Build an ExtractedTable from pdfplumber's raw row list.

        pdfplumber may return None for cells with no content. These are
        normalized to empty strings to ensure the LLM mapper receives uniform
        string data.

        Args:
            raw_rows: 2D list where the first row is treated as headers.
            sheet_name: Label for the extracted table's origin page.

        Returns:
            An ExtractedTable with headers and data rows.
        """
        if not raw_rows:
            return ExtractedTable(sheet_name=sheet_name)

        headers = [str(cell).strip() if cell is not None else "" for cell in raw_rows[0]]
        rows = [
            [str(cell).strip() if cell is not None else "" for cell in row]
            for row in raw_rows[1:]
        ]
        # Filter out rows that are entirely empty strings.
        rows = [row for row in rows if any(cell for cell in row)]

        return ExtractedTable(headers=headers, rows=rows, sheet_name=sheet_name)
