"""
Forecast Model - Bütçe Tahmini
"""

from sqlalchemy import Column, String, Numeric, DateTime, func, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from app.db.base import Base

class Forecast(Base):
    """
    Bütçe tahmini kaydı
    """
    __tablename__ = "forecasts"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    budget_id = Column(UUID(as_uuid=True), ForeignKey("budgets.id"), nullable=False, index=True)
    period_id = Column(UUID(as_uuid=True), ForeignKey("periods.id"), nullable=False, index=True)
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id"), nullable=True, index=True)
    customer_id = Column(UUID(as_uuid=True), ForeignKey("customers.id"), nullable=True, index=True)
    
    # Tahmin verileri
    forecast_method = Column(String(50), default="MOVING_AVERAGE", comment="Tahmin Yöntemi")
    base_amount = Column(Numeric(15, 2), nullable=False, comment="Temel Tutar (ortalama)")
    forecast_amount = Column(Numeric(15, 2), nullable=False, comment="Tahmin Tutarı")
    trend_percentage = Column(Numeric(5, 2), comment="Trend Yüzdesi")
    confidence_score = Column(Numeric(3, 2), comment="Güven Puanı (0-1)")
    lower_bound = Column(Numeric(15, 2), comment="Alt Sınır (%80 CI)")
    upper_bound = Column(Numeric(15, 2), comment="Üst Sınır (%80 CI)")
    
    # Metadata
    data_points_used = Column(String(500), comment="Kullanılan veri noktaları (JSON)")
    notes = Column(Text, comment="Tahmin Notları")
    created_by = Column(String(100), comment="Oluşturan Kullanıcı")
    created_date = Column(DateTime, default=func.now(), nullable=False)
    updated_date = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    budget = relationship("Budget")
    period = relationship("Period")
    product = relationship("Product")
    customer = relationship("Customer")
    
    def __repr__(self):
        return f"<Forecast(id={self.id}, budget_id={self.budget_id}, forecast_amount={self.forecast_amount})>"
