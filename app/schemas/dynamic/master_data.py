"""
Master Data Schemas - Anaveri Kayıt API Şemaları
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Any, Dict
from datetime import datetime


class MasterDataValueCreate(BaseModel):
    """Alan değeri oluşturma"""
    attribute_id: int = Field(..., description="Attribute ID")
    value: Optional[Any] = Field(None, description="Değer (tip attribute'a göre)")
    reference_id: Optional[int] = Field(None, description="REFERENCE tipi için hedef kayıt ID")


class MasterDataValueResponse(BaseModel):
    """Alan değeri response"""
    id: int
    attribute_id: int
    attribute_code: str
    attribute_label: str
    data_type: str
    value: Optional[str]
    reference_id: Optional[int]
    reference_display: Optional[str] = None  # Referans kaydının görünen adı

    class Config:
        from_attributes = True


class MasterDataBase(BaseModel):
    """Temel alanlar"""
    code: str = Field(..., min_length=1, max_length=50, description="Kayıt kodu")
    name: str = Field(..., min_length=1, max_length=200, description="Kayıt adı")
    is_active: bool = Field(True, description="Aktif mi?")
    sort_order: int = Field(0, description="Sıralama")


class MasterDataCreate(MasterDataBase):
    """Yeni kayıt oluşturma"""
    entity_id: int = Field(..., description="Hangi entity'ye ait?")
    values: Optional[List[MasterDataValueCreate]] = Field([], description="Alan değerleri")


class MasterDataUpdate(BaseModel):
    """Kayıt güncelleme (partial update)"""
    code: Optional[str] = Field(None, min_length=1, max_length=50)
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    is_active: Optional[bool] = None
    sort_order: Optional[int] = None
    values: Optional[List[MasterDataValueCreate]] = None


class MasterDataResponse(MasterDataBase):
    """Kayıt response"""
    id: int
    uuid: str
    entity_id: int
    entity_code: str
    entity_name: str
    created_date: datetime
    updated_date: datetime
    
    # Dinamik alan değerleri
    values: List[MasterDataValueResponse] = []
    
    # Flat values (kolay erişim için)
    flat_values: Optional[Dict[str, Any]] = Field(None, description="attribute_code: value formatında")

    class Config:
        from_attributes = True


class MasterDataListResponse(BaseModel):
    """Liste response"""
    items: List[MasterDataResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class MasterDataBulkCreate(BaseModel):
    """Toplu kayıt oluşturma"""
    entity_id: int
    records: List[MasterDataBase]


class MasterDataImport(BaseModel):
    """Excel/CSV import için"""
    entity_id: int
    data: List[Dict[str, Any]]  # [{"CODE": "M001", "NAME": "Acme", "SECTOR": "Otomotiv"}, ...]
