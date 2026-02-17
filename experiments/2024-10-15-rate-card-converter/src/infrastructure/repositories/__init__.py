"""Repository adapters implementing RateCardRepositoryPort and JobRepositoryPort.

Available adapters:
- SQLiteJobRepository / SQLiteRateCardRepository: Use SQLAlchemy async sessions
  with SQLite (local) or PostgreSQL (Azure) depending on DATABASE_URL.
- PostgresJobRepository / PostgresRateCardRepository: Structurally identical to
  the SQLite variants; kept separate for explicit Azure adapter identification.
"""
