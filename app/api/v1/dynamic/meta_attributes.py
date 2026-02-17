"""
Meta Attributes API - Anaveri Alan Yönetimi
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
import json
import logging

from app.db.session import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.models.dynamic.meta_entity import MetaEntity
from app.models.dynamic.meta_attribute import MetaAttribute
from app.models.dynamic.master_data_value import MasterDataValue
from app.schemas.dynamic.meta_attribute import (
    MetaAttributeCreate,
    MetaAttributeUpdate,
    MetaAttributeResponse,
    MetaAttributeBulkCreate
)

router = APIRouter(prefix="/meta-attributes", tags=["Meta Attributes - Anaveri Alanları"])
logger = logging.getLogger(__name__)


def enrich_attribute(attr: MetaAttribute, db: Session) -> MetaAttribute:
    """Attribute'a ek bilgiler ekle"""
    if attr.reference_entity_id:
        ref_entity = db.query(MetaEntity).filter(MetaEntity.id == attr.reference_entity_id).first()
        if ref_entity:
            attr.reference_entity_code = ref_entity.code
            attr.reference_entity_name = ref_entity.default_name

    if attr.options:
        try:
            attr.options = json.loads(attr.options)
        except:
            attr.options = []

    return attr


@router.get("/entity/{entity_id}", response_model=List[MetaAttributeResponse])
async def list_attributes_by_entity(
    entity_id: int,
    include_inactive: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Bir anaveri tipinin tüm alanlarını listele"""
    entity = db.query(MetaEntity).filter(MetaEntity.id == entity_id).first()
    if not entity:
        raise HTTPException(status_code=404, detail="Anaveri tipi bulunamadı")

    query = db.query(MetaAttribute).filter(MetaAttribute.entity_id == entity_id)

    if not include_inactive:
        query = query.filter(MetaAttribute.is_active == True)

    attributes = query.order_by(MetaAttribute.sort_order, MetaAttribute.id).all()

    return [enrich_attribute(attr, db) for attr in attributes]


@router.get("/{attribute_id}", response_model=MetaAttributeResponse)
async def get_attribute(
    attribute_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Alan detayı"""
    attr = db.query(MetaAttribute).filter(MetaAttribute.id == attribute_id).first()
    if not attr:
        raise HTTPException(status_code=404, detail="Alan bulunamadı")

    return enrich_attribute(attr, db)


@router.post("", response_model=MetaAttributeResponse, status_code=status.HTTP_201_CREATED)
async def create_attribute(
    data: MetaAttributeCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Yeni alan oluştur"""
    entity = db.query(MetaEntity).filter(MetaEntity.id == data.entity_id).first()
    if not entity:
        raise HTTPException(status_code=404, detail="Anaveri tipi bulunamadı")

    existing = db.query(MetaAttribute).filter(
        MetaAttribute.entity_id == data.entity_id,
        MetaAttribute.code == data.code.upper()
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail=f"'{data.code}' kodu bu anaveri tipinde zaten var")

    data_type_value = data.data_type.value if hasattr(data.data_type, 'value') else data.data_type
    if data_type_value == "reference" and data.reference_entity_id:
        ref_entity = db.query(MetaEntity).filter(MetaEntity.id == data.reference_entity_id).first()
        if not ref_entity:
            raise HTTPException(status_code=400, detail="Referans anaveri tipi bulunamadı")

    attr = MetaAttribute(
        entity_id=data.entity_id,
        code=data.code.upper(),
        default_label=data.default_label,
        data_type=data_type_value,
        options=json.dumps(data.options) if data.options else None,
        reference_entity_id=data.reference_entity_id,
        default_value=data.default_value,
        is_required=data.is_required,
        is_unique=data.is_unique,
        is_code_field=data.is_code_field,
        is_name_field=data.is_name_field,
        min_value=data.min_value,
        max_value=data.max_value,
        min_length=data.min_length,
        max_length=data.max_length,
        sort_order=data.sort_order
    )

    db.add(attr)
    db.commit()
    db.refresh(attr)

    return enrich_attribute(attr, db)


@router.post("/bulk", response_model=List[MetaAttributeResponse], status_code=status.HTTP_201_CREATED)
async def create_attributes_bulk(
    data: MetaAttributeBulkCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Toplu alan oluştur"""
    entity = db.query(MetaEntity).filter(MetaEntity.id == data.entity_id).first()
    if not entity:
        raise HTTPException(status_code=404, detail="Anaveri tipi bulunamadı")

    created = []
    for attr_data in data.attributes:
        existing = db.query(MetaAttribute).filter(
            MetaAttribute.entity_id == data.entity_id,
            MetaAttribute.code == attr_data.code.upper()
        ).first()
        if existing:
            continue

        attr_data_type = attr_data.data_type.value if hasattr(attr_data.data_type, 'value') else attr_data.data_type

        attr = MetaAttribute(
            entity_id=data.entity_id,
            code=attr_data.code.upper(),
            default_label=attr_data.default_label,
            data_type=attr_data_type,
            options=json.dumps(attr_data.options) if attr_data.options else None,
            reference_entity_id=attr_data.reference_entity_id,
            default_value=attr_data.default_value,
            is_required=attr_data.is_required,
            is_unique=attr_data.is_unique,
            is_code_field=attr_data.is_code_field,
            is_name_field=attr_data.is_name_field,
            sort_order=attr_data.sort_order
        )
        db.add(attr)
        created.append(attr)

    db.commit()

    return [enrich_attribute(attr, db) for attr in created]


@router.put("/{attribute_id}", response_model=MetaAttributeResponse)
async def update_attribute(
    attribute_id: int,
    data: MetaAttributeUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Alan güncelle"""
    attr = db.query(MetaAttribute).filter(MetaAttribute.id == attribute_id).first()
    if not attr:
        raise HTTPException(status_code=404, detail="Alan bulunamadı")

    if attr.is_system:
        if data.default_label:
            attr.default_label = data.default_label
        db.commit()
        db.refresh(attr)
        return enrich_attribute(attr, db)

    update_data = data.dict(exclude_unset=True)

    if "options" in update_data and update_data["options"]:
        update_data["options"] = json.dumps(update_data["options"])

    for field, value in update_data.items():
        setattr(attr, field, value)

    db.commit()
    db.refresh(attr)

    return enrich_attribute(attr, db)


@router.delete("/{attribute_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_attribute(
    attribute_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Alanı ve ilişkili tüm değerlerini sil.

    - Sistem alanları (CODE, NAME) silinemez
    - Özel alanlar (kullanıcı tanımlı) her zaman silinebilir
    - İlişkili değerler otomatik silinir
    """
    logger.info(f"Delete attribute request: id={attribute_id}")

    attr = db.query(MetaAttribute).filter(MetaAttribute.id == attribute_id).first()
    if not attr:
        raise HTTPException(status_code=404, detail="Alan bulunamadı")

    # Sistem alanları silinemez
    if attr.is_system:
        raise HTTPException(
            status_code=400,
            detail="Sistem alanları (CODE, NAME) silinemez. Bu alanlar anaveri yapısının temelini oluşturur."
        )

    # Önce ilişkili değerleri sil
    deleted_values = db.query(MasterDataValue).filter(MasterDataValue.attribute_id == attr.id).delete()
    logger.info(f"Deleted {deleted_values} values for attribute {attr.code}")

    # Sonra attribute'u sil
    db.delete(attr)
    db.commit()
    logger.info(f"Attribute {attr.code} (id={attribute_id}) deleted successfully")

    return None


@router.patch("/{attribute_id}/reorder", response_model=MetaAttributeResponse)
async def reorder_attribute(
    attribute_id: int,
    sort_order: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Alan sırasını değiştir"""
    attr = db.query(MetaAttribute).filter(MetaAttribute.id == attribute_id).first()
    if not attr:
        raise HTTPException(status_code=404, detail="Alan bulunamadı")

    attr.sort_order = sort_order
    db.commit()
    db.refresh(attr)

    return enrich_attribute(attr, db)
