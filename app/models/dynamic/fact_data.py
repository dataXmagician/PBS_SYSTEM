"""
Fact Data Model - Gerçek Veri Girişleri

Kullanıcının girdiği fact verilerini tutar.
Örnek: M001 × P001 × 2025-01 → Miktar:100, Fiyat:50
"""

from sqlalchemy import Column, Integer, String, ForeignKey, Index
from sqlalchemy.orm import relationship
from app.db.base import BaseModel
import uuid


class FactData(BaseModel):
    """
    Fact veri kaydı (header).
    
    Her satır bir boyut kombinasyonunu temsil eder.
    Ölçü değerleri FactDataValue'da tutulur.
    """
    __tablename__ = "fact_data"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    uuid = Column(String(36), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
    
    # Hangi fact tanımına ait?
    fact_definition_id = Column(Integer, ForeignKey("fact_definitions.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Boyut değerleri (JSON olarak tüm dimension_id:master_data_id çiftleri)
    # Örn: {"1": 5, "2": 12} -> entity_id:1 için master_data_id:5
    dimension_values = Column(String(500), nullable=False)  # JSON
    
    # Tarih boyutu (include_time_dimension=True ise)
    time_id = Column(Integer, ForeignKey("dim_time.id"), nullable=True, index=True)
    
    # Alternatif: Doğrudan tarih alanları (daha hızlı sorgular için)
    year = Column(Integer, nullable=True, index=True)
    month = Column(Integer, nullable=True, index=True)
    
    # Versiyon/Senaryo (Budget, Forecast, Actual...)
    version = Column(String(50), default="BUDGET", index=True)
    
    # İlişkiler
    fact_definition = relationship("FactDefinition", back_populates="data")
    time = relationship("DimTime")
    values = relationship("FactDataValue", back_populates="fact_data", cascade="all, delete-orphan")
    
    __table_args__ = (
        # Aynı kombinasyon tekrar edemez
        Index('ix_fact_data_combination', 'fact_definition_id', 'dimension_values', 'time_id', 'version'),
    )
    
    def __repr__(self):
        return f"<FactData(fact_id={self.fact_definition_id}, dims='{self.dimension_values}')>"


class FactDataValue(BaseModel):
    """
    Fact ölçü değeri.
    
    Her FactData kaydı için ölçü değerlerini tutar.
    """
    __tablename__ = "fact_data_values"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Hangi fact data kaydına ait?
    fact_data_id = Column(Integer, ForeignKey("fact_data.id", ondelete="CASCADE"), nullable=False)
    
    # Hangi ölçüye ait?
    measure_id = Column(Integer, ForeignKey("fact_measures.id", ondelete="CASCADE"), nullable=False)
    
    # Değer (string olarak saklanır)
    value = Column(String(50), nullable=True)
    
    # İlişkiler
    fact_data = relationship("FactData", back_populates="values")
    measure = relationship("FactMeasure")
    
    __table_args__ = (
        Index('ix_fact_data_measure', 'fact_data_id', 'measure_id', unique=True),
    )
    
    def __repr__(self):
        return f"<FactDataValue(measure_id={self.measure_id}, value='{self.value}')>"
