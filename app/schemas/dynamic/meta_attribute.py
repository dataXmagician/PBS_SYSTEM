"""
Meta Attribute Schemas - Anaveri Alan API Şemaları
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List, Any
from datetime import datetime
from enum import Enum


class AttributeTypeEnum(str, Enum):
    """Alan veri tipleri"""
    STRING = "string"
    INTEGER = "integer"
    DECIMAL = "decimal"
    BOOLEAN = "boolean"
    DATE = "date"
    DATETIME = "datetime"
    LIST = "list"
    REFERENCE = "reference"


class MetaAttributeBase(BaseModel):
    """Temel alanlar"""
    code: str = Field(..., min_length=1, max_length=50, description="Alan kodu")
    default_label: str = Field(..., min_length=1, max_length=100, description="Varsayılan etiket")
    data_type: AttributeTypeEnum = Field(..., description="Veri tipi")
    
    # Opsiyonel alanlar
    options: Optional[List[str]] = Field(None, description="LIST tipi için seçenekler")
    reference_entity_id: Optional[int] = Field(None, description="REFERENCE tipi için hedef entity ID")
    default_value: Optional[str] = Field(None, max_length=255, description="Varsayılan değer")
    
    # Validasyon
    is_required: bool = Field(False, description="Zorunlu mu?")
    is_unique: bool = Field(False, description="Tekil mi?")
    
    # Özel alanlar
    is_code_field: bool = Field(False, description="Kod alanı mı?")
    is_name_field: bool = Field(False, description="Ad alanı mı?")
    
    # Sınırlar
    min_value: Optional[str] = Field(None, description="Minimum değer")
    max_value: Optional[str] = Field(None, description="Maximum değer")
    min_length: Optional[int] = Field(None, description="Minimum uzunluk")
    max_length: Optional[int] = Field(None, description="Maximum uzunluk")
    
    sort_order: int = Field(0, description="Sıralama")

    @validator('options', pre=True, always=True)
    def validate_options(cls, v, values):
        if values.get('data_type') == AttributeTypeEnum.LIST and not v:
            raise ValueError('LIST tipi için options gerekli')
        return v

    @validator('reference_entity_id', pre=True, always=True)
    def validate_reference(cls, v, values):
        if values.get('data_type') == AttributeTypeEnum.REFERENCE and not v:
            raise ValueError('REFERENCE tipi için reference_entity_id gerekli')
        return v


class MetaAttributeCreate(MetaAttributeBase):
    """Yeni alan oluşturma"""
    entity_id: int = Field(..., description="Hangi entity'ye ait?")


class MetaAttributeUpdate(BaseModel):
    """Alan güncelleme (partial update)"""
    default_label: Optional[str] = Field(None, min_length=1, max_length=100)
    options: Optional[List[str]] = None
    default_value: Optional[str] = Field(None, max_length=255)
    is_required: Optional[bool] = None
    is_unique: Optional[bool] = None
    min_value: Optional[str] = None
    max_value: Optional[str] = None
    min_length: Optional[int] = None
    max_length: Optional[int] = None
    sort_order: Optional[int] = None
    is_active: Optional[bool] = None


class MetaAttributeResponse(MetaAttributeBase):
    """Alan response"""
    id: int
    uuid: str
    entity_id: int
    is_active: bool
    is_system: bool
    created_date: datetime
    updated_date: datetime
    
    # Referans entity bilgisi
    reference_entity_code: Optional[str] = None
    reference_entity_name: Optional[str] = None

    class Config:
        from_attributes = True


class MetaAttributeBulkCreate(BaseModel):
    """Toplu alan oluşturma"""
    entity_id: int
    attributes: List[MetaAttributeBase]
