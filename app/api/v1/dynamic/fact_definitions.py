"""
Fact Definitions API - Veri Giriş Şablonu Yönetimi
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func
from typing import List, Optional

from app.db.session import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.models.dynamic.meta_entity import MetaEntity
from app.models.dynamic.fact_definition import FactDefinition, FactDimension
from app.models.dynamic.fact_measure import FactMeasure, MeasureType, AggregationType
from app.models.dynamic.fact_data import FactData
from app.schemas.dynamic.fact_definition import (
    FactDefinitionCreate,
    FactDefinitionUpdate,
    FactDefinitionResponse,
    FactDefinitionListResponse,
    FactDimensionCreate,
    FactMeasureCreate
)

router = APIRouter(prefix="/fact-definitions", tags=["Fact Definitions - Veri Giriş Şablonları"])


def enrich_fact_definition(db: Session, fact: FactDefinition) -> FactDefinition:
    """Response'u zenginleştir"""
    # Dimensions
    for dim in fact.dimensions:
        entity = db.query(MetaEntity).filter(MetaEntity.id == dim.entity_id).first()
        if entity:
            dim.entity_code = entity.code
            dim.entity_name = entity.default_name
    
    # Data count
    fact.data_count = db.query(func.count(FactData.id))\
        .filter(FactData.fact_definition_id == fact.id).scalar()
    
    return fact


