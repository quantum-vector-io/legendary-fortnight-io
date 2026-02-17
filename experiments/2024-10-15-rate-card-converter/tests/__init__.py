"""Test suite for the Rate Card Converter application.

Tests are organized into two layers:
- unit/: Tests for individual components in isolation using mocks and in-memory fakes.
  No real database, file system, or API calls are made.
- integration/: Tests for the API layer using httpx.AsyncClient with all
  infrastructure dependencies overridden via FastAPI's dependency_overrides.

All tests use pytest-asyncio with asyncio_mode='auto' (configured in pyproject.toml),
which means async test functions do not require the @pytest.mark.asyncio decorator.
"""
