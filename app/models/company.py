"""
Company Model - Şirket tanımlaması
"""

from sqlalchemy import Column, String, Boolean, DateTime, func
from sqlalchemy.dialects.postgresql import UUID
import uuid
from app.db.base import Base
from datetime import datetime

class Company(Base):
    """
    Şirket modeli - SAP şirket kodları ile eşleştirilir
    """
    __tablename__ = "companies"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    sap_company_code = Column(String(4), unique=True, nullable=False, index=True, comment="SAP Şirket Kodu (0001, 1000 vb)")
    name = Column(String(100), nullable=False, comment="Şirket Adı")
    budget_detail_level = Column(
        String(50), 
        nullable=False, 
        default="PRODUCT",
        comment="Bütçe detay seviyesi: PRODUCT | PRODUCT_CUSTOMER | PERIOD_ONLY"
    )
    is_active = Column(Boolean, default=True, nullable=False, comment="Aktif mi?")
    sap_sync_date = Column(DateTime, nullable=True, comment="SAP son senkronizasyon tarihi")
    created_date = Column(DateTime, default=func.now(), nullable=False)
    updated_date = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    
    def __repr__(self):
        return f"<Company(id={self.id}, name={self.name}, code={self.sap_company_code})>"
