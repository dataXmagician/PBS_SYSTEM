"""
Budget Schema - Request/Response modelleri
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from uuid import UUID
from decimal import Decimal

# Budget Line Schema
class BudgetLineBase(BaseModel):
    """
    Budget Line temel bilgileri
    """
    period_id: UUID = Field(..., description="Dönem ID")
    product_id: Optional[UUID] = Field(None, description="Ürün ID (opsiyonel)")
    customer_id: Optional[UUID] = Field(None, description="Müşteri ID (opsiyonel)")
    original_amount: Decimal = Field(..., decimal_places=2, description="Orijinal Bütçe")
    revised_amount: Decimal = Field(..., decimal_places=2, description="Revize Bütçe")
    actual_amount: Decimal = Field(default=0, decimal_places=2, description="Gerçek Harcama")
    forecast_amount: Decimal = Field(default=0, decimal_places=2, description="Tahmin")
    notes: Optional[str] = Field(None, max_length=500)

class BudgetLineCreate(BudgetLineBase):
    """
    Yeni bütçe satırı oluşturma
    """
    pass

class BudgetLineUpdate(BaseModel):
    """
    Bütçe satırı güncelleme
    """
    revised_amount: Optional[Decimal] = None
    actual_amount: Optional[Decimal] = None
    forecast_amount: Optional[Decimal] = None
    notes: Optional[str] = None
    status: Optional[str] = None

class BudgetLineResponse(BudgetLineBase):
    """
    Bütçe satırı cevap modeli
    """
    id: UUID
    budget_id: UUID
    variance: Optional[Decimal]
    variance_percent: Optional[Decimal]
    status: str
    created_date: datetime
    updated_date: datetime
    
    class Config:
        from_attributes = True

# Budget Schema
class BudgetBase(BaseModel):
    """
    Budget temel bilgileri
    """
    fiscal_year: str = Field(..., max_length=4, description="Mali Yıl (2024, 2025 vb)")
    budget_version: str = Field(..., max_length=20, description="Bütçe Versiyonu")
    description: Optional[str] = Field(None, description="Açıklama")
    currency: str = Field(default="USD", max_length=3)

class BudgetCreate(BudgetBase):
    """
    Yeni bütçe oluşturma
    """
    company_id: UUID = Field(..., description="Şirket ID")

class BudgetUpdate(BaseModel):
    """
    Bütçe güncelleme
    """
    description: Optional[str] = None
    status: Optional[str] = None

class BudgetResponse(BudgetBase):
    """
    Bütçe cevap modeli
    """
    id: UUID
    company_id: UUID
    total_amount: Decimal
    status: str
    created_by: Optional[str]
    approved_by: Optional[str]
    created_date: datetime
    updated_date: datetime
    
    class Config:
        from_attributes = True

class BudgetDetailResponse(BudgetResponse):
    """
    Bütçe detay (satırları ile)
    """
    budget_lines: List[BudgetLineResponse] = []

class BudgetListResponse(BaseModel):
    """
    Bütçe listesi
    """
    data: List[BudgetResponse]
    total: int
