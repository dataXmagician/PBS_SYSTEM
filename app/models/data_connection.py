"""
Data Connection Models - Veri Baglantilari

Dis kaynak sistemlerden (SAP OData, HANA DB, Excel/CSV/TXT, Parquet)
veri cekip PostgreSQL staging tablolarina yazmak icin kullanilir.
"""

import enum
import uuid
from sqlalchemy import (
    Column, Integer, String, Boolean, Text, DateTime, Enum, ForeignKey,
    UniqueConstraint, Index
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.base import BaseModel


# ============ Enums ============

class ConnectionType(str, enum.Enum):
    sap_odata = "sap_odata"
    hana_db = "hana_db"
    file_upload = "file_upload"


class SyncStatus(str, enum.Enum):
    pending = "pending"
    running = "running"
    success = "success"
    failed = "failed"


class ColumnDataType(str, enum.Enum):
    string = "string"
    integer = "integer"
    decimal = "decimal"
    boolean = "boolean"
    date = "date"
    datetime = "datetime"


class MappingTargetType(str, enum.Enum):
    master_data = "master_data"
    system_version = "system_version"
    system_period = "system_period"
    system_parameter = "system_parameter"
    budget_entry = "budget_entry"


# ============ Models ============

class DataConnection(BaseModel):
    """
    Veri baglantisi tanimi.
    SAP OData, HANA DB veya dosya yuklemesi icin baglanti bilgilerini tutar.
    """
    __tablename__ = "data_connections"

    id = Column(Integer, primary_key=True, autoincrement=True)
    uuid = Column(String(36), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))

    code = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(200), nullable=False)
    description = Column(String(500), nullable=True)

    connection_type = Column(
        Enum(ConnectionType, name="connectiontype", create_type=False),
        nullable=False
    )

    # Baglanti bilgileri
    host = Column(String(500), nullable=True)
    port = Column(Integer, nullable=True)
    database_name = Column(String(200), nullable=True)
    username = Column(String(200), nullable=True)
    password = Column(String(500), nullable=True)  # TODO: Fernet ile sifreleme eklenecek

    # SAP OData spesifik
    sap_client = Column(String(10), nullable=True)
    sap_service_path = Column(String(500), nullable=True)

    # Genisletilebilir konfigurasyon
    extra_config = Column(JSONB, nullable=True)

    is_active = Column(Boolean, default=True, nullable=False)
    sort_order = Column(Integer, default=0)

    # Iliskiler
    queries = relationship(
        "DataConnectionQuery",
        back_populates="connection",
        cascade="all, delete-orphan",
        order_by="DataConnectionQuery.sort_order"
    )
    sync_logs = relationship(
        "DataSyncLog",
        back_populates="connection",
        cascade="all, delete-orphan",
        order_by="DataSyncLog.created_date.desc()"
    )

    def __repr__(self):
        return f"<DataConnection(code='{self.code}', type='{self.connection_type}')>"


class DataConnectionQuery(BaseModel):
    """
    Bir baglanti icin sorgu/veri kaynagi tanimi.
    HANA icin SQL sorgusu, SAP icin OData entity, dosya icin parse ayarlari.
    """
    __tablename__ = "data_connection_queries"
    __table_args__ = (
        UniqueConstraint('connection_id', 'code', name='uq_connection_query_code'),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    uuid = Column(String(36), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))

    connection_id = Column(
        Integer,
        ForeignKey("data_connections.id", ondelete="CASCADE"),
        nullable=False
    )

    code = Column(String(50), nullable=False)
    name = Column(String(200), nullable=False)
    description = Column(String(500), nullable=True)

    # HANA DB sorgusu
    query_text = Column(Text, nullable=True)

    # SAP OData ayarlari
    odata_entity = Column(String(500), nullable=True)
    odata_select = Column(String(1000), nullable=True)
    odata_filter = Column(String(1000), nullable=True)
    odata_top = Column(Integer, nullable=True)

    # Dosya parse ayarlari
    file_parse_config = Column(JSONB, nullable=True)

    # Staging tablo bilgileri
    staging_table_name = Column(String(100), nullable=True)
    staging_table_created = Column(Boolean, default=False, nullable=False)

    is_active = Column(Boolean, default=True, nullable=False)
    sort_order = Column(Integer, default=0)

    # Iliskiler
    connection = relationship("DataConnection", back_populates="queries")
    columns = relationship(
        "DataConnectionColumn",
        back_populates="query",
        cascade="all, delete-orphan",
        order_by="DataConnectionColumn.sort_order"
    )
    sync_logs = relationship(
        "DataSyncLog",
        back_populates="query"
    )
    mappings = relationship(
        "DataConnectionMapping",
        back_populates="query",
        cascade="all, delete-orphan",
        order_by="DataConnectionMapping.sort_order"
    )

    def __repr__(self):
        return f"<DataConnectionQuery(code='{self.code}', connection_id={self.connection_id})>"


