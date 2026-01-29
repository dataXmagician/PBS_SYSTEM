"""
Fact Definition Schemas - Veri Giriş Şablonu API Şemaları
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum


class TimeGranularityEnum(str, Enum):
    """Tarih granülaritesi"""
    DAY = "day"
    WEEK = "week"
    MONTH = "month"
    QUARTER = "quarter"
    YEAR = "year"


class MeasureTypeEnum(str, Enum):
    """Ölçü tipleri"""
    INTEGER = "integer"
    DECIMAL = "decimal"
    CURRENCY = "currency"
    PERCENTAGE = "percentage"


class AggregationTypeEnum(str, Enum):
    """Toplama yöntemleri"""
    SUM = "sum"
    AVG = "avg"
    MIN = "min"
    MAX = "max"
    COUNT = "count"
    LAST = "last"


class FactDimensionCreate(BaseModel):
    """Boyut ekleme"""
    entity_id: int = Field(..., description="Anaveri tipi ID")
    sort_order: int = Field(0, description="Sıralama")
    is_required: bool = Field(True, description="Zorunlu mu?")


class FactDimensionResponse(BaseModel):
    """Boyut response"""
    id: int
    entity_id: int
    entity_code: str
    entity_name: str
    sort_order: int
    is_required: bool

    class Config:
        from_attributes = True


class FactMeasureCreate(BaseModel):
    """Ölçü ekleme"""
    code: str = Field(..., min_length=1, max_length=50, description="Ölçü kodu")
    name: str = Field(..., min_length=1, max_length=100, description="Ölçü adı")
    measure_type: MeasureTypeEnum = Field(MeasureTypeEnum.DECIMAL, description="Veri tipi")
    aggregation: AggregationTypeEnum = Field(AggregationTypeEnum.SUM, description="Toplama yöntemi")
    decimal_places: int = Field(2, ge=0, le=10, description="Ondalık basamak")
    unit: Optional[str] = Field(None, max_length=20, description="Birim")
    default_value: str = Field("0", description="Varsayılan değer")
    is_required: bool = Field(False, description="Zorunlu mu?")
    is_calculated: bool = Field(False, description="Hesaplanan alan mı?")
    formula: Optional[str] = Field(None, max_length=500, description="Formül")
    sort_order: int = Field(0, description="Sıralama")


class FactMeasureResponse(FactMeasureCreate):
    """Ölçü response"""
    id: int
    fact_definition_id: int
    is_active: bool
    created_date: datetime
    updated_date: datetime

    class Config:
        from_attributes = True


class FactDefinitionBase(BaseModel):
    """Temel alanlar"""
    code: str = Field(..., min_length=1, max_length=50, description="Şablon kodu")
    name: str = Field(..., min_length=1, max_length=100, description="Şablon adı")
    description: Optional[str] = Field(None, max_length=500, description="Açıklama")
    include_time_dimension: bool = Field(True, description="Tarih boyutu dahil mi?")
    time_granularity: TimeGranularityEnum = Field(TimeGranularityEnum.MONTH, description="Tarih granülaritesi")


class FactDefinitionCreate(FactDefinitionBase):
    """Yeni şablon oluşturma"""
    dimensions: List[FactDimensionCreate] = Field(..., min_items=1, description="En az 1 boyut gerekli")
    measures: List[FactMeasureCreate] = Field(..., min_items=1, description="En az 1 ölçü gerekli")


class FactDefinitionUpdate(BaseModel):
    """Şablon güncelleme"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    include_time_dimension: Optional[bool] = None
    time_granularity: Optional[TimeGranularityEnum] = None
    is_active: Optional[bool] = None


class FactDefinitionResponse(FactDefinitionBase):
    """Şablon response"""
    id: int
    uuid: str
    is_active: bool
    created_date: datetime
    updated_date: datetime
    
    dimensions: List[FactDimensionResponse] = []
    measures: List[FactMeasureResponse] = []
    
    # İstatistikler
    data_count: Optional[int] = Field(0, description="Veri sayısı")

    class Config:
        from_attributes = True


class FactDefinitionListResponse(BaseModel):
    """Liste response"""
    items: List[FactDefinitionResponse]
    total: int
