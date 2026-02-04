"""
Master Data API - Anaveri Kayıt Yönetimi
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func
from typing import List, Optional, Dict, Any
import json
import csv
import io

from app.db.session import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.models.dynamic.meta_entity import MetaEntity
from app.models.dynamic.meta_attribute import MetaAttribute
from app.models.dynamic.master_data import MasterData
from app.models.dynamic.master_data_value import MasterDataValue
from app.schemas.dynamic.master_data import (
    MasterDataCreate,
    MasterDataUpdate,
    MasterDataResponse,
    MasterDataListResponse,
    MasterDataBulkCreate,
    MasterDataImport
)

router = APIRouter(prefix="/master-data", tags=["Master Data - Anaveri Kayıtları"])


def get_flat_values(db: Session, master_data: MasterData) -> Dict[str, Any]:
    """Alan değerlerini flat dict olarak döndür"""
    flat = {"CODE": master_data.code, "NAME": master_data.name}

    for val in master_data.values:
        attr = db.query(MetaAttribute).filter(MetaAttribute.id == val.attribute_id).first()
        if attr:
            # Reference tipinde reference_display kullan
            if val.reference_id:
                ref_record = db.query(MasterData).filter(MasterData.id == val.reference_id).first()
                if ref_record:
                    flat[attr.code] = f"{ref_record.code} - {ref_record.name}"
                else:
                    flat[attr.code] = val.value
            else:
                flat[attr.code] = val.value

    return flat


def enrich_response(db: Session, record: MasterData) -> MasterData:
    """Response'u zenginleştir"""
    entity = db.query(MetaEntity).filter(MetaEntity.id == record.entity_id).first()
    record.entity_code = entity.code if entity else ""
    record.entity_name = entity.default_name if entity else ""
    
    # Values'ı zenginleştir
    enriched_values = []
    for val in record.values:
        attr = db.query(MetaAttribute).filter(MetaAttribute.id == val.attribute_id).first()
        if attr:
            val.attribute_code = attr.code
            val.attribute_label = attr.default_label
            val.data_type = attr.data_type.value if hasattr(attr.data_type, 'value') else attr.data_type
            
            # Reference display
            if val.reference_id:
                ref_record = db.query(MasterData).filter(MasterData.id == val.reference_id).first()
                if ref_record:
                    val.reference_display = f"{ref_record.code} - {ref_record.name}"
            
            enriched_values.append(val)
    
    record.values = enriched_values
    record.flat_values = get_flat_values(db, record)
    
    return record


