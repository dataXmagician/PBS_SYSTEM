"""
Period Model - Mali Yıl Dönemi (SAP Period)
"""

from sqlalchemy import Column, String, Integer, Date, Boolean, DateTime, func, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from datetime import date
from app.db.base import Base

class Period(Base):
    """
    Mali yıl dönemi modeli
    """
    __tablename__ = "periods"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False, index=True)
    fiscal_year = Column(Integer, nullable=False, comment="Mali Yıl (2024, 2025 vb)")
    period = Column(Integer, nullable=False, comment="Dönem (1-12)")
    period_name = Column(String(50), comment="Dönem Adı (Jan 2024, Ocak 2024 vb)")
    start_date = Column(Date, nullable=False, comment="Başlangıç Tarihi")
    end_date = Column(Date, nullable=False, comment="Bitiş Tarihi")
    is_open = Column(Boolean, default=True, nullable=False, comment="Girişe açık mı?")
    is_locked = Column(Boolean, default=False, nullable=False, comment="Kilitli mi? (Onaylandı)")
    created_date = Column(DateTime, default=func.now(), nullable=False)
    updated_date = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    company = relationship("Company", backref="periods")
    
    def __repr__(self):
        return f"<Period(id={self.id}, fiscal_year={self.fiscal_year}, period={self.period})>"
