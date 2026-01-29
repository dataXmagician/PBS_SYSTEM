"""
Meta Translation Model - Çoklu Dil Desteği

Anaveri tipleri ve alanları için çeviri desteği sağlar.
"""

from sqlalchemy import Column, Integer, String, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from app.db.base import BaseModel


class MetaTranslation(BaseModel):
    """
    Çeviri kayıtları.
    
    Örnek:
        - entity_id: 1 (Müşteri)
        - language_code: "en"
        - translated_name: "Customer"
    """
    __tablename__ = "meta_translations"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Hangi anaveri tipi? (entity veya attribute'dan biri dolu olmalı)
    entity_id = Column(Integer, ForeignKey("meta_entities.id", ondelete="CASCADE"), nullable=True)
    
    # Hangi alan?
    attribute_id = Column(Integer, ForeignKey("meta_attributes.id", ondelete="CASCADE"), nullable=True)
    
    # Dil kodu (tr, en, de, fr...)
    language_code = Column(String(5), nullable=False, index=True)
    
    # Çevrilmiş isim/etiket
    translated_name = Column(String(100), nullable=False)
    
    # Çevrilmiş açıklama
    translated_description = Column(String(500), nullable=True)
    
    # İlişkiler
    entity = relationship("MetaEntity", back_populates="translations")
    attribute = relationship("MetaAttribute", back_populates="translations")
    
    __table_args__ = (
        # Aynı entity+dil kombinasyonu tekrar edemez
        UniqueConstraint('entity_id', 'language_code', name='uq_entity_language'),
        # Aynı attribute+dil kombinasyonu tekrar edemez  
        UniqueConstraint('attribute_id', 'language_code', name='uq_attribute_language'),
    )
    
    def __repr__(self):
        return f"<MetaTranslation(lang='{self.language_code}', name='{self.translated_name}')>"
