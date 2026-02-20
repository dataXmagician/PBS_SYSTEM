"""
Data Mapping Service - Staging -> Hedef Tablo Aktarim Servisi

Staging tablolarindaki verileri MasterData, sistem verileri
ve butce girisleri tablolarina aktarir.
"""

import logging
from datetime import datetime
from typing import Optional, List, Dict, Any

from sqlalchemy.orm import Session, joinedload
from sqlalchemy import text, func

from app.models.data_connection import (
    DataConnectionMapping, DataConnectionFieldMapping
)
from app.models.dynamic.master_data import MasterData
from app.models.dynamic.master_data_value import MasterDataValue
from app.models.dynamic.meta_attribute import MetaAttribute
from app.schemas.data_connection import MappingExecutionResult, MappingPreviewResponse

logger = logging.getLogger(__name__)


class DataMappingService:
    """Staging -> hedef tablo aktarim islemlerini yoneten sinif."""

    @staticmethod
    def execute_mapping(
        db: Session,
        mapping: DataConnectionMapping,
        triggered_by: str
    ) -> MappingExecutionResult:
        """
        Staging tablosundan hedef tabloya veri aktarimi yapar.
        Simdilik sadece MASTER_DATA hedefi destekleniyor.
        """
        target_type = mapping.target_type.value if hasattr(mapping.target_type, 'value') else str(mapping.target_type)

        if target_type == "master_data":
            return DataMappingService._execute_master_data_mapping(db, mapping)
        else:
            return MappingExecutionResult(
                success=False,
                message=f"'{target_type}' hedef tipi henuz desteklenmiyor.",
                processed=0, inserted=0, updated=0, errors=0
            )

    @staticmethod
    def _execute_master_data_mapping(
        db: Session,
        mapping: DataConnectionMapping
    ) -> MappingExecutionResult:
        """
        Staging -> MasterData + MasterDataValue aktarimi.
        Upsert: is_key_field ile eslestir, varsa guncelle, yoksa olustur.
        """
        query = mapping.query
        if not query or not query.staging_table_name or not query.staging_table_created:
            return MappingExecutionResult(
                success=False, message="Staging tablosu bulunamadi veya olusturulmamis.",
                processed=0, inserted=0, updated=0, errors=0
            )

        target_entity_id = mapping.target_entity_id
        if not target_entity_id:
            return MappingExecutionResult(
                success=False, message="Hedef entity (target_entity_id) belirtilmemis.",
                processed=0, inserted=0, updated=0, errors=0
            )

        field_mappings = mapping.field_mappings
        if not field_mappings:
            return MappingExecutionResult(
                success=False, message="Alan eslestirmeleri (field_mappings) bos.",
                processed=0, inserted=0, updated=0, errors=0
            )

        # Key field bul (genellikle code)
        key_fields = [fm for fm in field_mappings if fm.is_key_field]
        if not key_fields:
            return MappingExecutionResult(
                success=False, message="Anahtar alan (is_key_field) tanimlanmamis.",
                processed=0, inserted=0, updated=0, errors=0
            )

        # Entity'nin attribute'larini yukle
        attributes = db.query(MetaAttribute).filter(
            MetaAttribute.entity_id == target_entity_id
        ).all()
        attr_map = {a.code: a for a in attributes}

        # Staging'den tum veriyi oku
        table_name = query.staging_table_name
        result = db.execute(text(f'SELECT * FROM "{table_name}" ORDER BY _staging_id'))
        col_names = list(result.keys())
        all_rows = result.fetchall()

        processed = 0
        inserted = 0
        updated = 0
        errors = 0
        error_details = []

        for raw_row in all_rows:
            processed += 1
            try:
                row = {}
                for i, col_name in enumerate(col_names):
                    row[col_name] = raw_row[i]

                # Transform uygula ve degerleri hazirla
                transformed = {}
                for fm in field_mappings:
                    source_val = row.get(fm.source_column)
                    transformed_val = DataMappingService.apply_transform(
                        source_val, fm.transform_type, fm.transform_config
                    )
                    transformed[fm.target_field] = transformed_val

                # Key deger
                code_value = None
                name_value = None
                attribute_values = {}

                for fm in field_mappings:
                    target = fm.target_field.lower()
                    val = transformed[fm.target_field]

                    if target == "code":
                        code_value = val
                    elif target == "name":
                        name_value = val
                    else:
                        # Attribute olarak isle — "attr:" prefix'ini temizle
                        attr_key = fm.target_field
                        if attr_key.startswith("attr:"):
                            attr_key = attr_key[5:]
                        attribute_values[attr_key] = val

                if not code_value:
                    errors += 1
                    error_details.append(f"Satir {processed}: code degeri bos.")
                    continue

                # Mevcut kaydi ara (code ile)
                existing = db.query(MasterData).filter(
                    MasterData.entity_id == target_entity_id,
                    MasterData.code == str(code_value)
                ).first()

                if existing:
                    # Guncelle
                    if name_value:
                        existing.name = str(name_value)

                    # Attribute degerlerini guncelle
                    for attr_code, attr_val in attribute_values.items():
                        attr = attr_map.get(attr_code.upper()) or attr_map.get(attr_code)
                        if attr:
                            existing_val = db.query(MasterDataValue).filter(
                                MasterDataValue.master_data_id == existing.id,
                                MasterDataValue.attribute_id == attr.id
                            ).first()
                            if existing_val:
                                existing_val.value = str(attr_val) if attr_val is not None else None
                            else:
                                new_val = MasterDataValue(
                                    master_data_id=existing.id,
                                    attribute_id=attr.id,
                                    value=str(attr_val) if attr_val is not None else None
                                )
                                db.add(new_val)

                    updated += 1
                else:
                    # Yeni kayit olustur
                    new_record = MasterData(
                        entity_id=target_entity_id,
                        code=str(code_value),
                        name=str(name_value) if name_value else str(code_value)
                    )
                    db.add(new_record)
                    db.flush()  # ID almak icin

                    # Attribute degerlerini ekle
                    for attr_code, attr_val in attribute_values.items():
                        attr = attr_map.get(attr_code.upper()) or attr_map.get(attr_code)
                        if attr:
                            new_val = MasterDataValue(
                                master_data_id=new_record.id,
                                attribute_id=attr.id,
                                value=str(attr_val) if attr_val is not None else None
                            )
                            db.add(new_val)

                    inserted += 1

            except Exception as e:
                errors += 1
                error_details.append(f"Satir {processed}: {str(e)[:200]}")
                if errors > 100:
                    error_details.append("... 100'den fazla hata, islem durduruluyor.")
                    break

        db.commit()

        return MappingExecutionResult(
            success=errors == 0,
            message=f"Aktarim tamamlandi: {inserted} yeni, {updated} guncellenen, {errors} hata.",
            processed=processed,
            inserted=inserted,
            updated=updated,
            errors=errors,
            error_details=error_details[:50]  # Max 50 hata detayi
        )

    @staticmethod
    def preview_mapping(
        db: Session,
        mapping: DataConnectionMapping,
        limit: int = 20
    ) -> MappingPreviewResponse:
        """
        Mapping sonucunu dry-run olarak gosterir (DB'ye yazmaz).
        Staging'den veri okur, transform uygular, sonucu dondurur.
        """
        query = mapping.query
        if not query or not query.staging_table_name or not query.staging_table_created:
            return MappingPreviewResponse(columns=[], rows=[], total=0, target_info=None)

        field_mappings = mapping.field_mappings
        if not field_mappings:
            return MappingPreviewResponse(columns=[], rows=[], total=0, target_info=None)

        # Staging'den veri oku
        table_name = query.staging_table_name
        count_result = db.execute(text(f'SELECT COUNT(*) FROM "{table_name}"'))
        total = count_result.scalar() or 0

        result = db.execute(
            text(f'SELECT * FROM "{table_name}" ORDER BY _staging_id LIMIT :lim'),
            {"lim": limit}
        )
        col_names = list(result.keys())
        raw_rows = result.fetchall()

        # Transform uygula — "attr:" prefix'ini temizle
        def clean_target(t: str) -> str:
            return t[5:] if t.startswith("attr:") else t

        preview_columns = [clean_target(fm.target_field) for fm in field_mappings]
        preview_rows = []

        for raw_row in raw_rows:
            row = {}
            for i, col_name in enumerate(col_names):
                row[col_name] = raw_row[i]

            preview_row = {}
            for fm in field_mappings:
                source_val = row.get(fm.source_column)
                preview_row[clean_target(fm.target_field)] = DataMappingService.apply_transform(
                    source_val, fm.transform_type, fm.transform_config
                )
            preview_rows.append(preview_row)

        target_type = mapping.target_type.value if hasattr(mapping.target_type, 'value') else str(mapping.target_type)
        target_info = {
            "target_type": target_type,
            "target_entity_id": mapping.target_entity_id
        }

        return MappingPreviewResponse(
            columns=preview_columns,
            rows=preview_rows,
            total=total,
            target_info=target_info
        )

    @staticmethod
    def apply_transform(value: Any, transform_type: Optional[str], transform_config: Optional[dict]) -> Any:
        """Tek bir deger uzerine transform uygular."""
        if value is None:
            return None

        val_str = str(value)
        t = (transform_type or "none").lower()

        if t == "none" or t == "":
            return val_str
        elif t == "uppercase":
            return val_str.upper()
        elif t == "lowercase":
            return val_str.lower()
        elif t == "trim":
            return val_str.strip()
        elif t == "format_date":
            # Tarih format donusumu
            if transform_config:
                from_format = transform_config.get("from_format", "%Y-%m-%d")
                to_format = transform_config.get("to_format", "%Y-%m-%d")
                try:
                    dt = datetime.strptime(val_str, from_format)
                    return dt.strftime(to_format)
                except ValueError:
                    return val_str
            return val_str
        elif t == "lookup":
            # Gelecekte: baska bir tablodan deger cekme
            # Simdilik olduğu gibi dondur
            return val_str
        else:
            return val_str
