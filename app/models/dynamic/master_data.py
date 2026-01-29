"""
Master Data Model - Anaveri Kayıtları
"""

from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from app.db.base import BaseModel
import uuid


class MasterData(BaseModel):
    __tablename__ = "master_data"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    uuid = Column(String(36), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
    entity_id = Column(Integer, ForeignKey("meta_entities.id", ondelete="CASCADE"), nullable=False, index=True)
    code = Column(String(50), nullable=False, index=True)
    name = Column(String(200), nullable=False)
    is_active = Column(Boolean, default=True)
    sort_order = Column(Integer, default=0)
    
    entity = relationship("MetaEntity", back_populates="master_data")
    values = relationship("MasterDataValue", foreign_keys="[MasterDataValue.master_data_id]", back_populates="master_data", cascade="all, delete-orphan")
    
    __table_args__ = (
        UniqueConstraint('entity_id', 'code', name='uq_entity_code'),
    )