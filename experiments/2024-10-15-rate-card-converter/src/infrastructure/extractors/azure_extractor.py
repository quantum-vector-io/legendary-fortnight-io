"""Azure Document Intelligence extractor for production (Azure) deployments.

This adapter is NOT invoked in local or test environments. It is selected by
the dependency injection container only when ENVIRONMENT=azure and valid
Azure Document Intelligence credentials are configured. Locally, the
LocalDocumentExtractorDispatcher (using pdfplumber / openpyxl) is used instead.

The implementation uses httpx for async HTTP calls to the Azure Document
Intelligence REST API v4 (2024-02-29-preview). The SDK (azure-ai-documentintelligence)
is intentionally avoided to minimize mandatory dependencies for local development.

Polling pattern: Azure Document Intelligence is asynchronous. The initial POST
returns an Operation-Location header URL. We poll that URL until the operation
reaches 'succeeded' or 'failed' status, with a maximum of 30 attempts at 2-second
intervals (60 seconds total timeout).
"""

from __future__ import annotations

import asyncio
import logging

import httpx

from src.domain.exceptions import DocumentExtractionError, UnsupportedFileFormatError
from src.domain.ports.document_extractor import DocumentExtractorPort, ExtractedTable

logger = logging.getLogger(__name__)

_POLL_INTERVAL_SECONDS = 2
_MAX_POLL_ATTEMPTS = 30

_CONTENT_TYPE_MAP = {
    ".pdf": "application/pdf",
    ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
}


