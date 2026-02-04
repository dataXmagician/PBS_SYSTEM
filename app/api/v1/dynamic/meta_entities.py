"""
Meta Entities API - Anaveri Tipi Yönetimi
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func
from typing import List, Optional

from app.db.session import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.models.dynamic.meta_entity import MetaEntity
from app.models.dynamic.meta_attribute import MetaAttribute
from app.models.dynamic.master_data import MasterData
from app.schemas.dynamic.meta_entity import (
    MetaEntityCreate,
    MetaEntityUpdate,
    MetaEntityResponse,
    MetaEntityListResponse
)

router = APIRouter(prefix="/meta-entities", tags=["Meta Entities - Anaveri Tipleri"])


@router.get("", response_model=MetaEntityListResponse)
async def list_meta_entities(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: Optional[str] = None,
    is_active: Optional[bool] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Tüm anaveri tiplerini listele"""
    query = db.query(MetaEntity).options(joinedload(MetaEntity.attributes))

    if search:
        query = query.filter(
            (MetaEntity.code.ilike(f"%{search}%")) |
            (MetaEntity.default_name.ilike(f"%{search}%"))
        )

    if is_active is not None:
        query = query.filter(MetaEntity.is_active == is_active)

    # Total için ayrı query (joinedload ile count yapılmaz)
    count_query = db.query(func.count(MetaEntity.id))
    if search:
        count_query = count_query.filter(
            (MetaEntity.code.ilike(f"%{search}%")) |
            (MetaEntity.default_name.ilike(f"%{search}%"))
        )
    if is_active is not None:
        count_query = count_query.filter(MetaEntity.is_active == is_active)
    total = count_query.scalar()

    items = query.order_by(MetaEntity.sort_order, MetaEntity.code)\
        .offset((page - 1) * page_size)\
        .limit(page_size)\
        .all()

    # Her entity için kayıt sayısını ekle
    for item in items:
        item.record_count = db.query(func.count(MasterData.id))\
            .filter(MasterData.entity_id == item.id).scalar()

    return MetaEntityListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=(total + page_size - 1) // page_size
    )


@router.get("/{entity_id}", response_model=MetaEntityResponse)
async def get_meta_entity(
    entity_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Anaveri tipi detayı"""
    entity = db.query(MetaEntity)\
        .options(joinedload(MetaEntity.attributes))\
        .filter(MetaEntity.id == entity_id)\
        .first()
    if not entity:
        raise HTTPException(status_code=404, detail="Anaveri tipi bulunamadı")

    entity.record_count = db.query(func.count(MasterData.id))\
        .filter(MasterData.entity_id == entity.id).scalar()

    return entity


@router.get("/code/{code}", response_model=MetaEntityResponse)
async def get_meta_entity_by_code(
    code: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Kod ile anaveri tipi getir"""
    entity = db.query(MetaEntity).filter(MetaEntity.code == code.upper()).first()
    if not entity:
        raise HTTPException(status_code=404, detail="Anaveri tipi bulunamadı")
    
    entity.record_count = db.query(func.count(MasterData.id))\
        .filter(MasterData.entity_id == entity.id).scalar()
    
    return entity


@router.post("", response_model=MetaEntityResponse, status_code=status.HTTP_201_CREATED)
async def create_meta_entity(
    data: MetaEntityCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Yeni anaveri tipi oluştur"""
    # Kod kontrolü
    existing = db.query(MetaEntity).filter(MetaEntity.code == data.code.upper()).first()
    if existing:
        raise HTTPException(status_code=400, detail=f"'{data.code}' kodu zaten kullanılıyor")
    
    entity = MetaEntity(
        code=data.code.upper(),
        default_name=data.default_name,
        description=data.description,
        icon=data.icon or "database",
        color=data.color or "blue"
    )
    
    db.add(entity)
    db.commit()
    db.refresh(entity)
    
    # Varsayılan CODE ve NAME alanlarını ekle
    code_attr = MetaAttribute(
        entity_id=entity.id,
        code="CODE",
        default_label="Kod",
        data_type="string",
        is_required=True,
        is_unique=True,
        is_code_field=True,
        is_system=True,
        sort_order=0,
        max_length=50
    )

    name_attr = MetaAttribute(
        entity_id=entity.id,
        code="NAME",
        default_label="Ad",
        data_type="string",
        is_required=True,
        is_name_field=True,
        is_system=True,
        sort_order=1,
        max_length=200
    )
    
    db.add(code_attr)
    db.add(name_attr)
    db.commit()
    db.refresh(entity)
    
    entity.record_count = 0
    return entity


@router.put("/{entity_id}", response_model=MetaEntityResponse)
async def update_meta_entity(
    entity_id: int,
    data: MetaEntityUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Anaveri tipi güncelle"""
    entity = db.query(MetaEntity).filter(MetaEntity.id == entity_id).first()
    if not entity:
        raise HTTPException(status_code=404, detail="Anaveri tipi bulunamadı")
    
    if entity.is_system:
        raise HTTPException(status_code=400, detail="Sistem anaveri tipleri değiştirilemez")
    
    update_data = data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(entity, field, value)
    
    db.commit()
    db.refresh(entity)
    
    entity.record_count = db.query(func.count(MasterData.id))\
        .filter(MasterData.entity_id == entity.id).scalar()
    
    return entity


@router.delete("/{entity_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_meta_entity(
    entity_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Anaveri tipi sil"""
    entity = db.query(MetaEntity).filter(MetaEntity.id == entity_id).first()
    if not entity:
        raise HTTPException(status_code=404, detail="Anaveri tipi bulunamadı")
    
    if entity.is_system:
        raise HTTPException(status_code=400, detail="Sistem anaveri tipleri silinemez")
    
    # Kayıt var mı kontrol et
    record_count = db.query(func.count(MasterData.id))\
        .filter(MasterData.entity_id == entity.id).scalar()
    
    if record_count > 0:
        raise HTTPException(
            status_code=400, 
            detail=f"Bu anaveri tipinde {record_count} kayıt var. Önce kayıtları silin."
        )
    
    db.delete(entity)
    db.commit()
    return None
