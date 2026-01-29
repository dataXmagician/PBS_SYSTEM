"""
Period Schema - Request/Response modelleri
"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime, date
from uuid import UUID

class PeriodBase(BaseModel):
    """
    Period temel bilgileri
    """
    fiscal_year: int = Field(..., ge=2000, le=2100, description="Mali Yıl")
    period: int = Field(..., ge=1, le=12, description="Dönem (1-12)")
    period_name: Optional[str] = Field(None, max_length=50, description="Dönem Adı")
    start_date: date = Field(..., description="Başlangıç Tarihi")
    end_date: date = Field(..., description="Bitiş Tarihi")

class PeriodCreate(PeriodBase):
    """
    Yeni dönem oluşturma
    """
    company_id: UUID = Field(..., description="Şirket ID")

class PeriodUpdate(BaseModel):
    """
    Dönem güncelleme
    """
    period_name: Optional[str] = None
    is_open: Optional[bool] = None
    is_locked: Optional[bool] = None

class PeriodResponse(PeriodBase):
    """
    Dönem cevap modeli
    """
    id: UUID
    company_id: UUID
    is_open: bool
    is_locked: bool
    created_date: datetime
    updated_date: datetime
    
    class Config:
        from_attributes = True

class PeriodListResponse(BaseModel):
    """
    Dönem listesi cevabı
    """
    data: list[PeriodResponse]
    total: int
