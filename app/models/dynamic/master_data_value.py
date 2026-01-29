"""
Master Data Value Model - Anaveri Alan Değerleri

Her anaveri kaydının dinamik alan değerlerini tutar (EAV pattern).
"""

from sqlalchemy import Column, Integer, String, Text, ForeignKey, Index
from sqlalchemy.orm import relationship
from app.db.base import BaseModel


class MasterDataValue(BaseModel):
    """
    Anaveri alan değeri.
    
    Örnek (M001-Acme için):
        - master_data_id: 1 (M001)
        - attribute_id: 3 (Sektör alanı)
        - value: "Otomotiv"
    """
    __tablename__ = "master_data_values"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Hangi anaveri kaydına ait?
    master_data_id = Column(Integer, ForeignKey("master_data.id", ondelete="CASCADE"), nullable=False)
    
    # Hangi alana ait?
    attribute_id = Column(Integer, ForeignKey("meta_attributes.id", ondelete="CASCADE"), nullable=False)
    
    # Değer (tüm tipler string olarak saklanır, uygulama katmanında dönüştürülür)
    value = Column(Text, nullable=True)
    
    # Referans değeri (REFERENCE tipi için - ilişkili master_data.id)
    reference_id = Column(Integer, ForeignKey("master_data.id"), nullable=True)
    
    # İlişkiler
    master_data = relationship("MasterData", back_populates="values", foreign_keys=[master_data_id])
    attribute = relationship("MetaAttribute", back_populates="values")
    reference = relationship("MasterData", foreign_keys=[reference_id])
    
    __table_args__ = (
        # Her kayıt için her alan sadece bir kez olabilir
        Index('ix_master_data_attribute', 'master_data_id', 'attribute_id', unique=True),
    )
    
    def __repr__(self):
        return f"<MasterDataValue(master_data_id={self.master_data_id}, attribute_id={self.attribute_id})>"