@router.get("", response_model=FactDefinitionListResponse)
async def list_fact_definitions(
    is_active: Optional[bool] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Tüm şablonları listele"""
    query = db.query(FactDefinition)\
        .options(
            joinedload(FactDefinition.dimensions),
            joinedload(FactDefinition.measures)
        )
    
    if is_active is not None:
        query = query.filter(FactDefinition.is_active == is_active)
    
    items = query.order_by(FactDefinition.code).all()
    
    enriched = [enrich_fact_definition(db, item) for item in items]
    
    return FactDefinitionListResponse(
        items=enriched,
        total=len(enriched)
    )


@router.get("/{fact_id}", response_model=FactDefinitionResponse)
async def get_fact_definition(
    fact_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Şablon detayı"""
    fact = db.query(FactDefinition)\
        .options(
            joinedload(FactDefinition.dimensions),
            joinedload(FactDefinition.measures)
        )\
        .filter(FactDefinition.id == fact_id)\
        .first()
    
    if not fact:
        raise HTTPException(status_code=404, detail="Şablon bulunamadı")
    
    return enrich_fact_definition(db, fact)


@router.get("/code/{code}", response_model=FactDefinitionResponse)
async def get_fact_definition_by_code(
    code: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Kod ile şablon getir"""
    fact = db.query(FactDefinition)\
        .options(
            joinedload(FactDefinition.dimensions),
            joinedload(FactDefinition.measures)
        )\
        .filter(FactDefinition.code == code.upper())\
        .first()
    
    if not fact:
        raise HTTPException(status_code=404, detail="Şablon bulunamadı")
    
    return enrich_fact_definition(db, fact)


@router.post("", response_model=FactDefinitionResponse, status_code=status.HTTP_201_CREATED)
async def create_fact_definition(
    data: FactDefinitionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Yeni şablon oluştur"""
    # Kod kontrolü
    existing = db.query(FactDefinition).filter(FactDefinition.code == data.code.upper()).first()
    if existing:
        raise HTTPException(status_code=400, detail=f"'{data.code}' kodu zaten var")
    
    # Entity'leri kontrol et
    for dim in data.dimensions:
        entity = db.query(MetaEntity).filter(MetaEntity.id == dim.entity_id).first()
        if not entity:
            raise HTTPException(status_code=400, detail=f"Entity ID {dim.entity_id} bulunamadı")
    
    # Şablon oluştur
    fact = FactDefinition(
        code=data.code.upper(),
        name=data.name,
        description=data.description,
        include_time_dimension=data.include_time_dimension,
        time_granularity=data.time_granularity.value
    )
    
    db.add(fact)
    db.flush()
    
    # Boyutları ekle
    for idx, dim_data in enumerate(data.dimensions):
        dim = FactDimension(
            fact_definition_id=fact.id,
            entity_id=dim_data.entity_id,
            sort_order=dim_data.sort_order or idx,
            is_required=dim_data.is_required
        )
        db.add(dim)
    
    # Ölçüleri ekle
    for idx, measure_data in enumerate(data.measures):
        measure = FactMeasure(
            fact_definition_id=fact.id,
            code=measure_data.code.upper(),
            name=measure_data.name,
            measure_type=MeasureType(measure_data.measure_type.value),
            aggregation=AggregationType(measure_data.aggregation.value),
            decimal_places=measure_data.decimal_places,
            unit=measure_data.unit,
            default_value=measure_data.default_value,
            is_required=measure_data.is_required,
            is_calculated=measure_data.is_calculated,
            formula=measure_data.formula,
            sort_order=measure_data.sort_order or idx
        )
        db.add(measure)
    
    db.commit()
    
    # Yeniden yükle
    fact = db.query(FactDefinition)\
        .options(
            joinedload(FactDefinition.dimensions),
            joinedload(FactDefinition.measures)
        )\
        .filter(FactDefinition.id == fact.id)\
        .first()
    
    return enrich_fact_definition(db, fact)


@router.put("/{fact_id}", response_model=FactDefinitionResponse)
async def update_fact_definition(
    fact_id: int,
    data: FactDefinitionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Şablon güncelle"""
    fact = db.query(FactDefinition).filter(FactDefinition.id == fact_id).first()
    if not fact:
        raise HTTPException(status_code=404, detail="Şablon bulunamadı")
    
    update_data = data.dict(exclude_unset=True)
    
    if "time_granularity" in update_data:
        update_data["time_granularity"] = update_data["time_granularity"].value
    
    for field, value in update_data.items():
        setattr(fact, field, value)
    
    db.commit()
    
    # Yeniden yükle
    fact = db.query(FactDefinition)\
        .options(
            joinedload(FactDefinition.dimensions),
            joinedload(FactDefinition.measures)
        )\
        .filter(FactDefinition.id == fact_id)\
        .first()
    
    return enrich_fact_definition(db, fact)


@router.delete("/{fact_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_fact_definition(
    fact_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Şablon sil"""
    fact = db.query(FactDefinition).filter(FactDefinition.id == fact_id).first()
    if not fact:
        raise HTTPException(status_code=404, detail="Şablon bulunamadı")
    
    # Veri var mı kontrol et
    data_count = db.query(func.count(FactData.id))\
        .filter(FactData.fact_definition_id == fact.id).scalar()
    
    if data_count > 0:
        raise HTTPException(
            status_code=400,
            detail=f"Bu şablonda {data_count} veri kaydı var. Önce verileri silin."
        )
    
    db.delete(fact)
    db.commit()
    return None


# === Dimension Endpoints ===

@router.post("/{fact_id}/dimensions", response_model=FactDefinitionResponse)
async def add_dimension(
    fact_id: int,
    data: FactDimensionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Şablona boyut ekle"""
    fact = db.query(FactDefinition).filter(FactDefinition.id == fact_id).first()
    if not fact:
        raise HTTPException(status_code=404, detail="Şablon bulunamadı")
    
    entity = db.query(MetaEntity).filter(MetaEntity.id == data.entity_id).first()
    if not entity:
        raise HTTPException(status_code=400, detail="Entity bulunamadı")
    
    # Zaten var mı?
    existing = db.query(FactDimension).filter(
        FactDimension.fact_definition_id == fact_id,
        FactDimension.entity_id == data.entity_id
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Bu boyut zaten ekli")
    
    dim = FactDimension(
        fact_definition_id=fact_id,
        entity_id=data.entity_id,
        sort_order=data.sort_order,
        is_required=data.is_required
    )
    db.add(dim)
    db.commit()
    
    return await get_fact_definition(fact_id, db, current_user)


@router.delete("/{fact_id}/dimensions/{dimension_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_dimension(
    fact_id: int,
    dimension_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Şablondan boyut kaldır"""
    dim = db.query(FactDimension).filter(
        FactDimension.id == dimension_id,
        FactDimension.fact_definition_id == fact_id
    ).first()
    
    if not dim:
        raise HTTPException(status_code=404, detail="Boyut bulunamadı")
    
    db.delete(dim)
    db.commit()
    return None


# === Measure Endpoints ===

@router.post("/{fact_id}/measures", response_model=FactDefinitionResponse)
async def add_measure(
    fact_id: int,
    data: FactMeasureCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Şablona ölçü ekle"""
    fact = db.query(FactDefinition).filter(FactDefinition.id == fact_id).first()
    if not fact:
        raise HTTPException(status_code=404, detail="Şablon bulunamadı")
    
    # Kod kontrolü
    existing = db.query(FactMeasure).filter(
        FactMeasure.fact_definition_id == fact_id,
        FactMeasure.code == data.code.upper()
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail=f"'{data.code}' ölçüsü zaten var")
    
    measure = FactMeasure(
        fact_definition_id=fact_id,
        code=data.code.upper(),
        name=data.name,
        measure_type=MeasureType(data.measure_type.value),
        aggregation=AggregationType(data.aggregation.value),
        decimal_places=data.decimal_places,
        unit=data.unit,
        default_value=data.default_value,
        is_required=data.is_required,
        is_calculated=data.is_calculated,
        formula=data.formula,
        sort_order=data.sort_order
    )
    db.add(measure)
    db.commit()
    
    return await get_fact_definition(fact_id, db, current_user)


@router.delete("/{fact_id}/measures/{measure_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_measure(
    fact_id: int,
    measure_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Şablondan ölçü kaldır"""
    measure = db.query(FactMeasure).filter(
        FactMeasure.id == measure_id,
        FactMeasure.fact_definition_id == fact_id
    ).first()
    
    if not measure:
        raise HTTPException(status_code=404, detail="Ölçü bulunamadı")
    
    db.delete(measure)
    db.commit()
    return None