class DataConnectionColumn(BaseModel):
    """
    Sorgu sonucundaki kolon tanimlari.
    Otomatik algilanir, kullanici tarafindan duzenlenebilir.
    Staging tablosu bu kolonlara gore olusturulur.
    """
    __tablename__ = "data_connection_columns"
    __table_args__ = (
        UniqueConstraint('query_id', 'target_name', name='uq_query_column_target'),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)

    query_id = Column(
        Integer,
        ForeignKey("data_connection_queries.id", ondelete="CASCADE"),
        nullable=False
    )

    source_name = Column(String(200), nullable=False)
    target_name = Column(String(200), nullable=False)

    data_type = Column(
        Enum(ColumnDataType, name="columndatatype", create_type=False),
        nullable=False,
        default=ColumnDataType.string
    )

    is_nullable = Column(Boolean, default=True, nullable=False)
    is_primary_key = Column(Boolean, default=False, nullable=False)
    is_included = Column(Boolean, default=True, nullable=False)
    max_length = Column(Integer, nullable=True)
    sort_order = Column(Integer, default=0)

    # Iliskiler
    query = relationship("DataConnectionQuery", back_populates="columns")

    def __repr__(self):
        return f"<DataConnectionColumn(source='{self.source_name}', target='{self.target_name}')>"


class DataSyncLog(BaseModel):
    """
    Senkronizasyon gecmisi.
    Her sync islemi icin bir kayit olusturulur.
    """
    __tablename__ = "data_sync_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    uuid = Column(String(36), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))

    connection_id = Column(
        Integer,
        ForeignKey("data_connections.id", ondelete="CASCADE"),
        nullable=False
    )
    query_id = Column(
        Integer,
        ForeignKey("data_connection_queries.id", ondelete="SET NULL"),
        nullable=True
    )

    status = Column(
        Enum(SyncStatus, name="syncstatus", create_type=False),
        nullable=False,
        default=SyncStatus.pending
    )

    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    total_rows = Column(Integer, nullable=True)
    inserted_rows = Column(Integer, nullable=True)
    error_message = Column(Text, nullable=True)
    triggered_by = Column(String(100), nullable=True)

    # Iliskiler
    connection = relationship("DataConnection", back_populates="sync_logs")
    query = relationship("DataConnectionQuery", back_populates="sync_logs")

    def __repr__(self):
        return f"<DataSyncLog(id={self.id}, status='{self.status}')>"


class DataConnectionMapping(BaseModel):
    """
    Staging tablosundan hedef tabloya veri aktarim tanimi.
    Bir sorgunun verisini hangi hedefe (master_data, system, budget) aktaracagini belirler.
    """
    __tablename__ = "data_connection_mappings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    uuid = Column(String(36), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))

    query_id = Column(
        Integer,
        ForeignKey("data_connection_queries.id", ondelete="CASCADE"),
        nullable=False
    )

    target_type = Column(
        Enum(MappingTargetType, name="mappingtargettype", create_type=False),
        nullable=False
    )

    # master_data hedefi icin: hangi MetaEntity'ye yazilacak
    target_entity_id = Column(Integer, nullable=True)

    name = Column(String(200), nullable=False)
    description = Column(String(500), nullable=True)

    is_active = Column(Boolean, default=True, nullable=False)
    sort_order = Column(Integer, default=0)

    # Iliskiler
    query = relationship("DataConnectionQuery", back_populates="mappings")
    field_mappings = relationship(
        "DataConnectionFieldMapping",
        back_populates="mapping",
        cascade="all, delete-orphan",
        order_by="DataConnectionFieldMapping.sort_order"
    )

    def __repr__(self):
        return f"<DataConnectionMapping(name='{self.name}', target='{self.target_type}')>"


class DataConnectionFieldMapping(BaseModel):
    """
    Tek bir alan eslestirmesi: staging kolonu -> hedef alan.
    Transform islemleri ve anahtar alan tanimlarini icerir.
    """
    __tablename__ = "data_connection_field_mappings"
    __table_args__ = (
        UniqueConstraint('mapping_id', 'target_field', name='uq_mapping_target_field'),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)

    mapping_id = Column(
        Integer,
        ForeignKey("data_connection_mappings.id", ondelete="CASCADE"),
        nullable=False
    )

    source_column = Column(String(200), nullable=False)
    target_field = Column(String(200), nullable=False)

    # Transform: none, uppercase, lowercase, trim, format_date, lookup
    transform_type = Column(String(50), nullable=True, default="none")
    transform_config = Column(JSONB, nullable=True)

    # Eslestirme anahtari (upsert icin)
    is_key_field = Column(Boolean, default=False, nullable=False)

    sort_order = Column(Integer, default=0)

    # Iliskiler
    mapping = relationship("DataConnectionMapping", back_populates="field_mappings")

    def __repr__(self):
        return f"<DataConnectionFieldMapping(source='{self.source_column}', target='{self.target_field}')>"
