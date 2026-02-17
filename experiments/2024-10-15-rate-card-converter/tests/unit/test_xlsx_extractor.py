"""Unit tests for the XLSXExtractor infrastructure adapter.

Tests verify:
- Single and multi-sheet workbooks are extracted correctly.
- Leading empty rows are skipped; the first non-empty row becomes headers.
- Rows where all cells are empty are filtered out.
- Invalid bytes (not XLSX) raise UnsupportedFileFormatError.
- Each sheet produces a separate ExtractedTable with the correct sheet_name.

Test workbooks are constructed in-memory using openpyxl to avoid external files.
"""

from __future__ import annotations

import io

import openpyxl
import pytest

from src.domain.exceptions import UnsupportedFileFormatError
from src.domain.ports.document_extractor import ExtractedTable
from src.infrastructure.extractors.xlsx_extractor import XLSXExtractor


@pytest.fixture
def extractor() -> XLSXExtractor:
    """Return an XLSXExtractor instance."""
    return XLSXExtractor()


def _make_xlsx_bytes(*sheets: tuple[str, list[list]]) -> bytes:
    """Build an in-memory XLSX file from sheet definitions.

    Args:
        sheets: Tuples of (sheet_name, rows) where rows is a list of row lists.

    Returns:
        Raw XLSX bytes.
    """
    wb = openpyxl.Workbook()
    for index, (sheet_name, rows) in enumerate(sheets):
        if index == 0:
            ws = wb.active
            ws.title = sheet_name
        else:
            ws = wb.create_sheet(sheet_name)
        for row in rows:
            ws.append(row)
    buffer = io.BytesIO()
    wb.save(buffer)
    return buffer.getvalue()


async def test_extract_single_sheet(
    extractor: XLSXExtractor, sample_xlsx_bytes: bytes
) -> None:
    """Extracting the fixture XLSX should return at least one ExtractedTable."""
    result = await extractor.extract(sample_xlsx_bytes, "sample.xlsx")
    assert isinstance(result, list)
    assert len(result) >= 1
    assert result[0].headers != []


async def test_extracted_headers_are_strings(
    extractor: XLSXExtractor, sample_xlsx_bytes: bytes
) -> None:
    """All headers must be strings after extraction."""
    result = await extractor.extract(sample_xlsx_bytes, "sample.xlsx")
    for table in result:
        for header in table.headers:
            assert isinstance(header, str)


async def test_extracted_rows_are_lists_of_strings(
    extractor: XLSXExtractor, sample_xlsx_bytes: bytes
) -> None:
    """All data row cells must be strings after extraction."""
    result = await extractor.extract(sample_xlsx_bytes, "sample.xlsx")
    for table in result:
        for row in table.rows:
            for cell in row:
                assert isinstance(cell, str)


async def test_extract_skips_leading_empty_rows(extractor: XLSXExtractor) -> None:
    """Leading empty rows before the header row must be ignored."""
    xlsx_bytes = _make_xlsx_bytes(
        ("Sheet1", [
            [],           # empty row - should be skipped
            [],           # empty row - should be skipped
            ["Origin", "Destination", "Rate"],
            ["US", "EU", "10.0"],
        ])
    )
    result = await extractor.extract(xlsx_bytes, "test.xlsx")
    assert len(result) == 1
    assert result[0].headers == ["Origin", "Destination", "Rate"]
    assert len(result[0].rows) == 1


async def test_extract_skips_empty_data_rows(extractor: XLSXExtractor) -> None:
    """Rows where all cells are empty strings must be filtered out."""
    xlsx_bytes = _make_xlsx_bytes(
        ("Sheet1", [
            ["Origin", "Destination", "Rate"],
            ["US", "EU", "10.0"],
            [None, None, None],   # all-empty row - should be filtered
            ["US", "APAC", "7.0"],
        ])
    )
    result = await extractor.extract(xlsx_bytes, "test.xlsx")
    assert len(result[0].rows) == 2


async def test_extract_raises_on_invalid_bytes(extractor: XLSXExtractor) -> None:
    """Non-XLSX bytes must raise UnsupportedFileFormatError."""
    with pytest.raises(UnsupportedFileFormatError) as exc_info:
        await extractor.extract(b"this is not an xlsx file", "bad.xlsx")
    assert "bad.xlsx" in exc_info.value.message


async def test_extract_multiple_sheets_produces_multiple_tables(
    extractor: XLSXExtractor,
) -> None:
    """A workbook with two non-empty sheets must produce two ExtractedTable instances."""
    xlsx_bytes = _make_xlsx_bytes(
        ("Rates", [
            ["From", "To", "Rate"],
            ["US", "EU", "10.0"],
        ]),
        ("Surcharges", [
            ["Name", "Pct"],
            ["Fuel", "5.5"],
        ]),
    )
    result = await extractor.extract(xlsx_bytes, "multi_sheet.xlsx")
    assert len(result) == 2
    sheet_names = {t.sheet_name for t in result}
    assert "Rates" in sheet_names
    assert "Surcharges" in sheet_names


async def test_extract_none_cells_become_empty_strings(extractor: XLSXExtractor) -> None:
    """Cells with None values must be converted to empty strings."""
    xlsx_bytes = _make_xlsx_bytes(
        ("Sheet1", [
            ["A", "B", "C"],
            ["val", None, "other"],
        ])
    )
    result = await extractor.extract(xlsx_bytes, "test.xlsx")
    assert result[0].rows[0][1] == ""