# CSV Export/Import
@router.get("/export/{entity_id}/csv")
async def export_master_data_csv(
    entity_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Anaveri kayıtlarını CSV olarak dışa aktar"""
    entity = db.query(MetaEntity).filter(MetaEntity.id == entity_id).first()
    if not entity:
        raise HTTPException(status_code=404, detail="Anaveri tipi bulunamadı")

    # Attribute'ları al (aktif olanlar)
    attributes = db.query(MetaAttribute).filter(
        MetaAttribute.entity_id == entity_id,
        MetaAttribute.is_active == True,
        MetaAttribute.is_code_field == False,
        MetaAttribute.is_name_field == False
    ).order_by(MetaAttribute.sort_order).all()

    # Kayıtları al
    records = db.query(MasterData).options(joinedload(MasterData.values))\
        .filter(MasterData.entity_id == entity_id)\
        .order_by(MasterData.sort_order, MasterData.code)\
        .all()

    # CSV oluştur
    output = io.StringIO()

    # Header satırı
    headers = ["CODE", "NAME"] + [attr.code for attr in attributes]
    writer = csv.writer(output, delimiter=';')
    writer.writerow(headers)

    # Veri satırları
    for record in records:
        # Değerleri dict'e çevir
        values_dict = {}
        for val in record.values:
            attr = next((a for a in attributes if a.id == val.attribute_id), None)
            if attr:
                values_dict[attr.code] = val.value or ""

        # Satırı oluştur
        row = [record.code, record.name]
        for attr in attributes:
            row.append(values_dict.get(attr.code, ""))

        writer.writerow(row)

    # Response oluştur
    output.seek(0)

    # UTF-8 BOM ekle (Excel'de Türkçe karakter sorunu için)
    content = '\ufeff' + output.getvalue()

    return StreamingResponse(
        io.BytesIO(content.encode('utf-8')),
        media_type="text/csv; charset=utf-8",
        headers={
            "Content-Disposition": f"attachment; filename={entity.code}_export.csv"
        }
    )


@router.post("/import/{entity_id}/csv", response_model=Dict[str, Any])
async def import_master_data_csv(
    entity_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """CSV dosyasından anaveri kayıtlarını içe aktar"""
    entity = db.query(MetaEntity).filter(MetaEntity.id == entity_id).first()
    if not entity:
        raise HTTPException(status_code=404, detail="Anaveri tipi bulunamadı")

    # Dosya tipini kontrol et
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="Sadece CSV dosyaları kabul edilir")

    # Dosyayı oku
    content = await file.read()

    # UTF-8 BOM varsa kaldır
    if content.startswith(b'\xef\xbb\xbf'):
        content = content[3:]

    try:
        text = content.decode('utf-8')
    except UnicodeDecodeError:
        try:
            text = content.decode('latin-1')
        except:
            raise HTTPException(status_code=400, detail="Dosya kodlaması okunamadı")

    # CSV'yi parse et (hem ; hem , delimiter'ını dene)
    reader = None
    for delimiter in [';', ',', '\t']:
        try:
            test_reader = csv.reader(io.StringIO(text), delimiter=delimiter)
            first_row = next(test_reader)
            if len(first_row) >= 2:  # En az CODE ve NAME olmalı
                reader = csv.DictReader(io.StringIO(text), delimiter=delimiter)
                break
        except:
            continue

    if reader is None:
        raise HTTPException(status_code=400, detail="CSV formatı okunamadı")

    # Attribute'ları al
    attributes = db.query(MetaAttribute).filter(
        MetaAttribute.entity_id == entity_id,
        MetaAttribute.is_active == True
    ).all()

    attr_map = {attr.code: attr for attr in attributes}

    created = 0
    updated = 0
    errors = []

    for idx, row in enumerate(reader):
        try:
            code = str(row.get("CODE", "")).strip().upper()
            name = str(row.get("NAME", "")).strip()

            if not code or not name:
                errors.append(f"Satır {idx + 2}: CODE ve NAME zorunlu")
                continue

            # Mevcut kayıt var mı?
            existing = db.query(MasterData).filter(
                MasterData.entity_id == entity_id,
                MasterData.code == code
            ).first()

            if existing:
                # Güncelle
                existing.name = name
                record = existing
                updated += 1
            else:
                # Yeni oluştur
                record = MasterData(
                    entity_id=entity_id,
                    code=code,
                    name=name
                )
                db.add(record)
                db.flush()
                created += 1

            # Değerleri işle
            for attr_code, value in row.items():
                if attr_code in ["CODE", "NAME"]:
                    continue

                attr = attr_map.get(attr_code)
                if not attr or attr.is_code_field or attr.is_name_field:
                    continue

                # Mevcut değer var mı?
                existing_val = db.query(MasterDataValue).filter(
                    MasterDataValue.master_data_id == record.id,
                    MasterDataValue.attribute_id == attr.id
                ).first()

                clean_value = str(value).strip() if value else None

                if existing_val:
                    existing_val.value = clean_value
                else:
                    new_val = MasterDataValue(
                        master_data_id=record.id,
                        attribute_id=attr.id,
                        value=clean_value
                    )
                    db.add(new_val)

        except Exception as e:
            errors.append(f"Satır {idx + 2}: {str(e)}")

    db.commit()

    return {
        "created": created,
        "updated": updated,
        "errors": errors,
        "total_processed": created + updated + len(errors)
    }


@router.get("/entity/{entity_id}", response_model=MasterDataListResponse)
async def list_master_data(
    entity_id: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=500),
    search: Optional[str] = None,
    is_active: Optional[bool] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Bir anaveri tipinin tüm kayıtlarını listele"""
    entity = db.query(MetaEntity).filter(MetaEntity.id == entity_id).first()
    if not entity:
        raise HTTPException(status_code=404, detail="Anaveri tipi bulunamadı")
    
    query = db.query(MasterData).filter(MasterData.entity_id == entity_id)
    
    if search:
        query = query.filter(
            (MasterData.code.ilike(f"%{search}%")) |
            (MasterData.name.ilike(f"%{search}%"))
        )
    
    if is_active is not None:
        query = query.filter(MasterData.is_active == is_active)
    
    total = query.count()
    
    items = query.options(joinedload(MasterData.values))\
        .order_by(MasterData.sort_order, MasterData.code)\
        .offset((page - 1) * page_size)\
        .limit(page_size)\
        .all()
    
    # Response'ları zenginleştir
    enriched_items = [enrich_response(db, item) for item in items]
    
    return MasterDataListResponse(
        items=enriched_items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=(total + page_size - 1) // page_size
    )


@router.get("/entity/{entity_id}/all", response_model=List[MasterDataResponse])
async def list_all_master_data(
    entity_id: int,
    is_active: bool = True,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Dropdown/select için tüm kayıtları getir (sayfalama yok)"""
    entity = db.query(MetaEntity).filter(MetaEntity.id == entity_id).first()
    if not entity:
        raise HTTPException(status_code=404, detail="Anaveri tipi bulunamadı")
    
    query = db.query(MasterData).filter(MasterData.entity_id == entity_id)
    
    if is_active:
        query = query.filter(MasterData.is_active == True)
    
    items = query.order_by(MasterData.sort_order, MasterData.code).all()
    
    return [enrich_response(db, item) for item in items]


@router.get("/{record_id}", response_model=MasterDataResponse)
async def get_master_data(
    record_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Kayıt detayı"""
    record = db.query(MasterData)\
        .options(joinedload(MasterData.values))\
        .filter(MasterData.id == record_id)\
        .first()
    
    if not record:
        raise HTTPException(status_code=404, detail="Kayıt bulunamadı")
    
    return enrich_response(db, record)


@router.get("/entity/{entity_id}/code/{code}", response_model=MasterDataResponse)
async def get_master_data_by_code(
    entity_id: int,
    code: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Kod ile kayıt getir"""
    record = db.query(MasterData)\
        .options(joinedload(MasterData.values))\
        .filter(MasterData.entity_id == entity_id, MasterData.code == code.upper())\
        .first()
    
    if not record:
        raise HTTPException(status_code=404, detail="Kayıt bulunamadı")
    
    return enrich_response(db, record)


@router.post("", response_model=MasterDataResponse, status_code=status.HTTP_201_CREATED)
async def create_master_data(
    data: MasterDataCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Yeni kayıt oluştur"""
    # Entity kontrolü
    entity = db.query(MetaEntity).filter(MetaEntity.id == data.entity_id).first()
    if not entity:
        raise HTTPException(status_code=404, detail="Anaveri tipi bulunamadı")
    
    # Kod kontrolü
    existing = db.query(MasterData).filter(
        MasterData.entity_id == data.entity_id,
        MasterData.code == data.code.upper()
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail=f"'{data.code}' kodu bu anaveri tipinde zaten var")
    
    # Kayıt oluştur
    record = MasterData(
        entity_id=data.entity_id,
        code=data.code.upper(),
        name=data.name,
        is_active=data.is_active,
        sort_order=data.sort_order
    )
    
    db.add(record)
    db.flush()  # ID almak için
    
    # Değerleri ekle
    if data.values:
        for val_data in data.values:
            # Attribute kontrolü
            attr = db.query(MetaAttribute).filter(
                MetaAttribute.id == val_data.attribute_id,
                MetaAttribute.entity_id == data.entity_id
            ).first()
            
            if not attr:
                continue
            
            # CODE ve NAME alanlarını atla (zaten record'da var)
            if attr.is_code_field or attr.is_name_field:
                continue
            
            value = MasterDataValue(
                master_data_id=record.id,
                attribute_id=val_data.attribute_id,
                value=str(val_data.value) if val_data.value is not None else None,
                reference_id=val_data.reference_id
            )
            db.add(value)
    
    db.commit()
    db.refresh(record)
    
    # Response için yeniden yükle
    record = db.query(MasterData)\
        .options(joinedload(MasterData.values))\
        .filter(MasterData.id == record.id)\
        .first()
    
    return enrich_response(db, record)


@router.put("/{record_id}", response_model=MasterDataResponse)
async def update_master_data(
    record_id: int,
    data: MasterDataUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Kayıt güncelle"""
    record = db.query(MasterData).filter(MasterData.id == record_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Kayıt bulunamadı")
    
    # Kod değişiyorsa kontrol et
    if data.code and data.code.upper() != record.code:
        existing = db.query(MasterData).filter(
            MasterData.entity_id == record.entity_id,
            MasterData.code == data.code.upper(),
            MasterData.id != record_id
        ).first()
        if existing:
            raise HTTPException(status_code=400, detail=f"'{data.code}' kodu zaten var")
        record.code = data.code.upper()
    
    if data.name is not None:
        record.name = data.name
    if data.is_active is not None:
        record.is_active = data.is_active
    if data.sort_order is not None:
        record.sort_order = data.sort_order
    
    # Değerleri güncelle
    if data.values is not None:
        # Mevcut değerleri sil
        db.query(MasterDataValue).filter(MasterDataValue.master_data_id == record.id).delete()
        
        # Yeni değerleri ekle
        for val_data in data.values:
            attr = db.query(MetaAttribute).filter(
                MetaAttribute.id == val_data.attribute_id,
                MetaAttribute.entity_id == record.entity_id
            ).first()
            
            if not attr or attr.is_code_field or attr.is_name_field:
                continue
            
            value = MasterDataValue(
                master_data_id=record.id,
                attribute_id=val_data.attribute_id,
                value=str(val_data.value) if val_data.value is not None else None,
                reference_id=val_data.reference_id
            )
            db.add(value)
    
    db.commit()
    
    # Response için yeniden yükle
    record = db.query(MasterData)\
        .options(joinedload(MasterData.values))\
        .filter(MasterData.id == record_id)\
        .first()
    
    return enrich_response(db, record)


@router.delete("/{record_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_master_data(
    record_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Kayıt sil"""
    record = db.query(MasterData).filter(MasterData.id == record_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Kayıt bulunamadı")
    
    # TODO: Fact data'da kullanılıyor mu kontrol et
    
    db.delete(record)
    db.commit()
    return None


@router.post("/import", response_model=Dict[str, Any])
async def import_master_data(
    data: MasterDataImport,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Excel/CSV'den toplu import (JSON formatında)"""
    entity = db.query(MetaEntity).filter(MetaEntity.id == data.entity_id).first()
    if not entity:
        raise HTTPException(status_code=404, detail="Anaveri tipi bulunamadı")
    
    # Attribute'ları al
    attributes = db.query(MetaAttribute).filter(
        MetaAttribute.entity_id == data.entity_id,
        MetaAttribute.is_active == True
    ).all()
    
    attr_map = {attr.code: attr for attr in attributes}
    
    created = 0
    updated = 0
    errors = []
    
    for idx, row in enumerate(data.data):
        try:
            code = str(row.get("CODE", "")).upper()
            name = str(row.get("NAME", ""))
            
            if not code or not name:
                errors.append(f"Satır {idx + 1}: CODE ve NAME zorunlu")
                continue
            
            # Mevcut kayıt var mı?
            existing = db.query(MasterData).filter(
                MasterData.entity_id == data.entity_id,
                MasterData.code == code
            ).first()
            
            if existing:
                # Güncelle
                existing.name = name
                record = existing
                updated += 1
            else:
                # Yeni oluştur
                record = MasterData(
                    entity_id=data.entity_id,
                    code=code,
                    name=name
                )
                db.add(record)
                db.flush()
                created += 1
            
            # Değerleri işle
            for attr_code, value in row.items():
                if attr_code in ["CODE", "NAME"]:
                    continue
                
                attr = attr_map.get(attr_code)
                if not attr:
                    continue
                
                # Mevcut değer var mı?
                existing_val = db.query(MasterDataValue).filter(
                    MasterDataValue.master_data_id == record.id,
                    MasterDataValue.attribute_id == attr.id
                ).first()
                
                if existing_val:
                    existing_val.value = str(value) if value is not None else None
                else:
                    new_val = MasterDataValue(
                        master_data_id=record.id,
                        attribute_id=attr.id,
                        value=str(value) if value is not None else None
                    )
                    db.add(new_val)
        
        except Exception as e:
            errors.append(f"Satır {idx + 1}: {str(e)}")
    
    db.commit()
    
    return {
        "created": created,
        "updated": updated,
        "errors": errors,
        "total_processed": len(data.data)
    }
