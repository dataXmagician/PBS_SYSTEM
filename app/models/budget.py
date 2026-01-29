"""
Budget Model - Bütçe Ana Kaydı
"""

from sqlalchemy import Column, String, Numeric, DateTime, func, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from app.db.base import Base

class Budget(Base):
    """
    Bütçe ana kaydı - Her şirket ve mali yıl için bir bütçe
    """
    __tablename__ = "budgets"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False, index=True)
    fiscal_year = Column(String(4), nullable=False, comment="Mali Yıl (2024, 2025 vb)")
    budget_version = Column(String(20), nullable=False, comment="Bütçe Versiyonu (v1.0, v1.1 vb)")
    description = Column(Text, comment="Bütçe Açıklaması")
    total_amount = Column(Numeric(15, 2), default=0, comment="Toplam Bütçe Tutarı")
    currency = Column(String(3), default="USD", comment="Para Birimi")
    status = Column(String(20), default="DRAFT", comment="Durum: DRAFT, APPROVED, LOCKED, ARCHIVED")
    created_by = Column(String(100), comment="Oluşturan Kullanıcı")
    approved_by = Column(String(100), comment="Onaylayan Kullanıcı")
    created_date = Column(DateTime, default=func.now(), nullable=False)
    updated_date = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    company = relationship("Company", backref="budgets")
    budget_lines = relationship("BudgetLine", back_populates="budget", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Budget(id={self.id}, fiscal_year={self.fiscal_year}, version={self.budget_version})>"
