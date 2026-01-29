"""
Customer Model - Müşteri (SAP Customer Master)
"""

from sqlalchemy import Column, String, Boolean, DateTime, func, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from app.db.base import Base

class Customer(Base):
    """
    Müşteri modeli - SAP Customer Master'dan senkronize edilir
    """
    __tablename__ = "customers"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False, index=True)
    sap_customer_number = Column(String(10), nullable=False, index=True, comment="SAP Customer Number (KUNNR)")
    sap_customer_code = Column(String(10), comment="SAP Customer Code")
    name = Column(String(200), nullable=False, comment="Müşteri Adı")
    customer_group = Column(String(50), comment="Müşteri Grubu")
    sales_organization = Column(String(4), comment="SAP Sales Organization")
    distribution_channel = Column(String(2), comment="SAP Distribution Channel")
    division = Column(String(2), comment="SAP Division")
    is_active = Column(Boolean, default=True, nullable=False, comment="Aktif mi?")
    sap_sync_date = Column(DateTime, comment="SAP son senkronizasyon tarihi")
    created_date = Column(DateTime, default=func.now(), nullable=False)
    updated_date = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    company = relationship("Company", backref="customers")
    
    def __repr__(self):
        return f"<Customer(id={self.id}, name={self.name}, sap_customer={self.sap_customer_number})>"
