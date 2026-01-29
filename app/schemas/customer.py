"""
Customer Schema - Request/Response modelleri
"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from uuid import UUID

class CustomerBase(BaseModel):
    """
    Customer temel bilgileri
    """
    sap_customer_number: str = Field(..., max_length=10, description="SAP Customer Number")
    sap_customer_code: Optional[str] = Field(None, max_length=10, description="SAP Customer Code")
    name: str = Field(..., min_length=1, max_length=200, description="Müşteri Adı")
    customer_group: Optional[str] = Field(None, max_length=50)
    sales_organization: Optional[str] = Field(None, max_length=4)
    distribution_channel: Optional[str] = Field(None, max_length=2)
    division: Optional[str] = Field(None, max_length=2)

class CustomerCreate(CustomerBase):
    """
    Yeni müşteri oluşturma
    """
    company_id: UUID = Field(..., description="Şirket ID")

class CustomerUpdate(BaseModel):
    """
    Müşteri güncelleme
    """
    name: Optional[str] = Field(None, max_length=200)
    customer_group: Optional[str] = None
    is_active: Optional[bool] = None

class CustomerResponse(CustomerBase):
    """
    Müşteri cevap modeli
    """
    id: UUID
    company_id: UUID
    is_active: bool
    sap_sync_date: Optional[datetime]
    created_date: datetime
    updated_date: datetime
    
    class Config:
        from_attributes = True

class CustomerListResponse(BaseModel):
    """
    Müşteri listesi cevabı
    """
    data: list[CustomerResponse]
    total: int
