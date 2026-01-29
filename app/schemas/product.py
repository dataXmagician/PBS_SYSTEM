"""
Product Schema - Request/Response modelleri
"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from uuid import UUID

class ProductBase(BaseModel):
    """
    Product temel bilgileri
    """
    sap_material_number: str = Field(..., max_length=18, description="SAP Material Number")
    sap_material_code: Optional[str] = Field(None, max_length=20, description="SAP Material Code")
    name: str = Field(..., min_length=1, max_length=200, description="Ürün Adı")
    description: Optional[str] = Field(None, max_length=500)
    category: Optional[str] = Field(None, max_length=100)
    unit_of_measure: Optional[str] = Field(None, max_length=10)

class ProductCreate(ProductBase):
    """
    Yeni ürün oluşturma
    """
    company_id: UUID = Field(..., description="Şirket ID")

class ProductUpdate(BaseModel):
    """
    Ürün güncelleme
    """
    name: Optional[str] = Field(None, max_length=200)
    description: Optional[str] = None
    category: Optional[str] = None
    unit_of_measure: Optional[str] = None
    is_active: Optional[bool] = None

class ProductResponse(ProductBase):
    """
    Ürün cevap modeli
    """
    id: UUID
    company_id: UUID
    is_active: bool
    sap_sync_date: Optional[datetime]
    created_date: datetime
    updated_date: datetime
    
    class Config:
        from_attributes = True

class ProductListResponse(BaseModel):
    """
    Ürün listesi cevabı
    """
    data: list[ProductResponse]
    total: int
