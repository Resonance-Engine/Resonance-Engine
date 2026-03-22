"""SQLAlchemy ORM models — database table definitions."""

from datetime import datetime

from sqlalchemy import Column, DateTime, Float, Index, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


class EventModel(Base):
    """Events table — stores all ingested events."""

    __tablename__ = "events"

    event_id = Column(String, primary_key=True)
    timestamp = Column(DateTime(timezone=True), nullable=False, index=True)
    source = Column(String, nullable=False)
    url = Column(Text, nullable=False)
    raw_text = Column(Text, nullable=False)
    content_hash = Column(String(16), nullable=False, index=True)
    entities = Column(JSONB, default=list)
    event_type = Column(String, index=True)
    summary = Column(Text)
    confidence = Column(Float)
    metadata_ = Column("metadata", JSONB, default=dict)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    __table_args__ = (
        Index("ix_events_timestamp_desc", timestamp.desc()),
        Index("ix_events_entities_gin", entities, postgresql_using="gin"),
    )


class SignalModel(Base):
    """Signals table — stores all generated signals with evidence."""

    __tablename__ = "signals"

    signal_id = Column(String, primary_key=True)
    event_id = Column(String, nullable=False, index=True)
    timestamp = Column(DateTime(timezone=True), nullable=False, index=True)
    ticker = Column(String, nullable=False, index=True)
    signal_type = Column(String, nullable=False)
    signal_text = Column(Text, nullable=False)
    confidence = Column(Float, nullable=False)
    rationale = Column(Text, nullable=False)
    uncertainty = Column(Text, nullable=False)
    impact_window = Column(String, nullable=False)
    predicted_move = Column(Float)
    actual_move = Column(Float)
    evidence = Column(JSONB, default=list)
    citations = Column(JSONB, default=list)
    metadata_ = Column("metadata", JSONB, default=dict)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    __table_args__ = (
        Index("ix_signals_timestamp_desc", timestamp.desc()),
    )


class EntityModel(Base):
    """Entities table — canonical company/organization records."""

    __tablename__ = "entities"

    ticker = Column(String, primary_key=True)
    cik = Column(String, unique=True)
    name = Column(String, nullable=False)
    sic_code = Column(String)
    metadata_ = Column("metadata", JSONB, default=dict)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow)
