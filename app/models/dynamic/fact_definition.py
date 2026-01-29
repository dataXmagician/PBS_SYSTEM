"""
Fact Definition Model - Veri Giriş Şablonu Tanımları

Kullanıcının oluşturduğu veri giriş kombinasyonlarını tanımlar.
Örnek: Müşteri × Ürün × Tarih → Satış Miktarı, Satış Fiyatı
"""

from sqlalchemy import Column, Integer, String, Boolean, Text, ForeignKey
from sqlalchemy.orm import relationship
from app.db.base import BaseModel
import uuid


class FactDefinition(BaseModel):
    """
    Fact (veri giriş) tanımı.
    
    Örnek:
        - code: "SALES_BUDGET"
        - name: "Satış Bütçesi"
        - dimensions: [Müşteri, Ürün, Tarih]
        - measures: [Miktar, Fiyat, Tutar]
    """
    __tablename__ = "fact_definitions"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    uuid = Column(String(36), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
    
    # Tanımlayıcı kod
    code = Column(String(50), unique=True, nullable=False, index=True)
    
    # İsim
    name = Column(String(100), nullable=False)
    
    # Açıklama
    description = Column(Text, nullable=True)
    
    # Aktif mi?
    is_active = Column(Boolean, default=True)
    
    # Tarih boyutu dahil mi?
    include_time_dimension = Column(Boolean, default=True)
    
    # Tarih granülaritesi (day, week, month, quarter, year)
    time_granularity = Column(String(20), default="month")
    
    # İlişkiler
    dimensions = relationship("FactDimension", back_populates="fact_definition", cascade="all, delete-orphan")
    measures = relationship("FactMeasure", back_populates="fact_definition", cascade="all, delete-orphan")
    data = relationship("FactData", back_populates="fact_definition", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<FactDefinition(code='{self.code}', name='{self.name}')>"


class FactDimension(BaseModel):
    """
    Fact boyut ilişkisi.
    
    Bir fact hangi anaverilerden oluşuyor?
    """
    __tablename__ = "fact_dimensions"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Hangi fact tanımına ait?
    fact_definition_id = Column(Integer, ForeignKey("fact_definitions.id", ondelete="CASCADE"), nullable=False)
    
    # Hangi anaveri tipi?
    entity_id = Column(Integer, ForeignKey("meta_entities.id"), nullable=False)
    
    # Sıralama (UI'da gösterim sırası)
    sort_order = Column(Integer, default=0)
    
    # Zorunlu mu?
    is_required = Column(Boolean, default=True)
    
    # İlişkiler
    fact_definition = relationship("FactDefinition", back_populates="dimensions")
    entity = relationship("MetaEntity")
    
    def __repr__(self):
        return f"<FactDimension(fact_id={self.fact_definition_id}, entity_id={self.entity_id})>"
