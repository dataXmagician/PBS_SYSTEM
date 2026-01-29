"""
Product Model - Ürün (SAP Material Master)
"""

from sqlalchemy import Column, String, Boolean, DateTime, func, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from app.db.base import Base

class Product(Base):
    """
    Ürün modeli - SAP Material Master'dan senkronize edilir
    """
    __tablename__ = "products"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False, index=True)
    sap_material_number = Column(String(18), nullable=False, index=True, comment="SAP Material Number (MATNR)")
    sap_material_code = Column(String(20), comment="SAP Material Code")
    name = Column(String(200), nullable=False, comment="Ürün Adı")
    description = Column(String(500), comment="Açıklama")
    category = Column(String(100), comment="Ürün Kategorisi")
    unit_of_measure = Column(String(10), comment="Birim (PC, KG vb)")
    is_active = Column(Boolean, default=True, nullable=False, comment="Aktif mi?")
    sap_sync_date = Column(DateTime, comment="SAP son senkronizasyon tarihi")
    created_date = Column(DateTime, default=func.now(), nullable=False)
    updated_date = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    company = relationship("Company", backref="products")
    
    def __repr__(self):
        return f"<Product(id={self.id}, name={self.name}, sap_material={self.sap_material_number})>"
