"""Document extraction adapters implementing DocumentExtractorPort.

Available adapters:
- PDFExtractor: Uses pdfplumber for local PDF parsing.
- XLSXExtractor: Uses openpyxl for local Excel parsing.
- AzureDocumentExtractor: Uses Azure Document Intelligence REST API (production).
- LocalDocumentExtractorDispatcher: Routes to PDF or XLSX extractor by file extension.
"""
