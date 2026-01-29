"""
Forecast Schema - Request/Response modelleri
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from uuid import UUID
from decimal import Decimal

class ForecastBase(BaseModel):
    """
    Forecast temel bilgileri
    """
    budget_id: UUID = Field(..., description="Bütçe ID")
    period_id: UUID = Field(..., description="Dönem ID")
    product_id: Optional[UUID] = Field(None, description="Ürün ID (opsiyonel)")
    customer_id: Optional[UUID] = Field(None, description="Müşteri ID (opsiyonel)")
    forecast_method: str = Field(default="MOVING_AVERAGE", description="Tahmin Yöntemi")
    notes: Optional[str] = Field(None, description="Notlar")

class ForecastCreate(ForecastBase):
    """
    Yeni tahmin oluşturma
    """
    pass

class ForecastResponse(ForecastBase):
    """
    Tahmin cevap modeli
    """
    id: UUID
    base_amount: Decimal
    forecast_amount: Decimal
    trend_percentage: Optional[Decimal]
    confidence_score: Optional[Decimal]
    lower_bound: Optional[Decimal]
    upper_bound: Optional[Decimal]
    data_points_used: Optional[str]
    created_by: Optional[str]
    created_date: datetime
    updated_date: datetime
    
    class Config:
        from_attributes = True

class ForecastListResponse(BaseModel):
    """
    Tahmin listesi
    """
    data: List[ForecastResponse]
    total: int

class ForecastRequest(BaseModel):
    """
    Tahmin İstek (hesaplama için)
    """
    budget_id: UUID = Field(..., description="Bütçe ID")
    period_id: UUID = Field(..., description="Dönem ID")
    product_id: Optional[UUID] = Field(None, description="Ürün ID (opsiyonel)")
    customer_id: Optional[UUID] = Field(None, description="Müşteri ID (opsiyonel)")
    method: str = Field(default="MOVING_AVERAGE", description="Tahmin Yöntemi")
    lookback_periods: int = Field(default=3, ge=1, le=12, description="Kaç ay geri bakılacak")

class ForecastResult(BaseModel):
    """
    Tahmin Sonucu
    """
    forecast_amount: Decimal = Field(..., description="Tahmin Tutarı")
    trend_percentage: Decimal = Field(..., description="Trend Yüzdesi")
    confidence_score: Decimal = Field(..., description="Güven Puanı (0-1)")
    lower_bound: Decimal = Field(..., description="Alt Sınır")
    upper_bound: Decimal = Field(..., description="Üst Sınır")
    base_amount: Decimal = Field(..., description="Temel Tutar")
    data_points: List[dict] = Field(..., description="Kullanılan veri noktaları")
    interpretation: str = Field(..., description="Tahmin Yorumu")
