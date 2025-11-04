from sqlalchemy import (
    Column, Integer, String, Float, Date, DateTime, Boolean, Text, ForeignKey, UniqueConstraint, CheckConstraint
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base


class DimMO(Base):
    __tablename__ = "dim_mo"

    mo_id = Column(Integer, primary_key=True)
    mo_name = Column(String(255), nullable=False, unique=True)
    oktmo = Column(String(11))
    okato = Column(String(5))
    lat = Column(Float)
    lon = Column(Float)
    geojson_id = Column(String(50))
    population = Column(Integer)
    area_km2 = Column(Float)
    type = Column(String(50))
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # Relationships
    indicators = relationship("FactIndicator", back_populates="mo")
    penalties = relationship("FactPenalty", back_populates="mo")
    events = relationship("FactEvent", back_populates="mo")
    summaries = relationship("FactSummary", back_populates="mo")


class DimPeriod(Base):
    __tablename__ = "dim_period"

    period_id = Column(Integer, primary_key=True)
    period_type = Column(String(20), nullable=False)  # 'month', 'halfyear', 'year'
    date_from = Column(Date, nullable=False)
    date_to = Column(Date, nullable=False)
    edg_flag = Column(Boolean, default=False)
    created_at = Column(DateTime, server_default=func.now())

    # Relationships
    indicators = relationship("FactIndicator", back_populates="period")
    penalties = relationship("FactPenalty", back_populates="period")
    events = relationship("FactEvent", back_populates="period")
    summaries = relationship("FactSummary", back_populates="period")


class DimIndicator(Base):
    __tablename__ = "dim_indicator"

    ind_id = Column(Integer, primary_key=True)
    code = Column(String(50), nullable=False, unique=True)
    name = Column(String(255), nullable=False)
    block = Column(String(100))
    description = Column(Text)
    unit = Column(String(50))
    is_public = Column(Boolean, default=True)
    owner_org = Column(String(100))
    weight = Column(Float)
    min_value = Column(Float)
    max_value = Column(Float)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # Relationships
    facts = relationship("FactIndicator", back_populates="indicator")


class DimPenalty(Base):
    __tablename__ = "dim_penalty"

    pen_id = Column(Integer, primary_key=True)
    code = Column(String(50), nullable=False, unique=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    owner_org = Column(String(100))
    created_at = Column(DateTime, server_default=func.now())

    # Relationships
    facts = relationship("FactPenalty", back_populates="penalty")


class DimMethodology(Base):
    __tablename__ = "dim_methodology"

    version_id = Column(Integer, primary_key=True)
    version = Column(String(20), nullable=False, unique=True)
    valid_from = Column(Date, nullable=False)
    valid_to = Column(Date)
    notes = Column(Text)
    created_at = Column(DateTime, server_default=func.now())


class MapScale(Base):
    __tablename__ = "map_scale"

    scale_id = Column(Integer, primary_key=True)
    version_id = Column(Integer, ForeignKey("dim_methodology.version_id"), nullable=False)
    ind_id = Column(Integer, ForeignKey("dim_indicator.ind_id"))
    pen_id = Column(Integer, ForeignKey("dim_penalty.pen_id"))
    zone = Column(String(20))  # 'green', 'yellow', 'red'
    min_score = Column(Float)
    max_score = Column(Float)
    color_hex = Column(String(7))
    created_at = Column(DateTime, server_default=func.now())


class SrcRegistry(Base):
    __tablename__ = "src_registry"

    source_id = Column(Integer, primary_key=True)
    code = Column(String(50), nullable=False, unique=True)
    org = Column(String(100), nullable=False)
    contact = Column(String(255))
    channel = Column(String(50))  # 'API', 'SFTP', 'Excel', 'Manual'
    schedule = Column(String(100))
    format = Column(String(50))
    notes = Column(Text)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class FactIndicator(Base):
    __tablename__ = "fact_indicator"
    __table_args__ = (
        UniqueConstraint('mo_id', 'period_id', 'ind_id', 'version_id', name='uq_fact_indicator'),
    )

    fact_ind_id = Column(Integer, primary_key=True)
    mo_id = Column(Integer, ForeignKey("dim_mo.mo_id"), nullable=False)
    period_id = Column(Integer, ForeignKey("dim_period.period_id"), nullable=False)
    ind_id = Column(Integer, ForeignKey("dim_indicator.ind_id"), nullable=False)
    version_id = Column(Integer, ForeignKey("dim_methodology.version_id"), nullable=False)
    value_raw = Column(Float)
    value_norm = Column(Float)  # нормализованное значение (0-100)
    score = Column(Float)
    target = Column(Float)
    source_id = Column(Integer, ForeignKey("src_registry.source_id"))
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # Relationships
    mo = relationship("DimMO", back_populates="indicators")
    period = relationship("DimPeriod", back_populates="indicators")
    indicator = relationship("DimIndicator", back_populates="facts")


class FactPenalty(Base):
    __tablename__ = "fact_penalty"

    fact_pen_id = Column(Integer, primary_key=True)
    mo_id = Column(Integer, ForeignKey("dim_mo.mo_id"), nullable=False)
    period_id = Column(Integer, ForeignKey("dim_period.period_id"), nullable=False)
    pen_id = Column(Integer, ForeignKey("dim_penalty.pen_id"), nullable=False)
    version_id = Column(Integer, ForeignKey("dim_methodology.version_id"), nullable=False)
    score_negative = Column(Float)
    details = Column(Text)
    source_id = Column(Integer, ForeignKey("src_registry.source_id"))
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # Relationships
    mo = relationship("DimMO", back_populates="penalties")
    period = relationship("DimPeriod", back_populates="penalties")
    penalty = relationship("DimPenalty", back_populates="facts")


class FactEvent(Base):
    __tablename__ = "fact_events"

    event_id = Column(Integer, primary_key=True)
    mo_id = Column(Integer, ForeignKey("dim_mo.mo_id"), nullable=False)
    event_date = Column(Date, nullable=False)
    event_type = Column(String(50))
    title = Column(String(255))
    description = Column(Text)
    link = Column(String(500))
    source_id = Column(Integer, ForeignKey("src_registry.source_id"))
    created_at = Column(DateTime, server_default=func.now())

    # Relationships
    mo = relationship("DimMO", back_populates="events")
    period = relationship("DimPeriod", back_populates="events", foreign_keys="")


class FactSummary(Base):
    __tablename__ = "fact_summary"
    __table_args__ = (
        UniqueConstraint('mo_id', 'period_id', 'version_id', name='uq_fact_summary'),
    )

    summary_id = Column(Integer, primary_key=True)
    mo_id = Column(Integer, ForeignKey("dim_mo.mo_id"), nullable=False)
    period_id = Column(Integer, ForeignKey("dim_period.period_id"), nullable=False)
    version_id = Column(Integer, ForeignKey("dim_methodology.version_id"), nullable=False)
    score_public = Column(Float)
    score_closed = Column(Float)
    score_penalties = Column(Float)
    score_total = Column(Float)
    zone = Column(String(20))
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # Relationships
    mo = relationship("DimMO", back_populates="summaries")
    period = relationship("DimPeriod", back_populates="summaries")


class AuditLog(Base):
    __tablename__ = "audit_log"

    log_id = Column(Integer, primary_key=True)
    actor_id = Column(Integer)
    action = Column(String(50))
    entity = Column(String(100))
    entity_id = Column(Integer)
    old_value = Column(Text)
    new_value = Column(Text)
    ts = Column(DateTime, server_default=func.now())


class UploadLog(Base):
    __tablename__ = "upload_log"

    upload_id = Column(Integer, primary_key=True)
    source_id = Column(Integer, ForeignKey("src_registry.source_id"))
    file_name = Column(String(255))
    file_hash = Column(String(64))
    records_count = Column(Integer)
    status = Column(String(50))  # 'pending', 'processing', 'success', 'error'
    error_message = Column(Text)
    uploaded_at = Column(DateTime, server_default=func.now())
    processed_at = Column(DateTime)


class DataQualityFlag(Base):
    __tablename__ = "data_quality_flags"

    flag_id = Column(Integer, primary_key=True)
    mo_id = Column(Integer, ForeignKey("dim_mo.mo_id"))
    period_id = Column(Integer, ForeignKey("dim_period.period_id"))
    ind_id = Column(Integer, ForeignKey("dim_indicator.ind_id"))
    flag_type = Column(String(50))  # 'anomaly', 'missing', 'inconsistent'
    severity = Column(String(20))  # 'info', 'warning', 'error'
    message = Column(Text)
    created_at = Column(DateTime, server_default=func.now())