class AzureDocumentExtractor(DocumentExtractorPort):
    """Extracts document structure using Azure Document Intelligence prebuilt-layout model.

    This adapter implements DocumentExtractorPort using the Azure cloud service.
    It produces the same ExtractedTable output as the local extractors so that
    the LLM mapper and application layer require no changes between environments.

    Args:
        endpoint: Azure Document Intelligence resource endpoint URL.
        key: Azure Document Intelligence API subscription key.
    """

    def __init__(self, endpoint: str, key: str) -> None:
        self._endpoint = endpoint.rstrip("/")
        self._key = key

    async def extract(self, file_bytes: bytes, filename: str) -> list[ExtractedTable]:
        """Extract document content using Azure Document Intelligence.

        Args:
            file_bytes: Raw document bytes.
            filename: Original filename used to determine the content type.

        Returns:
            A list of ExtractedTable instances reconstructed from Azure's
            table cell response.

        Raises:
            UnsupportedFileFormatError: If the file extension is not PDF or XLSX.
            DocumentExtractionError: If the Azure API call fails or times out.
        """
        content_type = self._resolve_content_type(filename)
        operation_url = await self._submit_document(file_bytes, content_type)
        result = await self._poll_operation(operation_url)
        return self._build_tables(result)

    def _resolve_content_type(self, filename: str) -> str:
        """Map a filename extension to its Azure API content type string.

        Args:
            filename: The document filename with extension.

        Returns:
            MIME type string expected by the Azure API.

        Raises:
            UnsupportedFileFormatError: If the extension is not supported.
        """
        suffix = filename.lower().rsplit(".", 1)[-1]
        suffix = f".{suffix}"
        if suffix not in _CONTENT_TYPE_MAP:
            raise UnsupportedFileFormatError(
                f"Azure extractor does not support file format: {suffix}",
                detail={"filename": filename},
            )
        return _CONTENT_TYPE_MAP[suffix]

    async def _submit_document(self, file_bytes: bytes, content_type: str) -> str:
        """Submit the document to Azure Document Intelligence for analysis.

        Args:
            file_bytes: Raw document bytes.
            content_type: MIME type of the document.

        Returns:
            The Operation-Location URL for polling the analysis result.

        Raises:
            DocumentExtractionError: If the submission request fails.
        """
        url = (
            f"{self._endpoint}/documentintelligence/documentModels/"
            f"prebuilt-layout:analyze?api-version=2024-02-29-preview"
        )
        headers = {
            "Ocp-Apim-Subscription-Key": self._key,
            "Content-Type": content_type,
        }
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, content=file_bytes, headers=headers)

        if response.status_code != 202:
            raise DocumentExtractionError(
                f"Azure Document Intelligence submission failed with status {response.status_code}.",
                detail={"status_code": response.status_code, "body": response.text[:500]},
            )

        operation_url = response.headers.get("Operation-Location", "")
        if not operation_url:
            raise DocumentExtractionError("Azure API response missing Operation-Location header.")

        return operation_url

    async def _poll_operation(self, operation_url: str) -> dict:
        """Poll the operation URL until analysis completes or times out.

        Args:
            operation_url: The URL returned by the initial submission request.

        Returns:
            The analyzeResult dictionary from the completed operation.

        Raises:
            DocumentExtractionError: If the operation fails or exceeds the
                                     maximum polling attempts.
        """
        headers = {"Ocp-Apim-Subscription-Key": self._key}
        async with httpx.AsyncClient(timeout=30.0) as client:
            for attempt in range(_MAX_POLL_ATTEMPTS):
                await asyncio.sleep(_POLL_INTERVAL_SECONDS)
                response = await client.get(operation_url, headers=headers)
                data = response.json()
                status = data.get("status", "")

                if status == "succeeded":
                    return data.get("analyzeResult", {})
                if status == "failed":
                    raise DocumentExtractionError(
                        f"Azure Document Intelligence analysis failed: {data.get('error', {})}",
                        detail={"error": data.get("error", {})},
                    )
                logger.debug("Azure operation status '%s' — attempt %d/%d", status, attempt + 1, _MAX_POLL_ATTEMPTS)

        raise DocumentExtractionError(
            f"Azure Document Intelligence timed out after {_MAX_POLL_ATTEMPTS * _POLL_INTERVAL_SECONDS} seconds."
        )

    def _build_tables(self, analyze_result: dict) -> list[ExtractedTable]:
        """Convert Azure's analyzeResult tables into ExtractedTable instances.

        Azure returns tables as a flat list of cells with rowIndex and columnIndex.
        We reconstruct 2D grid matrices from these cells before extracting headers.

        Args:
            analyze_result: The analyzeResult dictionary from the Azure API response.

        Returns:
            List of ExtractedTable instances.
        """
        azure_tables = analyze_result.get("tables", [])
        results: list[ExtractedTable] = []

        for table_index, azure_table in enumerate(azure_tables):
            row_count = azure_table.get("rowCount", 0)
            col_count = azure_table.get("columnCount", 0)
            cells = azure_table.get("cells", [])

            grid = self._build_grid(row_count, col_count, cells)
            if not grid:
                continue

            headers = grid[0]
            rows = grid[1:]
            results.append(
                ExtractedTable(
                    headers=headers,
                    rows=rows,
                    sheet_name=f"table_{table_index + 1}",
                )
            )

        # Fall back to page text if no tables were found.
        if not results:
            results = self._extract_page_text(analyze_result)

        return results

    def _build_grid(
        self, row_count: int, col_count: int, cells: list[dict]
    ) -> list[list[str]]:
        """Reconstruct a 2D grid from Azure's flat cell list.

        Args:
            row_count: Total number of rows in the table.
            col_count: Total number of columns in the table.
            cells: List of cell dicts with rowIndex, columnIndex, content.

        Returns:
            A 2D list of strings representing the table grid.
        """
        grid: list[list[str]] = [[""] * col_count for _ in range(row_count)]
        for cell in cells:
            row_idx = cell.get("rowIndex", 0)
            col_idx = cell.get("columnIndex", 0)
            content = cell.get("content", "").strip()
            if row_idx < row_count and col_idx < col_count:
                grid[row_idx][col_idx] = content
        return grid

    def _extract_page_text(self, analyze_result: dict) -> list[ExtractedTable]:
        """Extract raw page text as fallback when no structured tables are found.

        Args:
            analyze_result: The analyzeResult from Azure.

        Returns:
            List of ExtractedTable instances with raw_text populated.
        """
        pages = analyze_result.get("pages", [])
        results: list[ExtractedTable] = []
        for page in pages:
            lines = page.get("lines", [])
            text = "\n".join(line.get("content", "") for line in lines)
            if text.strip():
                results.append(
                    ExtractedTable(
                        sheet_name=f"page_{page.get('pageNumber', 1)}",
                        raw_text=text.strip(),
                    )
                )
        return results
