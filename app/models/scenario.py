"""
Scenario Model - Bütçe Senaryo Analizi
"""

from sqlalchemy import Column, String, Numeric, DateTime, func, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from app.db.base import Base

class Scenario(Base):
    """
    Bütçe senaryo analizi
    """
    __tablename__ = "scenarios"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    budget_id = Column(UUID(as_uuid=True), ForeignKey("budgets.id"), nullable=False, index=True)
    scenario_name = Column(String(100), nullable=False, comment="Senaryo Adı (Base, Optimistic, Pessimistic)")
    scenario_type = Column(String(50), nullable=False, comment="Senaryo Tipi")
    description = Column(Text, comment="Senaryo Açıklaması")
    adjustment_percentage = Column(Numeric(5, 2), default=0, comment="Ayarlama Yüzdesi")
    total_amount = Column(Numeric(15, 2), default=0, comment="Toplam Tutar")
    impact = Column(Numeric(15, 2), comment="Etki Tutarı")
    impact_percentage = Column(Numeric(5, 2), comment="Etki Yüzdesi")
    created_by = Column(String(100), comment="Oluşturan Kullanıcı")
    created_date = Column(DateTime, default=func.now(), nullable=False)
    
    # Relationships
    budget = relationship("Budget", backref="scenarios")
    
    def __repr__(self):
        return f"<Scenario(id={self.id}, name={self.scenario_name}, type={self.scenario_type})>"
