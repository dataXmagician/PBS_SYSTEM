"""
Meta Entity Schemas - Anaveri Tipi API Şemaları
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class MetaEntityBase(BaseModel):
    """Temel alanlar"""
    code: str = Field(..., min_length=1, max_length=50, description="Tekil kod (CUSTOMER, PRODUCT...)")
    default_name: str = Field(..., min_length=1, max_length=100, description="Varsayılan isim")
    description: Optional[str] = Field(None, max_length=500, description="Açıklama")
    icon: Optional[str] = Field("database", max_length=50, description="Lucide icon adı")
    color: Optional[str] = Field("blue", max_length=20, description="UI rengi")


class MetaEntityCreate(MetaEntityBase):
    """Yeni anaveri tipi oluşturma"""
    pass


class MetaEntityUpdate(BaseModel):
    """Anaveri tipi güncelleme (partial update)"""
    default_name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    icon: Optional[str] = Field(None, max_length=50)
    color: Optional[str] = Field(None, max_length=20)
    is_active: Optional[bool] = None
    sort_order: Optional[int] = None


class MetaAttributeInEntity(BaseModel):
    """Entity içinde attribute özeti"""
    id: int
    uuid: str
    code: str
    default_label: str
    data_type: str
    is_required: bool
    is_unique: bool = False
    is_code_field: bool
    is_name_field: bool
    is_active: bool = True
    is_system: bool = False
    sort_order: int
    options: Optional[List[str]] = None
    reference_entity_id: Optional[int] = None
    default_value: Optional[str] = None

    class Config:
        from_attributes = True


class MetaTranslationInEntity(BaseModel):
    """Entity içinde translation özeti"""
    language_code: str
    translated_name: str
    translated_description: Optional[str] = None

    class Config:
        from_attributes = True


class MetaEntityResponse(MetaEntityBase):
    """Anaveri tipi response"""
    id: int
    uuid: str
    is_active: bool
    is_system: bool
    sort_order: int
    created_date: datetime
    updated_date: datetime
    
    # İlişkili veriler
    attributes: List[MetaAttributeInEntity] = []
    translations: List[MetaTranslationInEntity] = []
    
    # Hesaplanan alanlar
    record_count: Optional[int] = Field(0, description="Bu tipteki kayıt sayısı")

    class Config:
        from_attributes = True


class MetaEntityListResponse(BaseModel):
    """Liste response"""
    items: List[MetaEntityResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
