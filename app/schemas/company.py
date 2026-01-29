"""
Company Schema - Request/Response modelleri
"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from uuid import UUID

class CompanyBase(BaseModel):
    """
    Company temel bilgileri
    """
    sap_company_code: str = Field(..., min_length=4, max_length=4, description="SAP Şirket Kodu")
    name: str = Field(..., min_length=1, max_length=100, description="Şirket Adı")
    budget_detail_level: str = Field(
        default="PRODUCT", 
        description="Bütçe detay seviyesi: PRODUCT | PRODUCT_CUSTOMER | PERIOD_ONLY"
    )


class CompanyCreate(BaseModel):
    company_code: str
    company_name: str
    description: Optional[str] = None

class CompanyCreate(CompanyBase):
    """
    Yeni şirket oluşturma
    """
    pass

class CompanyUpdate(BaseModel):
    """
    Şirket güncelleme (tüm alanlar opsiyonel)
    """
    name: Optional[str] = Field(None, max_length=100)
    budget_detail_level: Optional[str] = None
    is_active: Optional[bool] = None

class CompanyResponse(CompanyBase):
    """
    Şirket cevap modeli
    """
    id: UUID
    is_active: bool
    sap_sync_date: Optional[datetime]
    created_date: datetime
    updated_date: datetime
    
    class Config:
        from_attributes = True

class CompanyListResponse(BaseModel):
    """
    Şirket listesi cevabı
    """
    data: list[CompanyResponse]
    total: int
    
class CompanyDetailResponse(CompanyResponse):
    """
    Şirket detay cevabı
    """
    pass
