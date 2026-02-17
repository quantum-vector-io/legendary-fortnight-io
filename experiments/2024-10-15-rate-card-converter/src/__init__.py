"""Rate Card Converter - main package.

This package implements a document parsing pipeline that converts freight carrier
rate cards from heterogeneous formats (PDF, Excel) into a standardized canonical
schema using LLM-assisted semantic field mapping.

Architecture: Hexagonal (Ports and Adapters).
- domain/: Pure business logic and abstract port interfaces.
- application/: Use case orchestration, depends only on domain ports.
- infrastructure/: Concrete adapter implementations (pdfplumber, LangChain, SQLAlchemy).
- api/: FastAPI presentation layer.
- config/: Settings and dependency injection wiring.
"""
