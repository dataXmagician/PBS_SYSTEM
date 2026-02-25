"""
DWH Mapping Service - DWH -> Hedef Sistem Esleme Servisi

DWH tablolarindaki verileri MasterData, SystemData (versiyon/donem/parametre)
ve BudgetEntry tablolarina aktarir.
"""

import logging
from datetime import datetime
from typing import Optional, List, Dict, Any

from sqlalchemy.orm import Session, joinedload
from sqlalchemy import text

from app.models.dwh import DwhMapping, DwhFieldMapping, DwhTable
from app.models.dynamic.master_data import MasterData
from app.models.dynamic.master_data_value import MasterDataValue
from app.models.dynamic.meta_attribute import MetaAttribute
from app.models.system_data import (
    BudgetVersion, BudgetPeriod, BudgetParameter, ParameterVersion
)
from app.models.budget_entry import (
    BudgetDefinition, BudgetDefinitionDimension, BudgetEntryRow, BudgetEntryCell,
    BudgetCellType
)
from app.schemas.dwh import DwhMappingExecutionResult, DwhMappingPreview

logger = logging.getLogger(__name__)


class DwhMappingService:
    """DWH -> hedef sistem esleme servisi."""

    @staticmethod
    def execute_mapping(
        db: Session,
        mapping: DwhMapping,
        triggered_by: str
    ) -> DwhMappingExecutionResult:
        """
        DWH tablosundan hedef sisteme veri aktarimi yapar.
        target_type'a gore ilgili handler'a yonlendirir.
        """
        target_type = mapping.target_type
        if hasattr(target_type, 'value'):
            target_type = target_type.value

        handler_map = {
            "master_data": DwhMappingService._execute_master_data_mapping,
            "system_version": DwhMappingService._execute_system_version_mapping,
            "system_period": DwhMappingService._execute_system_period_mapping,
            "system_parameter": DwhMappingService._execute_system_parameter_mapping,
            "budget_entry": DwhMappingService._execute_budget_entry_mapping,
        }

        handler = handler_map.get(target_type)
        if not handler:
            return DwhMappingExecutionResult(
                success=False,
                message=f"'{target_type}' hedef tipi desteklenmiyor."
            )

        try:
            return handler(db, mapping)
        except Exception as e:
            logger.error(f"DWH mapping hatasi ({target_type}): {e}")
            return DwhMappingExecutionResult(
                success=False,
                message=f"Esleme hatasi: {str(e)[:500]}",
                error_details=[str(e)]
            )

    # ============ Target Handlers ============

    @staticmethod
    def _execute_master_data_mapping(
        db: Session,
        mapping: DwhMapping
    ) -> DwhMappingExecutionResult:
        """
        DWH -> MasterData + MasterDataValue upsert.
        DataMappingService pattern'ini takip eder, kaynak DWH tablosu.
        target_field: code, name, attr:{attribute_code}
        """
        dwh_table = mapping.dwh_table
        if not dwh_table or not dwh_table.table_created:
            return DwhMappingExecutionResult(
                success=False, message="DWH tablosu bulunamadi veya olusturulmamis."
            )

        target_entity_id = mapping.target_entity_id
        if not target_entity_id:
            return DwhMappingExecutionResult(
                success=False, message="Hedef entity (target_entity_id) belirtilmemis."
            )

        field_mappings = mapping.field_mappings
        if not field_mappings:
            return DwhMappingExecutionResult(
                success=False, message="Alan eslestirmeleri bos."
            )

        key_fields = [fm for fm in field_mappings if fm.is_key_field]
        if not key_fields:
            return DwhMappingExecutionResult(
                success=False, message="Anahtar alan (is_key_field) tanimlanmamis."
            )

        # Entity attribute'larini yukle
        attributes = db.query(MetaAttribute).filter(
            MetaAttribute.entity_id == target_entity_id
        ).all()
        attr_map = {a.code: a for a in attributes}

        # DWH'dan veri oku
        rows_data = DwhMappingService._read_dwh_data(db, dwh_table)

        processed = 0
        inserted = 0
        updated = 0
        errors = 0
        error_details = []

        for row in rows_data:
            processed += 1
            try:
                transformed = DwhMappingService._apply_field_transforms(row, field_mappings)

                code_value = None
                name_value = None
                attribute_values = {}

                for fm in field_mappings:
                    target = fm.target_field.lower()
                    val = transformed.get(fm.target_field)

                    if target == "code":
                        code_value = val
                    elif target == "name":
                        name_value = val
                    else:
                        attr_key = fm.target_field
                        if attr_key.startswith("attr:"):
                            attr_key = attr_key[5:]
                        attribute_values[attr_key] = val

                if not code_value:
                    errors += 1
                    error_details.append(f"Satir {processed}: code degeri bos.")
                    continue

                # Upsert
                existing = db.query(MasterData).filter(
                    MasterData.entity_id == target_entity_id,
                    MasterData.code == str(code_value)
                ).first()

                if existing:
                    if name_value:
                        existing.name = str(name_value)
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
                                db.add(MasterDataValue(
                                    master_data_id=existing.id,
                                    attribute_id=attr.id,
                                    value=str(attr_val) if attr_val is not None else None
                                ))
                    updated += 1
                else:
                    new_record = MasterData(
                        entity_id=target_entity_id,
                        code=str(code_value),
                        name=str(name_value) if name_value else str(code_value)
                    )
                    db.add(new_record)
                    db.flush()
                    for attr_code, attr_val in attribute_values.items():
                        attr = attr_map.get(attr_code.upper()) or attr_map.get(attr_code)
                        if attr:
                            db.add(MasterDataValue(
                                master_data_id=new_record.id,
                                attribute_id=attr.id,
                                value=str(attr_val) if attr_val is not None else None
                            ))
                    inserted += 1

            except Exception as e:
                errors += 1
                error_details.append(f"Satir {processed}: {str(e)[:200]}")
                if errors > 100:
                    error_details.append("100'den fazla hata, islem durduruluyor.")
                    break

        db.commit()
        return DwhMappingExecutionResult(
            success=errors == 0,
            message=f"Aktarim tamamlandi: {inserted} yeni, {updated} guncellenen, {errors} hata.",
            processed=processed, inserted=inserted, updated=updated, errors=errors,
            error_details=error_details[:50]
        )

    @staticmethod
    def _execute_system_version_mapping(
        db: Session,
        mapping: DwhMapping
    ) -> DwhMappingExecutionResult:
        """
        DWH -> BudgetVersion upsert.
        target_field: code (key), name, description, is_active
        """
        dwh_table = mapping.dwh_table
        if not dwh_table or not dwh_table.table_created:
            return DwhMappingExecutionResult(
                success=False, message="DWH tablosu bulunamadi veya olusturulmamis."
            )

        field_mappings = mapping.field_mappings
        if not field_mappings:
            return DwhMappingExecutionResult(success=False, message="Alan eslestirmeleri bos.")

        rows_data = DwhMappingService._read_dwh_data(db, dwh_table)

        processed = 0
        inserted = 0
        updated = 0
        errors = 0
        error_details = []

        for row in rows_data:
            processed += 1
            try:
                transformed = DwhMappingService._apply_field_transforms(row, field_mappings)

                code_value = transformed.get("code")
                if not code_value:
                    errors += 1
                    error_details.append(f"Satir {processed}: code degeri bos.")
                    continue

                existing = db.query(BudgetVersion).filter(
                    BudgetVersion.code == str(code_value)
                ).first()

                if existing:
                    if "name" in transformed and transformed["name"]:
                        existing.name = str(transformed["name"])
                    if "description" in transformed:
                        existing.description = str(transformed["description"]) if transformed["description"] else None
                    if "is_active" in transformed:
                        existing.is_active = str(transformed["is_active"]).lower() in ("true", "1", "yes", "evet")
                    updated += 1
                else:
                    import uuid as uuid_lib
                    new_version = BudgetVersion(
                        uuid=uuid_lib.uuid4(),
                        code=str(code_value),
                        name=str(transformed.get("name", code_value)),
                        description=str(transformed.get("description", "")) if transformed.get("description") else None,
                        is_active=True,
                    )
                    db.add(new_version)
                    inserted += 1

            except Exception as e:
                errors += 1
                error_details.append(f"Satir {processed}: {str(e)[:200]}")
                if errors > 100:
                    break

        db.commit()
        return DwhMappingExecutionResult(
            success=errors == 0,
            message=f"Versiyon aktarimi: {inserted} yeni, {updated} guncellenen, {errors} hata.",
            processed=processed, inserted=inserted, updated=updated, errors=errors,
            error_details=error_details[:50]
        )

    @staticmethod
    def _execute_system_period_mapping(
        db: Session,
        mapping: DwhMapping
    ) -> DwhMappingExecutionResult:
        """
        DWH -> BudgetPeriod upsert.
        target_field: code (key, format: yyyy-MM), name (opsiyonel, auto generate)
        Auto: year/month/quarter code'dan cikarilir.
        """
        dwh_table = mapping.dwh_table
        if not dwh_table or not dwh_table.table_created:
            return DwhMappingExecutionResult(
                success=False, message="DWH tablosu bulunamadi veya olusturulmamis."
            )

        field_mappings = mapping.field_mappings
        if not field_mappings:
            return DwhMappingExecutionResult(success=False, message="Alan eslestirmeleri bos.")

        rows_data = DwhMappingService._read_dwh_data(db, dwh_table)

        processed = 0
        inserted = 0
        updated = 0
        errors = 0
        error_details = []

        for row in rows_data:
            processed += 1
            try:
                transformed = DwhMappingService._apply_field_transforms(row, field_mappings)

                code_value = transformed.get("code")
                if not code_value:
                    errors += 1
                    error_details.append(f"Satir {processed}: code degeri bos.")
                    continue

                # yyyy-MM formatindan year/month cikar
                code_str = str(code_value).strip()
                try:
                    parts = code_str.split("-")
                    year = int(parts[0])
                    month = int(parts[1])
                except (IndexError, ValueError):
                    errors += 1
                    error_details.append(f"Satir {processed}: Gecersiz kod formati '{code_str}' (beklenen: yyyy-MM).")
                    continue

                quarter = BudgetPeriod.get_quarter(month)
                name_value = transformed.get("name") or BudgetPeriod.generate_name(year, month)

                existing = db.query(BudgetPeriod).filter(
                    BudgetPeriod.code == code_str
                ).first()

                if existing:
                    existing.name = str(name_value)
                    existing.year = year
                    existing.month = month
                    existing.quarter = quarter
                    updated += 1
                else:
                    import uuid as uuid_lib
                    new_period = BudgetPeriod(
                        uuid=uuid_lib.uuid4(),
                        code=code_str,
                        name=str(name_value),
                        year=year,
                        month=month,
                        quarter=quarter,
                        is_active=True,
                    )
                    db.add(new_period)
                    inserted += 1

            except Exception as e:
                errors += 1
                error_details.append(f"Satir {processed}: {str(e)[:200]}")
                if errors > 100:
                    break

        db.commit()
        return DwhMappingExecutionResult(
            success=errors == 0,
            message=f"Donem aktarimi: {inserted} yeni, {updated} guncellenen, {errors} hata.",
            processed=processed, inserted=inserted, updated=updated, errors=errors,
            error_details=error_details[:50]
        )

    @staticmethod
    def _execute_system_parameter_mapping(
        db: Session,
        mapping: DwhMapping
    ) -> DwhMappingExecutionResult:
        """
        DWH -> BudgetParameter + ParameterVersion upsert.
        target_field: code (key), name, value_type, version_code, value
        version_code -> BudgetVersion.id cozumlenir.
        ParameterVersion upsert: (parameter_id, version_id) bazli.
        """
        dwh_table = mapping.dwh_table
        if not dwh_table or not dwh_table.table_created:
            return DwhMappingExecutionResult(
                success=False, message="DWH tablosu bulunamadi veya olusturulmamis."
            )

        field_mappings = mapping.field_mappings
        if not field_mappings:
            return DwhMappingExecutionResult(success=False, message="Alan eslestirmeleri bos.")

        # Versiyon cache'i
        versions = db.query(BudgetVersion).all()
        version_map = {v.code: v for v in versions}

        rows_data = DwhMappingService._read_dwh_data(db, dwh_table)

        processed = 0
        inserted = 0
        updated = 0
        errors = 0
        error_details = []

        for row in rows_data:
            processed += 1
            try:
                transformed = DwhMappingService._apply_field_transforms(row, field_mappings)

                code_value = transformed.get("code")
                if not code_value:
                    errors += 1
                    error_details.append(f"Satir {processed}: code degeri bos.")
                    continue

                code_str = str(code_value).strip()

                # Parametre upsert
                existing_param = db.query(BudgetParameter).filter(
                    BudgetParameter.code == code_str
                ).first()

                if existing_param:
                    if "name" in transformed and transformed["name"]:
                        existing_param.name = str(transformed["name"])
                    param = existing_param
                    updated += 1
                else:
                    import uuid as uuid_lib
                    from app.models.system_data import ParameterValueType
                    value_type_str = str(transformed.get("value_type", "sayi")).lower()
                    # value_type enum cozumle
                    vt = ParameterValueType.sayi
                    for member in ParameterValueType:
                        if member.value == value_type_str:
                            vt = member
                            break

                    param = BudgetParameter(
                        uuid=uuid_lib.uuid4(),
                        code=code_str,
                        name=str(transformed.get("name", code_str)),
                        description=str(transformed.get("description", "")) if transformed.get("description") else None,
                        value_type=vt,
                        is_active=True,
                    )
                    db.add(param)
                    db.flush()
                    inserted += 1

                # ParameterVersion upsert (version_code + value varsa)
                version_code = transformed.get("version_code")
                param_value = transformed.get("value")

                if version_code and param_value is not None:
                    version = version_map.get(str(version_code).strip())
                    if version:
                        existing_pv = db.query(ParameterVersion).filter(
                            ParameterVersion.parameter_id == param.id,
                            ParameterVersion.version_id == version.id
                        ).first()

                        if existing_pv:
                            existing_pv.value = str(param_value)
                        else:
                            db.add(ParameterVersion(
                                parameter_id=param.id,
                                version_id=version.id,
                                value=str(param_value)
                            ))
                    else:
                        error_details.append(
                            f"Satir {processed}: Versiyon bulunamadi: '{version_code}'"
                        )

            except Exception as e:
                errors += 1
                error_details.append(f"Satir {processed}: {str(e)[:200]}")
                if errors > 100:
                    break

        db.commit()
        return DwhMappingExecutionResult(
            success=errors == 0,
            message=f"Parametre aktarimi: {inserted} yeni, {updated} guncellenen, {errors} hata.",
            processed=processed, inserted=inserted, updated=updated, errors=errors,
            error_details=error_details[:50]
        )

    @staticmethod
    def _execute_budget_entry_mapping(
        db: Session,
        mapping: DwhMapping
    ) -> DwhMappingExecutionResult:
        """
        DWH -> BudgetEntryRow + BudgetEntryCell upsert (en karmasik).
        target_field convention'lari:
          - dim:{entity_id} -> MasterData code -> dimension_values JSONB
          - period -> BudgetPeriod code (yyyy-MM) -> period_id
          - measure:{measure_code} -> Olcu degeri (numeric)
          - currency -> Para birimi kodu
        """
        dwh_table = mapping.dwh_table
        if not dwh_table or not dwh_table.table_created:
            return DwhMappingExecutionResult(
                success=False, message="DWH tablosu bulunamadi veya olusturulmamis."
            )

        definition_id = mapping.target_definition_id
        if not definition_id:
            return DwhMappingExecutionResult(
                success=False, message="Hedef BudgetDefinition (target_definition_id) belirtilmemis."
            )

        definition = db.query(BudgetDefinition).filter(
            BudgetDefinition.id == definition_id
        ).first()
        if not definition:
            return DwhMappingExecutionResult(
                success=False, message=f"BudgetDefinition bulunamadi: {definition_id}"
            )

        field_mappings = mapping.field_mappings
        if not field_mappings:
            return DwhMappingExecutionResult(success=False, message="Alan eslestirmeleri bos.")

        # Cache'ler
        # Period cache: code -> id
        periods = db.query(BudgetPeriod).all()
        period_map = {p.code: p.id for p in periods}

        # MasterData cache: (entity_id, code) -> master_data_id
        # Boyut entity ID'leri bul
        dim_entity_ids = set()
        for fm in field_mappings:
            if fm.target_field.startswith("dim:"):
                try:
                    eid = int(fm.target_field[4:])
                    dim_entity_ids.add(eid)
                except ValueError:
                    pass

        md_cache = {}
        for eid in dim_entity_ids:
            records = db.query(MasterData).filter(MasterData.entity_id == eid).all()
            for r in records:
                md_cache[(eid, r.code)] = r.id

        rows_data = DwhMappingService._read_dwh_data(db, dwh_table)

        processed = 0
        inserted = 0
        updated = 0
        errors = 0
        error_details = []

        for row in rows_data:
            processed += 1
            try:
                transformed = DwhMappingService._apply_field_transforms(row, field_mappings)

                # 1. Dimension values cozumle
                dimension_values = {}
                period_id = None
                currency_code = None
                measure_values = {}

                for fm in field_mappings:
                    tf = fm.target_field
                    val = transformed.get(tf)

                    if tf.startswith("dim:"):
                        # dim:{entity_id} -> MasterData code'u cozumle
                        try:
                            entity_id = int(tf[4:])
                        except ValueError:
                            continue
                        if val:
                            md_id = md_cache.get((entity_id, str(val)))
                            if md_id:
                                dimension_values[str(entity_id)] = md_id
                            else:
                                error_details.append(
                                    f"Satir {processed}: MasterData bulunamadi: entity={entity_id}, code='{val}'"
                                )
                    elif tf == "period":
                        if val:
                            pid = period_map.get(str(val).strip())
                            if pid:
                                period_id = pid
                            else:
                                error_details.append(
                                    f"Satir {processed}: Donem bulunamadi: '{val}'"
                                )
                    elif tf == "currency":
                        currency_code = str(val) if val else None
                    elif tf.startswith("measure:"):
                        measure_code = tf[8:]
                        if val is not None:
                            try:
                                measure_values[measure_code] = float(str(val).replace(",", "."))
                            except (ValueError, TypeError):
                                measure_values[measure_code] = 0

                if not dimension_values:
                    errors += 1
                    error_details.append(f"Satir {processed}: Boyut degerleri cozumlenemedi.")
                    continue

                if not period_id:
                    errors += 1
                    error_details.append(f"Satir {processed}: Donem cozumlenemedi.")
                    continue

                # 2. BudgetEntryRow bul/olustur (dimension_values JSONB esitligi)
                import json
                dim_json = json.dumps(dimension_values, sort_keys=True)

                # JSONB equality icin cast ile karsilastir
                existing_row = None
                candidate_rows = db.query(BudgetEntryRow).filter(
                    BudgetEntryRow.budget_definition_id == definition_id
                ).all()

                for cr in candidate_rows:
                    cr_dims = cr.dimension_values or {}
                    if json.dumps(cr_dims, sort_keys=True, default=str) == dim_json:
                        existing_row = cr
                        break

                if existing_row:
                    entry_row = existing_row
                    if currency_code:
                        entry_row.currency_code = currency_code
                else:
                    import uuid as uuid_lib
                    entry_row = BudgetEntryRow(
                        uuid=uuid_lib.uuid4(),
                        budget_definition_id=definition_id,
                        dimension_values=dimension_values,
                        currency_code=currency_code or "TL",
                        is_active=True,
                    )
                    db.add(entry_row)
                    db.flush()

                # 3. BudgetEntryCell upsert: (row_id, period_id, measure_code)
                for measure_code, value in measure_values.items():
                    existing_cell = db.query(BudgetEntryCell).filter(
                        BudgetEntryCell.row_id == entry_row.id,
                        BudgetEntryCell.period_id == period_id,
                        BudgetEntryCell.measure_code == measure_code
                    ).first()

                    if existing_cell:
                        existing_cell.value = value
                        updated += 1
                    else:
                        db.add(BudgetEntryCell(
                            row_id=entry_row.id,
                            period_id=period_id,
                            measure_code=measure_code,
                            value=value,
                            cell_type=BudgetCellType.input,
                        ))
                        inserted += 1

            except Exception as e:
                errors += 1
                error_details.append(f"Satir {processed}: {str(e)[:200]}")
                if errors > 100:
                    error_details.append("100'den fazla hata, islem durduruluyor.")
                    break

        db.commit()
        return DwhMappingExecutionResult(
            success=errors == 0,
            message=f"Butce girisi aktarimi: {inserted} yeni, {updated} guncellenen, {errors} hata.",
            processed=processed, inserted=inserted, updated=updated, errors=errors,
            error_details=error_details[:50]
        )

    # ============ Preview ============

    @staticmethod
    def preview_mapping(
        db: Session,
        mapping: DwhMapping,
        limit: int = 20
    ) -> DwhMappingPreview:
        """
        Esleme onizleme: DWH verisini transform edip gosterir (DB'ye yazmaz).
        """
        dwh_table = mapping.dwh_table
        if not dwh_table or not dwh_table.table_created:
            return DwhMappingPreview(columns=[], rows=[], total=0)

        field_mappings = mapping.field_mappings
        if not field_mappings:
            return DwhMappingPreview(columns=[], rows=[], total=0)

        # DWH'dan veri oku (limitli)
        table_name = dwh_table.table_name
        count_result = db.execute(text(f'SELECT COUNT(*) FROM "{table_name}"'))
        total = count_result.scalar() or 0

        result = db.execute(
            text(f'SELECT * FROM "{table_name}" ORDER BY "_dwh_id" LIMIT :lim'),
            {"lim": limit}
        )
        col_names = list(result.keys())
        raw_rows = result.fetchall()

        # Transform uygula
        def clean_target(t: str) -> str:
            if t.startswith("attr:"):
                return t[5:]
            return t

        preview_columns = [clean_target(fm.target_field) for fm in field_mappings]
        preview_rows = []

        for raw_row in raw_rows:
            row = {}
            for i, col_name in enumerate(col_names):
                row[col_name] = raw_row[i]

            preview_row = {}
            for fm in field_mappings:
                source_val = row.get(fm.source_column)
                preview_row[clean_target(fm.target_field)] = DwhMappingService._apply_transform(
                    source_val, fm.transform_type, fm.transform_config
                )
            preview_rows.append(preview_row)

        target_type = mapping.target_type
        if hasattr(target_type, 'value'):
            target_type = target_type.value

        return DwhMappingPreview(
            columns=preview_columns,
            rows=preview_rows,
            total=total,
            target_info=f"{target_type} (entity_id={mapping.target_entity_id})"
        )

    # ============ Helpers ============

    @staticmethod
    def _read_dwh_data(db: Session, dwh_table: DwhTable) -> List[Dict]:
        """DWH tablosundan tum veriyi dict listesi olarak okur."""
        table_name = dwh_table.table_name
        result = db.execute(text(f'SELECT * FROM "{table_name}" ORDER BY "_dwh_id"'))
        col_names = list(result.keys())
        raw_rows = result.fetchall()

        rows = []
        for raw_row in raw_rows:
            row = {}
            for i, col_name in enumerate(col_names):
                row[col_name] = raw_row[i]
            rows.append(row)
        return rows

    @staticmethod
    def _apply_field_transforms(
        row: Dict,
        field_mappings: List[DwhFieldMapping]
    ) -> Dict:
        """Tum field mapping'ler icin transform uygular."""
        transformed = {}
        for fm in field_mappings:
            source_val = row.get(fm.source_column)
            transformed[fm.target_field] = DwhMappingService._apply_transform(
                source_val, fm.transform_type, fm.transform_config
            )
        return transformed

    @staticmethod
    def _apply_transform(value: Any, transform_type: Optional[str], transform_config: Optional[dict]) -> Any:
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
            return val_str
        else:
            return val_str
