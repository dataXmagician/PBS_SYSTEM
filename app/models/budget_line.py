"""
BudgetLine Model - Bütçe Detay Satırları
"""

from sqlalchemy import Column, String, Numeric, DateTime, func, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from app.db.base import Base

class BudgetLine(Base):
    """
    Bütçe detay satırı - Şirkete ait detay seviyesine göre oluşturulur
    PRODUCT: sadece material
    PRODUCT_CUSTOMER: material + customer
    PERIOD_ONLY: sadece dönem
    """
    __tablename__ = "budget_lines"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    budget_id = Column(UUID(as_uuid=True), ForeignKey("budgets.id"), nullable=False, index=True)
    period_id = Column(UUID(as_uuid=True), ForeignKey("periods.id"), nullable=False, index=True)
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id"), nullable=True, index=True, comment="Ürün (opsiyonel, detay seviyesine bağlı)")
    customer_id = Column(UUID(as_uuid=True), ForeignKey("customers.id"), nullable=True, index=True, comment="Müşteri (opsiyonel, detay seviyesine bağlı)")
    
    # Bütçe tutarları
    original_amount = Column(Numeric(15, 2), nullable=False, default=0, comment="Orijinal Bütçe")
    revised_amount = Column(Numeric(15, 2), nullable=False, default=0, comment="Revize Bütçe")
    actual_amount = Column(Numeric(15, 2), nullable=False, default=0, comment="Gerçek Harcama")
    forecast_amount = Column(Numeric(15, 2), nullable=False, default=0, comment="Tahmin")
    
    variance = Column(Numeric(15, 2), comment="Varyans = Revised - Actual")
    variance_percent = Column(Numeric(5, 2), comment="Varyans %")
    
    status = Column(String(20), default="ACTIVE", comment="Durum: ACTIVE, ARCHIVED")
    notes = Column(String(500), comment="Notlar")
    
    created_date = Column(DateTime, default=func.now(), nullable=False)
    updated_date = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    budget = relationship("Budget", back_populates="budget_lines")
    period = relationship("Period")
    product = relationship("Product")
    customer = relationship("Customer")
    
    def __repr__(self):
        return f"<BudgetLine(id={self.id}, budget_id={self.budget_id}, period_id={self.period_id})>"
