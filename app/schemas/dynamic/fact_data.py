"""
Fact Data Schemas - Veri Giriş API Şemaları
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime, date


class FactDataValueCreate(BaseModel):
    """Ölçü değeri"""
    measure_id: int = Field(..., description="Ölçü ID")
    value: Any = Field(..., description="Değer")


class FactDataValueResponse(BaseModel):
    """Ölçü değeri response"""
    id: int
    measure_id: int
    measure_code: str
    measure_name: str
    value: Optional[str]
    
    class Config:
        from_attributes = True


class FactDataCreate(BaseModel):
    """Yeni veri girişi"""
    fact_definition_id: int = Field(..., description="Şablon ID")
    dimension_values: Dict[str, int] = Field(..., description="Boyut değerleri {entity_id: master_data_id}")
    year: Optional[int] = Field(None, description="Yıl")
    month: Optional[int] = Field(None, ge=1, le=12, description="Ay")
    version: str = Field("BUDGET", description="Versiyon (BUDGET, FORECAST, ACTUAL)")
    values: List[FactDataValueCreate] = Field(..., description="Ölçü değerleri")


class FactDataUpdate(BaseModel):
    """Veri güncelleme"""
    values: List[FactDataValueCreate] = Field(..., description="Ölçü değerleri")


class FactDataResponse(BaseModel):
    """Veri response"""
    id: int
    uuid: str
    fact_definition_id: int
    dimension_values: Dict[str, int]
    dimension_display: Optional[Dict[str, str]] = None  # {entity_code: "master_data_code - name"}
    year: Optional[int]
    month: Optional[int]
    version: str
    values: List[FactDataValueResponse] = []
    created_date: datetime
    updated_date: datetime

    class Config:
        from_attributes = True


class FactDataListResponse(BaseModel):
    """Liste response"""
    items: List[FactDataResponse]
    total: int
    page: int
    page_size: int


class FactDataBulkCreate(BaseModel):
    """Toplu veri girişi"""
    fact_definition_id: int
    version: str = "BUDGET"
    data: List[Dict[str, Any]]
    """
    Örnek data formatı:
    [
        {
            "CUSTOMER": "M001",  # entity_code: master_data_code
            "PRODUCT": "P001",
            "YEAR": 2025,
            "MONTH": 1,
            "QUANTITY": 100,    # measure_code: value
            "PRICE": 50.00
        },
        ...
    ]
    """


class FactDataQuery(BaseModel):
    """Veri sorgulama"""
    fact_definition_id: int
    filters: Optional[Dict[str, Any]] = None  # {"CUSTOMER": ["M001", "M002"], "YEAR": 2025}
    version: Optional[str] = None
    year_from: Optional[int] = None
    year_to: Optional[int] = None
    month_from: Optional[int] = None
    month_to: Optional[int] = None
    page: int = 1
    page_size: int = 100


class FactDataPivotQuery(BaseModel):
    """Pivot tablo sorgusu"""
    fact_definition_id: int
    rows: List[str] = Field(..., description="Satır boyutları (entity_code'lar)")
    columns: List[str] = Field(..., description="Sütun boyutları")
    measures: List[str] = Field(..., description="Gösterilecek ölçüler (measure_code'lar)")
    filters: Optional[Dict[str, Any]] = None
    version: Optional[str] = "BUDGET"


class FactDataPivotResponse(BaseModel):
    """Pivot tablo response"""
    headers: List[str]
    rows: List[Dict[str, Any]]
    totals: Optional[Dict[str, Any]] = None
