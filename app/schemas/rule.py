"""
Rule Schema - Request/Response modelleri
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from uuid import UUID
from decimal import Decimal

class RuleBase(BaseModel):
    """
    Rule temel bilgileri
    """
    rule_name: str = Field(..., description="Kuralın Adı")
    rule_type: str = Field(..., description="Kural Tipi (PERCENTAGE, FORMULA, THRESHOLD)")
    description: Optional[str] = Field(None, description="Açıklama")
    action: str = Field(..., description="İşlem (örn: original_amount * 1.1)")
    percentage_value: Optional[Decimal] = Field(None, description="Yüzde değeri")
    threshold_amount: Optional[Decimal] = Field(None, description="Eşik tutarı")
    is_active: bool = Field(default=True, description="Aktif mi?")
    apply_automatically: bool = Field(default=True, description="Otomatik uygula?")
    requires_approval: bool = Field(default=False, description="Onay gerekli mi?")

class RuleCreate(RuleBase):
    """
    Yeni kural oluşturma
    """
    company_id: UUID = Field(..., description="Şirket ID")

class RuleUpdate(BaseModel):
    """
    Kural güncelleme
    """
    rule_name: Optional[str] = None
    description: Optional[str] = None
    action: Optional[str] = None
    percentage_value: Optional[Decimal] = None
    is_active: Optional[bool] = None

class RuleResponse(RuleBase):
    """
    Kural cevap modeli
    """
    id: UUID
    company_id: UUID
    created_by: Optional[str]
    created_date: datetime
    updated_date: datetime
    
    class Config:
        from_attributes = True

class RuleListResponse(BaseModel):
    """
    Kural listesi
    """
    data: List[RuleResponse]
    total: int

class CalculationPreview(BaseModel):
    """
    Hesaplama önizlemesi
    """
    original_amount: Decimal
    revised_amount: Decimal
    difference: Decimal
    percentage_change: Decimal
    applied_rules: List[str] = Field(description="Uygulanan kurallar")

class BulkCalculationRequest(BaseModel):
    """
    Toplu hesaplama isteği
    """
    lines: List[dict] = Field(description="Satırlar")
    apply_rules: bool = Field(default=True, description="Kuralları uygula?")
    rule_ids: Optional[List[UUID]] = Field(None, description="Uygulanacak kural ID'leri")

class BulkCalculationResponse(BaseModel):
    """
    Toplu hesaplama sonucu
    """
    processed_count: int
    success_count: int
    error_count: int
    results: List[dict]