"""
DWH (Data Warehouse) Models - Veri Ambarı

Staging tablolarından DWH katmanına veri aktarımı,
zamanlama ve hedef sistem eşlemeleri için kullanılır.
"""

import enum
import uuid as uuid_lib
from sqlalchemy import (
    Column, Integer, String, Boolean, Text, DateTime, Enum, ForeignKey,
    UniqueConstraint
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.base import BaseModel
from app.models.data_connection import ColumnDataType, MappingTargetType


# ============ Enums ============

class DwhTableSourceType(str, enum.Enum):
    staging_copy = "staging_copy"
    custom = "custom"
    staging_modified = "staging_modified"


class DwhLoadStrategy(str, enum.Enum):
    full = "full"
    incremental = "incremental"
    append = "append"


class DwhTransferStatus(str, enum.Enum):
    pending = "pending"
    running = "running"
    success = "success"
    failed = "failed"


class DwhScheduleFrequency(str, enum.Enum):
    manual = "manual"
    hourly = "hourly"
    daily = "daily"
    weekly = "weekly"
    monthly = "monthly"
    cron = "cron"


# ============ Models ============

class DwhTable(BaseModel):
    """
    DWH tablo tanımı.
    Staging'den kopyalanmış, kullanıcı tanımlı veya değiştirilmiş yapıda olabilir.
    """
    __tablename__ = "dwh_tables"

    id = Column(Integer, primary_key=True, autoincrement=True)
    uuid = Column(String(36), unique=True, nullable=False, default=lambda: str(uuid_lib.uuid4()))

    code = Column(String(100), unique=True, nullable=False, index=True)
    name = Column(String(200), nullable=False)
    description = Column(String(500), nullable=True)

    source_type = Column(
        Enum(DwhTableSourceType, name="dwhtablesourcetype", create_type=False),
        nullable=False
    )

    # Staging'den kopyalandıysa kaynak sorgu
    source_query_id = Column(
        Integer,
        ForeignKey("data_connection_queries.id", ondelete="SET NULL"),
        nullable=True
    )

    # Fiziksel PostgreSQL tablo adı (dwh_{code})
    table_name = Column(String(100), nullable=False, unique=True)
    table_created = Column(Boolean, default=False, nullable=False)

    is_active = Column(Boolean, default=True, nullable=False)
    sort_order = Column(Integer, default=0)

    # İlişkiler
    source_query = relationship("DataConnectionQuery")
    columns = relationship(
        "DwhColumn",
        back_populates="dwh_table",
        cascade="all, delete-orphan",
        order_by="DwhColumn.sort_order"
    )
    transfers = relationship(
        "DwhTransfer",
        back_populates="dwh_table",
        cascade="all, delete-orphan",
        order_by="DwhTransfer.sort_order"
    )
    mappings = relationship(
        "DwhMapping",
        back_populates="dwh_table",
        cascade="all, delete-orphan",
        order_by="DwhMapping.sort_order"
    )

    def __repr__(self):
        return f"<DwhTable(code='{self.code}', table='{self.table_name}')>"


class DwhColumn(BaseModel):
    """
    DWH tablo kolon tanımları.
    columndatatype enum'unu yeniden kullanır (data_connection'dan).
    """
    __tablename__ = "dwh_columns"
    __table_args__ = (
        UniqueConstraint('dwh_table_id', 'column_name', name='uq_dwh_table_column'),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)

    dwh_table_id = Column(
        Integer,
        ForeignKey("dwh_tables.id", ondelete="CASCADE"),
        nullable=False
    )

    column_name = Column(String(200), nullable=False)
    data_type = Column(
        Enum(ColumnDataType, name="columndatatype", create_type=False),
        nullable=False,
        default=ColumnDataType.string
    )
    is_nullable = Column(Boolean, default=True, nullable=False)
    is_primary_key = Column(Boolean, default=False, nullable=False)
    is_incremental_key = Column(Boolean, default=False, nullable=False)
    max_length = Column(Integer, nullable=True)
    sort_order = Column(Integer, default=0)

    # İlişkiler
    dwh_table = relationship("DwhTable", back_populates="columns")

    def __repr__(self):
        return f"<DwhColumn(name='{self.column_name}', type='{self.data_type}')>"


class DwhTransfer(BaseModel):
    """
    Staging → DWH aktarım tanımı.
    Yükleme stratejisi, artımlı kolon ve kolon eşlemesi bilgilerini tutar.
    """
    __tablename__ = "dwh_transfers"

    id = Column(Integer, primary_key=True, autoincrement=True)
    uuid = Column(String(36), unique=True, nullable=False, default=lambda: str(uuid_lib.uuid4()))

    dwh_table_id = Column(
        Integer,
        ForeignKey("dwh_tables.id", ondelete="CASCADE"),
        nullable=False
    )

    # Kaynak staging sorgusu
    source_query_id = Column(
        Integer,
        ForeignKey("data_connection_queries.id", ondelete="SET NULL"),
        nullable=True
    )

    name = Column(String(200), nullable=False)
    description = Column(String(500), nullable=True)

    # Yükleme stratejisi
    load_strategy = Column(
        Enum(DwhLoadStrategy, name="dwhloadstrategy", create_type=False),
        nullable=False,
        default=DwhLoadStrategy.full
    )

    # Artımlı yükleme için kolon adı ve son değer
    incremental_column = Column(String(200), nullable=True)
    last_incremental_value = Column(String(500), nullable=True)

    # Kolon eşlemesi: {staging_kolon: dwh_kolon}, null ise 1:1
    column_mapping = Column(JSONB, nullable=True)

    is_active = Column(Boolean, default=True, nullable=False)
    sort_order = Column(Integer, default=0)

    # İlişkiler
    dwh_table = relationship("DwhTable", back_populates="transfers")
    source_query = relationship("DataConnectionQuery")
    schedule = relationship(
        "DwhSchedule",
        back_populates="transfer",
        uselist=False,
        cascade="all, delete-orphan"
    )
    logs = relationship(
        "DwhTransferLog",
        back_populates="transfer",
        cascade="all, delete-orphan",
        order_by="DwhTransferLog.created_date.desc()"
    )

    def __repr__(self):
        return f"<DwhTransfer(name='{self.name}', strategy='{self.load_strategy}')>"


class DwhSchedule(BaseModel):
    """
    DWH transfer zamanlaması.
    Her transfer'ın en fazla bir zamanlaması olabilir (1:1).
    """
    __tablename__ = "dwh_schedules"

    id = Column(Integer, primary_key=True, autoincrement=True)

    transfer_id = Column(
        Integer,
        ForeignKey("dwh_transfers.id", ondelete="CASCADE"),
        nullable=False,
        unique=True
    )

    frequency = Column(
        Enum(DwhScheduleFrequency, name="dwhschedulefrequency", create_type=False),
        nullable=False,
        default=DwhScheduleFrequency.manual
    )

    # Cron ifadesi (frequency=cron olduğunda)
    cron_expression = Column(String(100), nullable=True)

    # Basit zamanlama alanları
    hour = Column(Integer, nullable=True)          # 0-23
    minute = Column(Integer, default=0)             # 0-59
    day_of_week = Column(Integer, nullable=True)    # 0-6 (0=Pazartesi)
    day_of_month = Column(Integer, nullable=True)   # 1-31

    is_enabled = Column(Boolean, default=False, nullable=False)
    last_run_at = Column(DateTime, nullable=True)
    next_run_at = Column(DateTime, nullable=True)

    # İlişkiler
    transfer = relationship("DwhTransfer", back_populates="schedule")

    def __repr__(self):
        return f"<DwhSchedule(transfer_id={self.transfer_id}, freq='{self.frequency}')>"


class DwhTransferLog(BaseModel):
    """
    DWH transfer çalıştırma geçmişi.
    DataSyncLog pattern'ini takip eder.
    """
    __tablename__ = "dwh_transfer_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    uuid = Column(String(36), unique=True, nullable=False, default=lambda: str(uuid_lib.uuid4()))

    transfer_id = Column(
        Integer,
        ForeignKey("dwh_transfers.id", ondelete="CASCADE"),
        nullable=False
    )

    status = Column(
        Enum(DwhTransferStatus, name="dwhtransferstatus", create_type=False),
        nullable=False,
        default=DwhTransferStatus.pending
    )

    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)

    total_rows = Column(Integer, nullable=True)
    inserted_rows = Column(Integer, nullable=True)
    updated_rows = Column(Integer, nullable=True)
    deleted_rows = Column(Integer, nullable=True)

    error_message = Column(Text, nullable=True)
    triggered_by = Column(String(100), nullable=True)

    # İlişkiler
    transfer = relationship("DwhTransfer", back_populates="logs")

    def __repr__(self):
        return f"<DwhTransferLog(id={self.id}, status='{self.status}')>"


