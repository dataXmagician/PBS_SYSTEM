"""
Meta Attribute Model - Anaveri Alan Tanımları
"""

from sqlalchemy import Column, Integer, String, Boolean, Text, ForeignKey, Enum
from sqlalchemy.orm import relationship
from app.db.base import BaseModel
import enum
import uuid


class AttributeType(enum.Enum):
    STRING = "string"
    INTEGER = "integer"
    DECIMAL = "decimal"
    BOOLEAN = "boolean"
    DATE = "date"
    DATETIME = "datetime"
    LIST = "list"
    REFERENCE = "reference"


class MetaAttribute(BaseModel):
    __tablename__ = "meta_attributes"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    uuid = Column(String(36), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
    entity_id = Column(Integer, ForeignKey("meta_entities.id", ondelete="CASCADE"), nullable=False)
    code = Column(String(50), nullable=False, index=True)
    default_label = Column(String(100), nullable=False)
    data_type = Column(
        Enum(
            'string', 'integer', 'decimal', 'boolean', 'date', 'datetime', 'list', 'reference',
            name='attributetype',
            create_type=False
        ),
        nullable=False,
        default='string'
    )
    options = Column(Text, nullable=True)
    reference_entity_id = Column(Integer, ForeignKey("meta_entities.id"), nullable=True)
    default_value = Column(String(255), nullable=True)
    is_required = Column(Boolean, default=False)
    is_unique = Column(Boolean, default=False)
    is_code_field = Column(Boolean, default=False)
    is_name_field = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    is_system = Column(Boolean, default=False)
    sort_order = Column(Integer, default=0)
    min_value = Column(String(50), nullable=True)
    max_value = Column(String(50), nullable=True)
    min_length = Column(Integer, nullable=True)
    max_length = Column(Integer, nullable=True)
    
    entity = relationship("MetaEntity", foreign_keys=[entity_id], back_populates="attributes")
    reference_entity = relationship("MetaEntity", foreign_keys=[reference_entity_id])
    translations = relationship("MetaTranslation", back_populates="attribute", cascade="all, delete-orphan")
    values = relationship("MasterDataValue", back_populates="attribute", cascade="all, delete-orphan")