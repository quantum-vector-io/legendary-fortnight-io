"""SQLAlchemy 2.0 ORM models for the Rate Card Converter application.

Design note on denormalization: The StandardizedRateCard is stored as a JSON
blob in the standardized_data column rather than being normalized into separate
rate_entries and surcharges tables. This is a deliberate trade-off for the
experiment context:

- Benefit: Simpler schema, no JOIN queries, easy to retrieve the full card.
- Trade-off: No SQL-level filtering on rate attributes (e.g. WHERE currency='USD').

For production use, individual RateEntry rows should be normalized into a
rate_entries table with foreign key to rate_cards.id to support filtering,
aggregation, and comparison queries.

The indexed metadata columns (carrier_name, source_format, source_filename)
on RateCardModel allow basic filtering without parsing the JSON blob.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, JSON, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Declarative base for all ORM models in this application."""


class JobModel(Base):
    """ORM model for the ProcessingJob entity.

    Maps to the 'jobs' table. Status transitions are the primary write
    pattern: a job is inserted once and then updated multiple times as
    processing progresses through the pipeline.
    """

    __tablename__ = "jobs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, comment="UUID4 identifier.")
    filename: Mapped[str] = mapped_column(String(512), nullable=False, comment="Original uploaded filename.")
    file_format: Mapped[str] = mapped_column(String(10), nullable=False, comment="Document format: pdf or xlsx.")
    status: Mapped[str] = mapped_column(String(20), nullable=False, comment="Job lifecycle status.")
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True, comment="Failure reason if status=failed.")
    rate_card_id: Mapped[str | None] = mapped_column(
        String(36), nullable=True, comment="ID of the resulting RateCard."
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)


class RateCardModel(Base):
    """ORM model for the RateCard persistence aggregate.

    Maps to the 'rate_cards' table. The full StandardizedRateCard value object
    is stored as JSON in standardized_data to avoid schema migrations when
    the rate card schema evolves. Indexed metadata columns support basic lookups.
    """

    __tablename__ = "rate_cards"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, comment="UUID4 identifier.")
    job_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True, comment="Parent job UUID.")
    carrier_name: Mapped[str] = mapped_column(String(256), nullable=False, index=True)
    carrier_code: Mapped[str | None] = mapped_column(String(50), nullable=True)
    source_format: Mapped[str] = mapped_column(String(10), nullable=False, comment="pdf or excel.")
    source_filename: Mapped[str] = mapped_column(String(512), nullable=False)
    standardized_data: Mapped[dict] = mapped_column(
        JSON, nullable=False, comment="Full StandardizedRateCard serialized as JSON."
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
