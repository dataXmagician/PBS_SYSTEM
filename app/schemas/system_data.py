"""
System Data Schemas - Sistem Verileri API Şemaları
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from uuid import UUID


# ============ Budget Period Schemas ============

class BudgetPeriodBase(BaseModel):
    code: str = Field(..., min_length=7, max_length=7, pattern=r'^\d{4}-\d{2}$', description="Dönem kodu (yyyy-MM)")


class BudgetPeriodCreate(BaseModel):
    start_period: str = Field(..., pattern=r'^\d{4}-\d{2}$', description="Başlangıç dönemi (yyyy-MM)")
    end_period: str = Field(..., pattern=r'^\d{4}-\d{2}$', description="Bitiş dönemi (yyyy-MM)")


class BudgetPeriodResponse(BaseModel):
    id: int
    uuid: UUID
    code: str
    name: str
    year: int
    month: int
    quarter: int
    is_active: bool
    sort_order: int
    created_date: datetime
    updated_date: datetime

    class Config:
        from_attributes = True


class BudgetPeriodListResponse(BaseModel):
    items: List[BudgetPeriodResponse]
    total: int


# ============ Budget Version Schemas ============

class BudgetVersionBase(BaseModel):
    code: str = Field(..., min_length=1, max_length=50, description="Versiyon kodu")
    name: str = Field(..., min_length=1, max_length=200, description="Versiyon adı")
    description: Optional[str] = Field(None, max_length=500)
    start_period_id: Optional[int] = None
    end_period_id: Optional[int] = None
    is_active: bool = True


class BudgetVersionCreate(BudgetVersionBase):
    pass


class BudgetVersionUpdate(BaseModel):
    code: Optional[str] = Field(None, min_length=1, max_length=50)
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=500)
    start_period_id: Optional[int] = None
    end_period_id: Optional[int] = None
    is_active: Optional[bool] = None
    is_locked: Optional[bool] = None


class BudgetVersionCopy(BaseModel):
    new_code: str = Field(..., min_length=1, max_length=50, description="Yeni versiyon kodu")
    new_name: str = Field(..., min_length=1, max_length=200, description="Yeni versiyon adı")
    description: Optional[str] = Field(None, max_length=500)
    copy_parameters: bool = Field(False, description="Kaynak versiyondaki parametre değerlerini kopyala")


class BudgetVersionResponse(BaseModel):
    id: int
    uuid: UUID
    code: str
    name: str
    description: Optional[str]
    start_period_id: Optional[int]
    end_period_id: Optional[int]
    start_period: Optional[BudgetPeriodResponse] = None
    end_period: Optional[BudgetPeriodResponse] = None
    is_active: bool
    is_locked: bool
    copied_from_id: Optional[int]
    sort_order: int
    created_date: datetime
    updated_date: datetime

    class Config:
        from_attributes = True


class BudgetVersionListResponse(BaseModel):
    items: List[BudgetVersionResponse]
    total: int


# ============ Budget Parameter Schemas ============

class VersionValueInput(BaseModel):
    """Parametre oluştururken/güncellerken versiyon-değer çifti"""
    version_id: int
    value: Optional[str] = None


class VersionValueResponse(BaseModel):
    """Parametre response'unda versiyon-değer çifti"""
    version_id: int
    version_code: str
    version_name: str
    value: Optional[str] = None


class BudgetParameterCreate(BaseModel):
    code: str = Field(..., min_length=1, max_length=50, description="Parametre kodu")
    name: str = Field(..., min_length=1, max_length=200, description="Parametre adı")
    description: Optional[str] = Field(None, max_length=500)
    value_type: str = Field(..., description="Değer tipi (tutar, miktar, sayi, yuzde)")
    version_values: List[VersionValueInput] = Field(default=[], description="Versiyon-değer çiftleri")
    is_active: bool = True


class BudgetParameterUpdate(BaseModel):
    code: Optional[str] = Field(None, min_length=1, max_length=50)
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=500)
    value_type: Optional[str] = None
    version_values: Optional[List[VersionValueInput]] = None
    is_active: Optional[bool] = None


class BudgetParameterResponse(BaseModel):
    id: int
    uuid: UUID
    code: str
    name: str
    description: Optional[str]
    value_type: str
    version_values: List[VersionValueResponse] = []
    is_active: bool
    sort_order: int
    created_date: datetime
    updated_date: datetime

    class Config:
        from_attributes = True


class BudgetParameterListResponse(BaseModel):
    items: List[BudgetParameterResponse]
    total: int


# ============ Budget Currency Schemas ============

class BudgetCurrencyBase(BaseModel):
    code: str = Field(..., min_length=1, max_length=10, description="Para birimi kodu")
    name: str = Field(..., min_length=1, max_length=200, description="Para birimi adi")
    is_active: bool = False


class BudgetCurrencyCreate(BudgetCurrencyBase):
    pass


class BudgetCurrencyUpdate(BaseModel):
    code: Optional[str] = Field(None, min_length=1, max_length=10)
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    is_active: Optional[bool] = None


class BudgetCurrencyResponse(BaseModel):
    id: int
    uuid: UUID
    code: str
    name: str
    is_active: bool
    sort_order: int
    created_date: datetime
    updated_date: datetime

    class Config:
        from_attributes = True


class BudgetCurrencyListResponse(BaseModel):
    items: List[BudgetCurrencyResponse]
    total: int


# ============ System Data Summary ============

class SystemDataSummary(BaseModel):
    """Sistem verileri özet bilgisi"""
    entity_type: str  # "version" | "period" | "parameter" | "currency"
    code: str
    name: str
    icon: str
    color: str
    description: str
    record_count: int
