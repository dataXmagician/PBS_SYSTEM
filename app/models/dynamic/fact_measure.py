"""
Fact Measure Model - Ölçü Değer Tanımları

Her fact için girilecek sayısal değerleri tanımlar.
Örnek: Miktar, Birim Fiyat, Tutar, İskonto %...
"""

from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Enum
from sqlalchemy.orm import relationship
from app.db.base import BaseModel
import enum


class MeasureType(enum.Enum):
    """Ölçü tipleri"""
    INTEGER = "integer"       # Tam sayı
    DECIMAL = "decimal"       # Ondalıklı sayı
    CURRENCY = "currency"     # Para birimi
    PERCENTAGE = "percentage" # Yüzde


class AggregationType(enum.Enum):
    """Toplama yöntemleri"""
    SUM = "sum"         # Toplam
    AVG = "avg"         # Ortalama
    MIN = "min"         # Minimum
    MAX = "max"         # Maximum
    COUNT = "count"     # Sayım
    LAST = "last"       # Son değer


class FactMeasure(BaseModel):
    """
    Ölçü değer tanımı.
    
    Örnek:
        - code: "QUANTITY"
        - name: "Miktar"
        - measure_type: INTEGER
        - aggregation: SUM
    """
    __tablename__ = "fact_measures"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Hangi fact tanımına ait?
    fact_definition_id = Column(Integer, ForeignKey("fact_definitions.id", ondelete="CASCADE"), nullable=False)
    
    # Ölçü kodu
    code = Column(String(50), nullable=False)
    
    # Ölçü adı
    name = Column(String(100), nullable=False)
    
    # Veri tipi
    measure_type = Column(Enum(MeasureType), default=MeasureType.DECIMAL)
    
    # Toplama yöntemi
    aggregation = Column(Enum(AggregationType), default=AggregationType.SUM)
    
    # Ondalık basamak sayısı
    decimal_places = Column(Integer, default=2)
    
    # Birim (adet, kg, TL, USD...)
    unit = Column(String(20), nullable=True)
    
    # Varsayılan değer
    default_value = Column(String(50), default="0")
    
    # Zorunlu mu?
    is_required = Column(Boolean, default=False)
    
    # Hesaplanmış alan mı? (formülle)
    is_calculated = Column(Boolean, default=False)
    
    # Hesaplama formülü (is_calculated=True ise)
    formula = Column(String(500), nullable=True)  # Örn: "QUANTITY * UNIT_PRICE"
    
    # Sıralama
    sort_order = Column(Integer, default=0)
    
    # Aktif mi?
    is_active = Column(Boolean, default=True)
    
    # İlişkiler
    fact_definition = relationship("FactDefinition", back_populates="measures")
    
    def __repr__(self):
        return f"<FactMeasure(code='{self.code}', name='{self.name}')>"
