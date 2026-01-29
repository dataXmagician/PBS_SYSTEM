"""
Fact Data API - Veri Giriş Yönetimi
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, and_
from typing import List, Optional, Dict, Any
import json

from app.db.session import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.models.dynamic.meta_entity import MetaEntity
from app.models.dynamic.master_data import MasterData
from app.models.dynamic.fact_definition import FactDefinition, FactDimension
from app.models.dynamic.fact_measure import FactMeasure
from app.models.dynamic.fact_data import FactData, FactDataValue
from app.models.dynamic.dim_time import DimTime
from app.schemas.dynamic.fact_data import (
    FactDataCreate,
    FactDataUpdate,
    FactDataResponse,
    FactDataListResponse,
    FactDataBulkCreate,
    FactDataQuery
)

router = APIRouter(prefix="/fact-data", tags=["Fact Data - Veri Girişleri"])


def enrich_fact_data(db: Session, data: FactData) -> FactData:
    """Response'u zenginleştir"""
    # Dimension display
    dim_display = {}
    dim_values = json.loads(data.dimension_values) if isinstance(data.dimension_values, str) else data.dimension_values
    
    for entity_id_str, master_data_id in dim_values.items():
        entity = db.query(MetaEntity).filter(MetaEntity.id == int(entity_id_str)).first()
        master = db.query(MasterData).filter(MasterData.id == master_data_id).first()
        if entity and master:
            dim_display[entity.code] = f"{master.code} - {master.name}"
    
    data.dimension_display = dim_display
    data.dimension_values = dim_values
    
    # Values
    for val in data.values:
        measure = db.query(FactMeasure).filter(FactMeasure.id == val.measure_id).first()
        if measure:
            val.measure_code = measure.code
            val.measure_name = measure.name
    
    return data


@router.get("/definition/{fact_definition_id}", response_model=FactDataListResponse)
async def list_fact_data(
    fact_definition_id: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=500),
    version: Optional[str] = None,
    year: Optional[int] = None,
    month: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Bir şablonun verilerini listele"""
    fact_def = db.query(FactDefinition).filter(FactDefinition.id == fact_definition_id).first()
    if not fact_def:
        raise HTTPException(status_code=404, detail="Şablon bulunamadı")
    
    query = db.query(FactData)\
        .options(joinedload(FactData.values))\
        .filter(FactData.fact_definition_id == fact_definition_id)
    
    if version:
        query = query.filter(FactData.version == version.upper())
    if year:
        query = query.filter(FactData.year == year)
    if month:
        query = query.filter(FactData.month == month)
    
    total = query.count()
    
    items = query.order_by(FactData.year.desc(), FactData.month.desc(), FactData.id)\
        .offset((page - 1) * page_size)\
        .limit(page_size)\
        .all()
    
    enriched = [enrich_fact_data(db, item) for item in items]
    
    return FactDataListResponse(
        items=enriched,
        total=total,
        page=page,
        page_size=page_size
    )


@router.get("/{data_id}", response_model=FactDataResponse)
async def get_fact_data(
    data_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Veri detayı"""
    data = db.query(FactData)\
        .options(joinedload(FactData.values))\
        .filter(FactData.id == data_id)\
        .first()
    
    if not data:
        raise HTTPException(status_code=404, detail="Veri bulunamadı")
    
    return enrich_fact_data(db, data)


