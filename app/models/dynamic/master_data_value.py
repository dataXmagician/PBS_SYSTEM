"""
Master Data Value Model - Anaveri Alan Değerleri
"""

from sqlalchemy import Column, Integer, String, Text, ForeignKey, Index
from sqlalchemy.orm import relationship
from app.db.base import BaseModel


class MasterDataValue(BaseModel):
    __tablename__ = "master_data_values"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    master_data_id = Column(Integer, ForeignKey("master_data.id", ondelete="CASCADE"), nullable=False)
    attribute_id = Column(Integer, ForeignKey("meta_attributes.id", ondelete="CASCADE"), nullable=False)
    value = Column(Text, nullable=True)
    reference_id = Column(Integer, ForeignKey("master_data.id"), nullable=True)
    
    master_data = relationship("MasterData", foreign_keys=[master_data_id], back_populates="values")
    attribute = relationship("MetaAttribute", back_populates="values")
    reference = relationship("MasterData", foreign_keys=[reference_id])
    
    __table_args__ = (
        Index('ix_master_data_attribute', 'master_data_id', 'attribute_id', unique=True),
    )