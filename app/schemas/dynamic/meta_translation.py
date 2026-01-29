"""
Meta Translation Schemas - Çoklu Dil API Şemaları
"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class MetaTranslationBase(BaseModel):
    """Temel alanlar"""
    language_code: str = Field(..., min_length=2, max_length=5, description="Dil kodu (tr, en, de...)")
    translated_name: str = Field(..., min_length=1, max_length=100, description="Çevrilmiş isim")
    translated_description: Optional[str] = Field(None, max_length=500, description="Çevrilmiş açıklama")


class MetaTranslationCreate(MetaTranslationBase):
    """Yeni çeviri oluşturma"""
    entity_id: Optional[int] = Field(None, description="Entity ID (entity veya attribute'dan biri dolu olmalı)")
    attribute_id: Optional[int] = Field(None, description="Attribute ID")


class MetaTranslationUpdate(BaseModel):
    """Çeviri güncelleme"""
    translated_name: Optional[str] = Field(None, min_length=1, max_length=100)
    translated_description: Optional[str] = Field(None, max_length=500)


class MetaTranslationResponse(MetaTranslationBase):
    """Çeviri response"""
    id: int
    entity_id: Optional[int]
    attribute_id: Optional[int]
    created_date: datetime
    updated_date: datetime

    class Config:
        from_attributes = True


class TranslationBulkCreate(BaseModel):
    """Toplu çeviri oluşturma (bir entity için tüm diller)"""
    entity_id: int
    translations: list[MetaTranslationBase]


class TranslationBulkAttributeCreate(BaseModel):
    """Toplu attribute çevirisi"""
    attribute_id: int
    translations: list[MetaTranslationBase]