@router.post("", response_model=FactDataResponse, status_code=status.HTTP_201_CREATED)
async def create_fact_data(
    data: FactDataCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Yeni veri girişi"""
    # Şablon kontrolü
    fact_def = db.query(FactDefinition)\
        .options(joinedload(FactDefinition.dimensions))\
        .filter(FactDefinition.id == data.fact_definition_id)\
        .first()
    
    if not fact_def:
        raise HTTPException(status_code=404, detail="Şablon bulunamadı")
    
    # Boyut değerlerini kontrol et
    for entity_id_str, master_data_id in data.dimension_values.items():
        entity_id = int(entity_id_str)
        
        # Bu entity şablonda var mı?
        dim_exists = any(d.entity_id == entity_id for d in fact_def.dimensions)
        if not dim_exists:
            raise HTTPException(status_code=400, detail=f"Entity {entity_id} bu şablonda yok")
        
        # Master data var mı?
        master = db.query(MasterData).filter(
            MasterData.id == master_data_id,
            MasterData.entity_id == entity_id
        ).first()
        if not master:
            raise HTTPException(status_code=400, detail=f"Master data {master_data_id} bulunamadı")
    
    # Aynı kombinasyon var mı kontrol et
    dim_json = json.dumps(data.dimension_values, sort_keys=True)
    existing = db.query(FactData).filter(
        FactData.fact_definition_id == data.fact_definition_id,
        FactData.dimension_values == dim_json,
        FactData.year == data.year,
        FactData.month == data.month,
        FactData.version == data.version.upper()
    ).first()
    
    if existing:
        raise HTTPException(status_code=400, detail="Bu kombinasyon için veri zaten var")
    
    # Time dimension
    time_id = None
    if fact_def.include_time_dimension and data.year and data.month:
        time_record = db.query(DimTime).filter(
            DimTime.year == data.year,
            DimTime.month == data.month,
            DimTime.day == 1
        ).first()
        if time_record:
            time_id = time_record.id
    
    # Veri oluştur
    fact_data = FactData(
        fact_definition_id=data.fact_definition_id,
        dimension_values=dim_json,
        time_id=time_id,
        year=data.year,
        month=data.month,
        version=data.version.upper()
    )
    
    db.add(fact_data)
    db.flush()
    
    # Değerleri ekle
    for val_data in data.values:
        # Ölçü kontrolü
        measure = db.query(FactMeasure).filter(
            FactMeasure.id == val_data.measure_id,
            FactMeasure.fact_definition_id == data.fact_definition_id
        ).first()
        
        if not measure:
            continue
        
        value = FactDataValue(
            fact_data_id=fact_data.id,
            measure_id=val_data.measure_id,
            value=str(val_data.value) if val_data.value is not None else None
        )
        db.add(value)
    
    db.commit()
    
    # Yeniden yükle
    fact_data = db.query(FactData)\
        .options(joinedload(FactData.values))\
        .filter(FactData.id == fact_data.id)\
        .first()
    
    return enrich_fact_data(db, fact_data)


@router.put("/{data_id}", response_model=FactDataResponse)
async def update_fact_data(
    data_id: int,
    data: FactDataUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Veri güncelle"""
    fact_data = db.query(FactData).filter(FactData.id == data_id).first()
    if not fact_data:
        raise HTTPException(status_code=404, detail="Veri bulunamadı")
    
    # Mevcut değerleri sil
    db.query(FactDataValue).filter(FactDataValue.fact_data_id == data_id).delete()
    
    # Yeni değerleri ekle
    for val_data in data.values:
        measure = db.query(FactMeasure).filter(
            FactMeasure.id == val_data.measure_id,
            FactMeasure.fact_definition_id == fact_data.fact_definition_id
        ).first()
        
        if not measure:
            continue
        
        value = FactDataValue(
            fact_data_id=data_id,
            measure_id=val_data.measure_id,
            value=str(val_data.value) if val_data.value is not None else None
        )
        db.add(value)
    
    db.commit()
    
    # Yeniden yükle
    fact_data = db.query(FactData)\
        .options(joinedload(FactData.values))\
        .filter(FactData.id == data_id)\
        .first()
    
    return enrich_fact_data(db, fact_data)


@router.delete("/{data_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_fact_data(
    data_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Veri sil"""
    fact_data = db.query(FactData).filter(FactData.id == data_id).first()
    if not fact_data:
        raise HTTPException(status_code=404, detail="Veri bulunamadı")
    
    db.delete(fact_data)
    db.commit()
    return None


@router.post("/bulk", response_model=Dict[str, Any])
async def bulk_create_fact_data(
    data: FactDataBulkCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Toplu veri girişi"""
    fact_def = db.query(FactDefinition)\
        .options(
            joinedload(FactDefinition.dimensions),
            joinedload(FactDefinition.measures)
        )\
        .filter(FactDefinition.id == data.fact_definition_id)\
        .first()
    
    if not fact_def:
        raise HTTPException(status_code=404, detail="Şablon bulunamadı")
    
    # Entity ve measure map'leri oluştur
    entity_map = {}  # code -> id
    for dim in fact_def.dimensions:
        entity = db.query(MetaEntity).filter(MetaEntity.id == dim.entity_id).first()
        if entity:
            entity_map[entity.code] = entity.id
    
    measure_map = {m.code: m for m in fact_def.measures}
    
    # Master data map (her entity için code -> id)
    master_map = {}  # {entity_code: {master_code: master_id}}
    for entity_code, entity_id in entity_map.items():
        masters = db.query(MasterData).filter(MasterData.entity_id == entity_id).all()
        master_map[entity_code] = {m.code: m.id for m in masters}
    
    created = 0
    updated = 0
    errors = []
    
    for idx, row in enumerate(data.data):
        try:
            # Dimension değerlerini çıkar
            dim_values = {}
            year = row.get("YEAR")
            month = row.get("MONTH")
            
            for entity_code, entity_id in entity_map.items():
                master_code = row.get(entity_code)
                if not master_code:
                    errors.append(f"Satır {idx + 1}: {entity_code} eksik")
                    continue
                
                master_id = master_map.get(entity_code, {}).get(str(master_code).upper())
                if not master_id:
                    errors.append(f"Satır {idx + 1}: {entity_code}={master_code} bulunamadı")
                    continue
                
                dim_values[str(entity_id)] = master_id
            
            if len(dim_values) != len(entity_map):
                continue
            
            dim_json = json.dumps(dim_values, sort_keys=True)
            
            # Mevcut kayıt var mı?
            existing = db.query(FactData).filter(
                FactData.fact_definition_id == data.fact_definition_id,
                FactData.dimension_values == dim_json,
                FactData.year == year,
                FactData.month == month,
                FactData.version == data.version.upper()
            ).first()
            
            if existing:
                # Güncelle
                db.query(FactDataValue).filter(FactDataValue.fact_data_id == existing.id).delete()
                fact_data = existing
                updated += 1
            else:
                # Yeni oluştur
                fact_data = FactData(
                    fact_definition_id=data.fact_definition_id,
                    dimension_values=dim_json,
                    year=year,
                    month=month,
                    version=data.version.upper()
                )
                db.add(fact_data)
                db.flush()
                created += 1
            
            # Ölçü değerlerini ekle
            for measure_code, measure in measure_map.items():
                value = row.get(measure_code)
                if value is not None:
                    fact_value = FactDataValue(
                        fact_data_id=fact_data.id,
                        measure_id=measure.id,
                        value=str(value)
                    )
                    db.add(fact_value)
        
        except Exception as e:
            errors.append(f"Satır {idx + 1}: {str(e)}")
    
    db.commit()
    
    return {
        "created": created,
        "updated": updated,
        "errors": errors[:50],  # İlk 50 hata
        "total_errors": len(errors),
        "total_processed": len(data.data)
    }


@router.post("/query", response_model=FactDataListResponse)
async def query_fact_data(
    query: FactDataQuery,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Gelişmiş veri sorgulama"""
    fact_def = db.query(FactDefinition).filter(FactDefinition.id == query.fact_definition_id).first()
    if not fact_def:
        raise HTTPException(status_code=404, detail="Şablon bulunamadı")
    
    db_query = db.query(FactData)\
        .options(joinedload(FactData.values))\
        .filter(FactData.fact_definition_id == query.fact_definition_id)
    
    if query.version:
        db_query = db_query.filter(FactData.version == query.version.upper())
    
    if query.year_from:
        db_query = db_query.filter(FactData.year >= query.year_from)
    if query.year_to:
        db_query = db_query.filter(FactData.year <= query.year_to)
    if query.month_from:
        db_query = db_query.filter(FactData.month >= query.month_from)
    if query.month_to:
        db_query = db_query.filter(FactData.month <= query.month_to)
    
    # TODO: Dimension filter desteği eklenecek
    
    total = db_query.count()
    
    items = db_query.order_by(FactData.year, FactData.month)\
        .offset((query.page - 1) * query.page_size)\
        .limit(query.page_size)\
        .all()
    
    enriched = [enrich_fact_data(db, item) for item in items]
    
    return FactDataListResponse(
        items=enriched,
        total=total,
        page=query.page,
        page_size=query.page_size
    )
