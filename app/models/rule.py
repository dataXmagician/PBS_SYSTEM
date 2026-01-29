"""
Rule Model - Otomatik Hesaplama Kuralları
"""

from sqlalchemy import Column, String, Numeric, DateTime, func, ForeignKey, Text, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from app.db.base import Base

class CalculationRule(Base):
    """
    Bütçe satırları için otomatik hesaplama kuralları
    """
    __tablename__ = "calculation_rules"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False, index=True)
    rule_name = Column(String(100), nullable=False, comment="Kuralın Adı")
    rule_type = Column(String(50), nullable=False, comment="Kural Tipi (PERCENTAGE, FORMULA, THRESHOLD)")
    
    # Rule Tanımı
    description = Column(Text, comment="Kuralın Açıklaması")
    condition = Column(String(500), comment="Koşul (örn: revised_amount > 100000)")
    action = Column(String(500), nullable=False, comment="İşlem (örn: revised_amount * 1.1)")
    
    # Parametreler
    percentage_value = Column(Numeric(5, 2), comment="Yüzde değeri (% tipi için)")
    threshold_amount = Column(Numeric(15, 2), comment="Eşik tutarı")
    
    # Kontrol
    is_active = Column(Boolean, default=True, comment="Aktif mi?")
    apply_automatically = Column(Boolean, default=True, comment="Otomatik uygula?")
    requires_approval = Column(Boolean, default=False, comment="Onay gerekli mi?")
    
    # Metadata
    created_by = Column(String(100), comment="Oluşturan")
    created_date = Column(DateTime, default=func.now(), nullable=False)
    updated_date = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    company = relationship("Company")
    
    def __repr__(self):
        return f"<CalculationRule(id={self.id}, name={self.rule_name}, type={self.rule_type})>"