class DwhMapping(BaseModel):
    """
    DWH tablosundan hedef sisteme veri eşleme tanımı.
    Mevcut mappingtargettype enum'unu yeniden kullanır.
    """
    __tablename__ = "dwh_mappings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    uuid = Column(String(36), unique=True, nullable=False, default=lambda: str(uuid_lib.uuid4()))

    dwh_table_id = Column(
        Integer,
        ForeignKey("dwh_tables.id", ondelete="CASCADE"),
        nullable=False
    )

    target_type = Column(
        Enum(MappingTargetType, name="mappingtargettype", create_type=False),
        nullable=False
    )

    # Hedefe özel ID'ler
    target_entity_id = Column(Integer, nullable=True)       # master_data için MetaEntity ID
    target_definition_id = Column(Integer, nullable=True)    # budget_entry için BudgetDefinition ID
    target_version_id = Column(Integer, nullable=True)       # system versiyon/dönem için

    name = Column(String(200), nullable=False)
    description = Column(String(500), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    sort_order = Column(Integer, default=0)

    # İlişkiler
    dwh_table = relationship("DwhTable", back_populates="mappings")
    field_mappings = relationship(
        "DwhFieldMapping",
        back_populates="mapping",
        cascade="all, delete-orphan",
        order_by="DwhFieldMapping.sort_order"
    )

    def __repr__(self):
        return f"<DwhMapping(name='{self.name}', target='{self.target_type}')>"


class DwhFieldMapping(BaseModel):
    """
    DWH → hedef alan eşlemesi.
    DataConnectionFieldMapping pattern'ini takip eder.
    """
    __tablename__ = "dwh_field_mappings"
    __table_args__ = (
        UniqueConstraint('mapping_id', 'target_field', name='uq_dwh_mapping_target_field'),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)

    mapping_id = Column(
        Integer,
        ForeignKey("dwh_mappings.id", ondelete="CASCADE"),
        nullable=False
    )

    source_column = Column(String(200), nullable=False)
    target_field = Column(String(200), nullable=False)

    transform_type = Column(String(50), nullable=True, default="none")
    transform_config = Column(JSONB, nullable=True)

    is_key_field = Column(Boolean, default=False, nullable=False)
    sort_order = Column(Integer, default=0)

    # İlişkiler
    mapping = relationship("DwhMapping", back_populates="field_mappings")

    def __repr__(self):
        return f"<DwhFieldMapping(source='{self.source_column}', target='{self.target_field}')>"
