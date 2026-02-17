"""
Budget Entries API - Butce Girisleri Endpoint'leri
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_
from typing import Optional, List
import itertools
import json

from app.db.session import get_db
from app.models.budget_entry import (
    BudgetType, BudgetTypeMeasure, BudgetDefinition, BudgetDefinitionDimension,
    BudgetEntryRow, BudgetEntryCell, BudgetCellType, BudgetMeasureType,
    RuleSet, RuleSetItem, RuleType, CalculationSnapshot
)
from app.models.system_data import BudgetVersion, BudgetPeriod, BudgetParameter, ParameterVersion, BudgetCurrency
from app.models.dynamic.meta_entity import MetaEntity
from app.models.dynamic.master_data import MasterData
from app.models.dynamic.master_data_value import MasterDataValue
from app.models.dynamic.meta_attribute import MetaAttribute
from app.schemas.budget_entry import (
    BudgetTypeResponse, BudgetTypeListResponse,
    BudgetDefinitionCreate, BudgetDefinitionUpdate, BudgetDefinitionResponse,
    BudgetDefinitionListResponse, DimensionInfo,
    BudgetGridResponse, BudgetGridRow, CellData, PeriodInfo, BudgetTypeMeasureResponse,
    BudgetBulkSaveRequest, BudgetBulkSaveResponse,
    BudgetRowCurrencyBulkUpdate, BudgetRowCurrencyBulkResponse,
    GenerateRowsResponse,
    RuleSetCreate, RuleSetUpdate, RuleSetResponse, RuleSetListResponse,
    RuleSetItemResponse,
    CalculateRequest, CalculateResponse,
    UndoResponse
)
from decimal import Decimal

router = APIRouter(
    prefix="/budget-entries",
    tags=["Butce Girisleri"]
)


# ============ Helper Functions ============

def _build_definition_response(definition: BudgetDefinition, db: Session) -> dict:
    """Build definition response dict with related data."""
    dims = []
    for d in definition.dimensions:
        entity = db.query(MetaEntity).filter(MetaEntity.id == d.entity_id).first()
        dims.append({
            "id": d.id,
            "entity_id": d.entity_id,
            "entity_code": entity.code if entity else "",
            "entity_name": entity.default_name if entity else "",
            "sort_order": d.sort_order,
        })

    row_count = db.query(BudgetEntryRow).filter(
        BudgetEntryRow.budget_definition_id == definition.id
    ).count()

    return {
        "id": definition.id,
        "uuid": definition.uuid,
        "code": definition.code,
        "name": definition.name,
        "description": definition.description,
        "version_id": definition.version_id,
        "version_code": definition.version.code if definition.version else None,
        "version_name": definition.version.name if definition.version else None,
        "budget_type_id": definition.budget_type_id,
        "budget_type_code": definition.budget_type.code if definition.budget_type else None,
        "budget_type_name": definition.budget_type.name if definition.budget_type else None,
        "dimensions": dims,
        "status": definition.status.value if definition.status else "draft",
        "is_active": definition.is_active,
        "row_count": row_count,
        "created_by": definition.created_by,
        "created_date": definition.created_date,
        "updated_date": definition.updated_date,
    }


def _get_periods_for_version(db: Session, version: BudgetVersion) -> list:
    """Get all periods between version's start and end period."""
    if not version.start_period_id or not version.end_period_id:
        return []

    start_period = db.query(BudgetPeriod).filter(BudgetPeriod.id == version.start_period_id).first()
    end_period = db.query(BudgetPeriod).filter(BudgetPeriod.id == version.end_period_id).first()

    if not start_period or not end_period:
        return []

    periods = db.query(BudgetPeriod).filter(
        BudgetPeriod.code >= start_period.code,
        BudgetPeriod.code <= end_period.code,
        BudgetPeriod.is_active == True
    ).order_by(BudgetPeriod.code).all()

    return periods


def _generate_rows_for_definition(db: Session, definition: BudgetDefinition) -> dict:
    """Generate rows from cartesian product of dimension master data."""
    dimension_entities = db.query(BudgetDefinitionDimension).filter(
        BudgetDefinitionDimension.budget_definition_id == definition.id
    ).order_by(BudgetDefinitionDimension.sort_order).all()

    if not dimension_entities:
        return {"created_count": 0, "existing_count": 0, "total_count": 0}

    # Get master data for each dimension
    dimension_data = []
    for dim in dimension_entities:
        master_records = db.query(MasterData).filter(
            MasterData.entity_id == dim.entity_id,
            MasterData.is_active == True
        ).order_by(MasterData.sort_order, MasterData.code).all()
        dimension_data.append({
            "entity_id": dim.entity_id,
            "records": master_records
        })

    # Cartesian product
    record_lists = [d["records"] for d in dimension_data]
    entity_ids = [d["entity_id"] for d in dimension_data]

    if not all(record_lists):
        return {"created_count": 0, "existing_count": 0, "total_count": 0}

    combinations = list(itertools.product(*record_lists))

    created = 0
    existing = 0

    default_currency = db.query(BudgetCurrency).filter(
        BudgetCurrency.is_active == True
    ).order_by(BudgetCurrency.sort_order, BudgetCurrency.code).first()
    default_currency_code = default_currency.code if default_currency else "TL"

    for combo in combinations:
        dim_values = {}
        for i, record in enumerate(combo):
            dim_values[str(entity_ids[i])] = record.id

        # Check if row already exists
        existing_row = db.query(BudgetEntryRow).filter(
            BudgetEntryRow.budget_definition_id == definition.id,
            BudgetEntryRow.dimension_values == dim_values
        ).first()

        if existing_row:
            existing += 1
        else:
            new_row = BudgetEntryRow(
                budget_definition_id=definition.id,
                dimension_values=dim_values,
                currency_code=default_currency_code,
                is_active=True,
                sort_order=created + existing,
            )
            db.add(new_row)
            created += 1

    db.flush()
    total = db.query(BudgetEntryRow).filter(
        BudgetEntryRow.budget_definition_id == definition.id
    ).count()

    return {"created_count": created, "existing_count": existing, "total_count": total}


# ============ Budget Types ============

@router.get("/types", response_model=BudgetTypeListResponse)
def list_budget_types(
    is_active: Optional[bool] = None,
    db: Session = Depends(get_db)
):
    query = db.query(BudgetType).options(joinedload(BudgetType.measures))
    if is_active is not None:
        query = query.filter(BudgetType.is_active == is_active)
    types = query.order_by(BudgetType.sort_order).all()
    return {"items": types, "total": len(types)}


@router.get("/types/{type_id}", response_model=BudgetTypeResponse)
def get_budget_type(type_id: int, db: Session = Depends(get_db)):
    bt = db.query(BudgetType).options(
        joinedload(BudgetType.measures)
    ).filter(BudgetType.id == type_id).first()
    if not bt:
        raise HTTPException(status_code=404, detail="Butce tipi bulunamadi")
    return bt


# ============ Budget Definitions ============

@router.get("/definitions", response_model=BudgetDefinitionListResponse)
def list_definitions(
    version_id: Optional[int] = None,
    budget_type_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    query = db.query(BudgetDefinition).options(
        joinedload(BudgetDefinition.version),
        joinedload(BudgetDefinition.budget_type),
        joinedload(BudgetDefinition.dimensions),
    )
    if version_id:
        query = query.filter(BudgetDefinition.version_id == version_id)
    if budget_type_id:
        query = query.filter(BudgetDefinition.budget_type_id == budget_type_id)

    definitions = query.order_by(BudgetDefinition.sort_order, BudgetDefinition.id.desc()).all()

    items = [_build_definition_response(d, db) for d in definitions]
    return {"items": items, "total": len(items)}


@router.get("/definitions/{def_id}", response_model=BudgetDefinitionResponse)
def get_definition(def_id: int, db: Session = Depends(get_db)):
    definition = db.query(BudgetDefinition).options(
        joinedload(BudgetDefinition.version),
        joinedload(BudgetDefinition.budget_type),
        joinedload(BudgetDefinition.dimensions),
    ).filter(BudgetDefinition.id == def_id).first()

    if not definition:
        raise HTTPException(status_code=404, detail="Butce tanimi bulunamadi")

    return _build_definition_response(definition, db)


@router.post("/definitions", response_model=BudgetDefinitionResponse, status_code=201)
def create_definition(data: BudgetDefinitionCreate, db: Session = Depends(get_db)):
    # Validate version exists
    version = db.query(BudgetVersion).filter(BudgetVersion.id == data.version_id).first()
    if not version:
        raise HTTPException(status_code=400, detail="Versiyon bulunamadi")

    # Validate budget type exists
    budget_type = db.query(BudgetType).filter(BudgetType.id == data.budget_type_id).first()
    if not budget_type:
        raise HTTPException(status_code=400, detail="Butce tipi bulunamadi")

    # Auto-generate code/name if not provided
    code = data.code.upper() if data.code else f"{version.code}_{budget_type.code}".upper()
    name = data.name if data.name else f"{version.name} - {budget_type.name}"

    # Ensure unique code (append _N if needed)
    base_code = code
    counter = 1
    while db.query(BudgetDefinition).filter(BudgetDefinition.code == code).first():
        code = f"{base_code}_{counter}"
        counter += 1

    # Validate dimension entities exist
    for entity_id in data.dimension_entity_ids:
        entity = db.query(MetaEntity).filter(MetaEntity.id == entity_id).first()
        if not entity:
            raise HTTPException(status_code=400, detail=f"Anaveri tipi bulunamadi: {entity_id}")

    # Create definition
    definition = BudgetDefinition(
        version_id=data.version_id,
        budget_type_id=data.budget_type_id,
        code=code,
        name=name,
        description=data.description,
    )
    db.add(definition)
    db.flush()

    # Create dimensions
    for i, entity_id in enumerate(data.dimension_entity_ids):
        dim = BudgetDefinitionDimension(
            budget_definition_id=definition.id,
            entity_id=entity_id,
            sort_order=i,
        )
        db.add(dim)

    db.flush()

    # Auto-generate rows
    _generate_rows_for_definition(db, definition)

    db.commit()
    db.refresh(definition)

    # Reload with relationships
    definition = db.query(BudgetDefinition).options(
        joinedload(BudgetDefinition.version),
        joinedload(BudgetDefinition.budget_type),
        joinedload(BudgetDefinition.dimensions),
    ).filter(BudgetDefinition.id == definition.id).first()

    return _build_definition_response(definition, db)


@router.put("/definitions/{def_id}", response_model=BudgetDefinitionResponse)
def update_definition(def_id: int, data: BudgetDefinitionUpdate, db: Session = Depends(get_db)):
    definition = db.query(BudgetDefinition).options(
        joinedload(BudgetDefinition.version),
        joinedload(BudgetDefinition.budget_type),
        joinedload(BudgetDefinition.dimensions),
    ).filter(BudgetDefinition.id == def_id).first()

    if not definition:
        raise HTTPException(status_code=404, detail="Butce tanimi bulunamadi")

    if data.name is not None:
        definition.name = data.name
    if data.description is not None:
        definition.description = data.description
    if data.status is not None:
        definition.status = data.status

    db.commit()
    db.refresh(definition)

    return _build_definition_response(definition, db)


@router.delete("/definitions/{def_id}", status_code=204)
def delete_definition(def_id: int, db: Session = Depends(get_db)):
    definition = db.query(BudgetDefinition).filter(BudgetDefinition.id == def_id).first()
    if not definition:
        raise HTTPException(status_code=404, detail="Butce tanimi bulunamadi")

    if definition.status and definition.status.value == "locked":
        raise HTTPException(status_code=400, detail="Kilitli tanim silinemez")

    db.delete(definition)
    db.commit()


# ============ Grid Data ============

@router.get("/grid/{def_id}", response_model=BudgetGridResponse)
def get_grid(def_id: int, db: Session = Depends(get_db)):
    """Full grid data for a budget definition."""
    definition = db.query(BudgetDefinition).options(
        joinedload(BudgetDefinition.version),
        joinedload(BudgetDefinition.budget_type).joinedload(BudgetType.measures),
        joinedload(BudgetDefinition.dimensions),
    ).filter(BudgetDefinition.id == def_id).first()

    if not definition:
        raise HTTPException(status_code=404, detail="Butce tanimi bulunamadi")

    # Get periods for version
    periods = _get_periods_for_version(db, definition.version)
    period_infos = [
        PeriodInfo(id=p.id, code=p.code, name=p.name, year=p.year, month=p.month, quarter=p.quarter)
        for p in periods
    ]

    # Get measures
    measures = [m for m in definition.budget_type.measures if m.is_active]
    measure_responses = [
        BudgetTypeMeasureResponse(
            id=m.id, code=m.code, name=m.name,
            measure_type=m.measure_type.value, data_type=m.data_type.value,
            formula=m.formula, decimal_places=m.decimal_places,
            unit=m.unit, default_value=m.default_value,
            sort_order=m.sort_order, is_active=m.is_active,
        )
        for m in measures
    ]

    # Get all rows
    rows = db.query(BudgetEntryRow).filter(
        BudgetEntryRow.budget_definition_id == def_id,
        BudgetEntryRow.is_active == True
    ).order_by(BudgetEntryRow.sort_order).all()

    if not rows:
        def_response = _build_definition_response(definition, db)
        return BudgetGridResponse(
            definition=def_response,
            periods=period_infos,
            measures=measure_responses,
            rows=[],
            total_rows=0,
        )

    row_ids = [r.id for r in rows]

    # Get all cells in one query
    cells = db.query(BudgetEntryCell).filter(
        BudgetEntryCell.row_id.in_(row_ids)
    ).all()

    # Build cell lookup: {row_id: {period_id: {measure_code: cell}}}
    cell_lookup = {}
    for cell in cells:
        if cell.row_id not in cell_lookup:
            cell_lookup[cell.row_id] = {}
        if cell.period_id not in cell_lookup[cell.row_id]:
            cell_lookup[cell.row_id][cell.period_id] = {}
        cell_lookup[cell.row_id][cell.period_id][cell.measure_code] = cell

    # Resolve dimension display names
    # Collect all master_data_ids
    all_md_ids = set()
    for row in rows:
        for entity_id_str, md_id in row.dimension_values.items():
            all_md_ids.add(md_id)

    # Batch load master data
    md_lookup = {}
    if all_md_ids:
        master_records = db.query(MasterData).filter(MasterData.id.in_(list(all_md_ids))).all()
        for md in master_records:
            md_lookup[md.id] = {"id": md.id, "code": md.code, "name": md.name}

    # Build grid rows
    grid_rows = []
    for row in rows:
        # Resolve dimension values to display info
        dim_display = {}
        for entity_id_str, md_id in row.dimension_values.items():
            md_info = md_lookup.get(md_id, {"id": md_id, "code": "?", "name": "?"})
            dim_display[entity_id_str] = md_info

        # Build cells dict
        row_cells = {}
        for period in periods:
            period_cells = {}
            for measure in measures:
                cell = cell_lookup.get(row.id, {}).get(period.id, {}).get(measure.code)
                if cell:
                    period_cells[measure.code] = CellData(
                        value=float(cell.value) if cell.value is not None else None,
                        cell_type=cell.cell_type.value if cell.cell_type else "input"
                    )
                else:
                    period_cells[measure.code] = CellData(value=None, cell_type="input")
            row_cells[str(period.id)] = period_cells

        grid_rows.append(BudgetGridRow(
            row_id=row.id,
            dimension_values=dim_display,
            currency_code=row.currency_code,
            cells=row_cells,
        ))

    def_response = _build_definition_response(definition, db)

    return BudgetGridResponse(
        definition=def_response,
        periods=period_infos,
        measures=measure_responses,
        rows=grid_rows,
        total_rows=len(grid_rows),
    )


@router.post("/grid/{def_id}/save", response_model=BudgetBulkSaveResponse)
def save_grid(def_id: int, data: BudgetBulkSaveRequest, db: Session = Depends(get_db)):
    """Bulk save cells for a budget definition."""
    definition = db.query(BudgetDefinition).options(
        joinedload(BudgetDefinition.budget_type).joinedload(BudgetType.measures),
    ).filter(BudgetDefinition.id == def_id).first()

    if not definition:
        raise HTTPException(status_code=404, detail="Butce tanimi bulunamadi")

    if definition.status and definition.status.value == "locked":
        raise HTTPException(status_code=400, detail="Kilitli tanim uzerinde degisiklik yapilamaz")

    # Build input measure codes set
    input_measures = {
        m.code for m in definition.budget_type.measures
        if m.measure_type == BudgetMeasureType.input
    }

    saved = 0
    errors = []

    for cell_update in data.cells:
        # Only allow saving input measures
        if cell_update.measure_code not in input_measures:
            errors.append(f"'{cell_update.measure_code}' hesaplanan olcu, deger girilmez")
            continue

        # Upsert cell
        existing_cell = db.query(BudgetEntryCell).filter(
            BudgetEntryCell.row_id == cell_update.row_id,
            BudgetEntryCell.period_id == cell_update.period_id,
            BudgetEntryCell.measure_code == cell_update.measure_code,
        ).first()

        if existing_cell:
            existing_cell.value = cell_update.value
            existing_cell.cell_type = BudgetCellType.input
            existing_cell.is_manual_override = True
        else:
            new_cell = BudgetEntryCell(
                row_id=cell_update.row_id,
                period_id=cell_update.period_id,
                measure_code=cell_update.measure_code,
                value=cell_update.value,
                cell_type=BudgetCellType.input,
                is_manual_override=True,
            )
            db.add(new_cell)
        saved += 1

    db.commit()

    return BudgetBulkSaveResponse(saved_count=saved, errors=errors)


@router.put("/grid/{def_id}/rows/currency", response_model=BudgetRowCurrencyBulkResponse)
def update_row_currencies(def_id: int, data: BudgetRowCurrencyBulkUpdate, db: Session = Depends(get_db)):
    """Update currency_code for budget grid rows."""
    definition = db.query(BudgetDefinition).filter(BudgetDefinition.id == def_id).first()
    if not definition:
        raise HTTPException(status_code=404, detail="Butce tanimi bulunamadi")

    if definition.status and definition.status.value == "locked":
        raise HTTPException(status_code=400, detail="Kilitli tanim uzerinde degisiklik yapilamaz")

    if not data.rows:
        return BudgetRowCurrencyBulkResponse(updated_count=0, errors=[])

    active_codes = {
        c.code for c in db.query(BudgetCurrency).filter(BudgetCurrency.is_active == True).all()
    }

    updated = 0
    errors = []

    for row_update in data.rows:
        row = db.query(BudgetEntryRow).filter(
            BudgetEntryRow.id == row_update.row_id,
            BudgetEntryRow.budget_definition_id == def_id
        ).first()
        if not row:
            errors.append(f"Satir bulunamadi: {row_update.row_id}")
            continue

        if row_update.currency_code:
            code = row_update.currency_code.upper()
            if code not in active_codes:
                errors.append(f"Para birimi aktif degil veya bulunamadi: {code}")
                continue
            row.currency_code = code
        else:
            row.currency_code = None
        updated += 1

    db.commit()
    return BudgetRowCurrencyBulkResponse(updated_count=updated, errors=errors)


@router.post("/grid/{def_id}/generate-rows", response_model=GenerateRowsResponse)
def generate_rows(def_id: int, db: Session = Depends(get_db)):
    """(Re)generate rows from master data cartesian product."""
    definition = db.query(BudgetDefinition).options(
        joinedload(BudgetDefinition.dimensions),
    ).filter(BudgetDefinition.id == def_id).first()

    if not definition:
        raise HTTPException(status_code=404, detail="Butce tanimi bulunamadi")

    result = _generate_rows_for_definition(db, definition)
    db.commit()

    return GenerateRowsResponse(**result)


# ============ Rule Sets ============

def _build_rule_set_response(rs: RuleSet, db: Session) -> dict:
    """Build rule set response dict with items."""
    items = []
    for item in rs.items:
        item_dict = {
            "id": item.id,
            "rule_type": item.rule_type.value if item.rule_type else "fixed_value",
            "target_measure_code": item.target_measure_code,
            "condition_entity_id": item.condition_entity_id,
            "condition_entity_code": None,
            "condition_entity_name": None,
            "condition_attribute_code": item.condition_attribute_code,
            "condition_operator": item.condition_operator or "eq",
            "condition_value": item.condition_value,
            "apply_to_period_ids": item.apply_to_period_ids,
            "fixed_value": float(item.fixed_value) if item.fixed_value is not None else None,
            "parameter_id": item.parameter_id,
            "parameter_code": None,
            "parameter_name": None,
            "parameter_operation": item.parameter_operation or "multiply",
            "formula": item.formula,
            "currency_code": item.currency_code,
            "currency_source_entity_id": item.currency_source_entity_id,
            "currency_source_attribute_code": item.currency_source_attribute_code,
            "priority": item.priority or 0,
            "is_active": item.is_active,
            "sort_order": item.sort_order or 0,
        }
        if item.condition_entity_id:
            entity = db.query(MetaEntity).filter(MetaEntity.id == item.condition_entity_id).first()
            if entity:
                item_dict["condition_entity_code"] = entity.code
                item_dict["condition_entity_name"] = entity.default_name
        if item.parameter_id:
            param = db.query(BudgetParameter).filter(BudgetParameter.id == item.parameter_id).first()
            if param:
                item_dict["parameter_code"] = param.code
                item_dict["parameter_name"] = param.name
        items.append(item_dict)

    return {
        "id": rs.id,
        "uuid": rs.uuid,
        "budget_type_id": rs.budget_type_id,
        "code": rs.code,
        "name": rs.name,
        "description": rs.description,
        "items": items,
        "is_active": rs.is_active,
        "sort_order": rs.sort_order or 0,
        "created_date": rs.created_date,
        "updated_date": rs.updated_date,
    }


@router.get("/rule-sets", response_model=RuleSetListResponse)
def list_rule_sets(
    budget_type_id: Optional[int] = None,
    is_active: Optional[bool] = None,
    db: Session = Depends(get_db)
):
    query = db.query(RuleSet).options(joinedload(RuleSet.items))
    if budget_type_id is not None:
        query = query.filter(RuleSet.budget_type_id == budget_type_id)
    if is_active is not None:
        query = query.filter(RuleSet.is_active == is_active)
    rule_sets = query.order_by(RuleSet.sort_order).all()
    items = [_build_rule_set_response(rs, db) for rs in rule_sets]
    return {"items": items, "total": len(items)}


@router.get("/rule-sets/{rs_id}", response_model=RuleSetResponse)
def get_rule_set(rs_id: int, db: Session = Depends(get_db)):
    rs = db.query(RuleSet).options(joinedload(RuleSet.items)).filter(RuleSet.id == rs_id).first()
    if not rs:
        raise HTTPException(status_code=404, detail="Kural seti bulunamadi")
    return _build_rule_set_response(rs, db)


@router.post("/rule-sets", response_model=RuleSetResponse, status_code=201)
def create_rule_set(data: RuleSetCreate, db: Session = Depends(get_db)):
    # Validate budget type
    bt = db.query(BudgetType).filter(BudgetType.id == data.budget_type_id).first()
    if not bt:
        raise HTTPException(status_code=400, detail="Butce tipi bulunamadi")

    # Check code uniqueness
    existing = db.query(RuleSet).filter(RuleSet.code == data.code.upper()).first()
    if existing:
        raise HTTPException(status_code=400, detail=f"'{data.code.upper()}' kodu zaten kullaniliyor")

    rs = RuleSet(
        budget_type_id=data.budget_type_id,
        code=data.code.upper(),
        name=data.name,
        description=data.description,
    )
    db.add(rs)
    db.flush()

    # Create items
    for i, item_data in enumerate(data.items):
        item = RuleSetItem(
            rule_set_id=rs.id,
            rule_type=RuleType(item_data.rule_type),
            target_measure_code=item_data.target_measure_code,
            condition_entity_id=item_data.condition_entity_id,
            condition_attribute_code=item_data.condition_attribute_code,
            condition_operator=item_data.condition_operator,
            condition_value=item_data.condition_value,
            apply_to_period_ids=item_data.apply_to_period_ids,
            fixed_value=item_data.fixed_value,
            parameter_id=item_data.parameter_id,
            parameter_operation=item_data.parameter_operation,
            formula=item_data.formula,
            currency_code=item_data.currency_code,
            currency_source_entity_id=item_data.currency_source_entity_id,
            currency_source_attribute_code=item_data.currency_source_attribute_code,
            priority=item_data.priority,
            is_active=item_data.is_active,
            sort_order=i,
        )
        db.add(item)

    db.commit()
    db.refresh(rs)

    rs = db.query(RuleSet).options(joinedload(RuleSet.items)).filter(RuleSet.id == rs.id).first()
    return _build_rule_set_response(rs, db)


@router.put("/rule-sets/{rs_id}", response_model=RuleSetResponse)
def update_rule_set(rs_id: int, data: RuleSetUpdate, db: Session = Depends(get_db)):
    rs = db.query(RuleSet).options(joinedload(RuleSet.items)).filter(RuleSet.id == rs_id).first()
    if not rs:
        raise HTTPException(status_code=404, detail="Kural seti bulunamadi")

    if data.name is not None:
        rs.name = data.name
    if data.description is not None:
        rs.description = data.description
    if data.is_active is not None:
        rs.is_active = data.is_active

    # Replace items if provided
    if data.items is not None:
        # Delete old items
        db.query(RuleSetItem).filter(RuleSetItem.rule_set_id == rs.id).delete()
        db.flush()

        for i, item_data in enumerate(data.items):
            item = RuleSetItem(
                rule_set_id=rs.id,
                rule_type=RuleType(item_data.rule_type),
                target_measure_code=item_data.target_measure_code,
                condition_entity_id=item_data.condition_entity_id,
                condition_attribute_code=item_data.condition_attribute_code,
                condition_operator=item_data.condition_operator,
                condition_value=item_data.condition_value,
                apply_to_period_ids=item_data.apply_to_period_ids,
                fixed_value=item_data.fixed_value,
                parameter_id=item_data.parameter_id,
                parameter_operation=item_data.parameter_operation,
                formula=item_data.formula,
                currency_code=item_data.currency_code,
                currency_source_entity_id=item_data.currency_source_entity_id,
                currency_source_attribute_code=item_data.currency_source_attribute_code,
                priority=item_data.priority,
                is_active=item_data.is_active,
                sort_order=i,
            )
            db.add(item)

    db.commit()
    db.refresh(rs)

    rs = db.query(RuleSet).options(joinedload(RuleSet.items)).filter(RuleSet.id == rs.id).first()
    return _build_rule_set_response(rs, db)


@router.delete("/rule-sets/{rs_id}", status_code=204)
def delete_rule_set(rs_id: int, db: Session = Depends(get_db)):
    rs = db.query(RuleSet).filter(RuleSet.id == rs_id).first()
    if not rs:
        raise HTTPException(status_code=404, detail="Kural seti bulunamadi")
    db.delete(rs)
    db.commit()


# ============ Calculate ============

def _check_condition(row: BudgetEntryRow, item: RuleSetItem, db: Session) -> bool:
    """Check if a rule set item's condition matches the given row."""
    if not item.condition_entity_id or not item.condition_attribute_code:
        return True  # No condition = matches all rows

    entity_id_str = str(item.condition_entity_id)
    md_id = row.dimension_values.get(entity_id_str)
    if md_id is None:
        return False  # Row doesn't have this dimension

    attr_code_upper = item.condition_attribute_code.upper()

    # Handle built-in fields CODE and NAME (direct MasterData columns)
    if attr_code_upper in ("CODE", "NAME"):
        md = db.query(MasterData).filter(MasterData.id == md_id).first()
        if not md:
            return False
        actual_value = md.code if attr_code_upper == "CODE" else md.name
    else:
        # Resolve attribute_code to attribute_id via MetaAttribute
        attr = db.query(MetaAttribute).filter(
            MetaAttribute.entity_id == item.condition_entity_id,
            MetaAttribute.code == item.condition_attribute_code
        ).first()
        if not attr:
            return False

        # Get the master data value for the specified attribute
        md_value = db.query(MasterDataValue).filter(
            MasterDataValue.master_data_id == md_id,
            MasterDataValue.attribute_id == attr.id
        ).first()

        if md_value is None:
            return False

        actual_value = md_value.value or ""

    condition_value = item.condition_value or ""
    operator = item.condition_operator or "eq"

    if operator == "eq":
        return actual_value == condition_value
    elif operator == "ne":
        return actual_value != condition_value
    elif operator == "in":
        try:
            allowed = json.loads(condition_value) if condition_value.startswith("[") else [v.strip() for v in condition_value.split(",")]
            return actual_value in allowed
        except (json.JSONDecodeError, AttributeError):
            return False
    return False


def _get_row_attribute_value(row: BudgetEntryRow, entity_id: int | None, attribute_code: str | None, db: Session) -> str | None:
    """Resolve a master data attribute value for a row."""
    if not entity_id or not attribute_code:
        return None
    md_id = row.dimension_values.get(str(entity_id))
    if md_id is None:
        return None

    attr_code_upper = attribute_code.upper()
    if attr_code_upper in ("CODE", "NAME"):
        md = db.query(MasterData).filter(MasterData.id == md_id).first()
        if not md:
            return None
        return md.code if attr_code_upper == "CODE" else md.name

    attr = db.query(MetaAttribute).filter(
        MetaAttribute.entity_id == entity_id,
        MetaAttribute.code == attribute_code
    ).first()
    if not attr:
        return None

    md_value = db.query(MasterDataValue).filter(
        MasterDataValue.master_data_id == md_id,
        MasterDataValue.attribute_id == attr.id
    ).first()
    if md_value is None:
        return None
    return md_value.value


def _check_period(period_id: int, item: RuleSetItem) -> bool:
    """Check if a period is in the rule item's applicable periods."""
    if not item.apply_to_period_ids:
        return True  # null = all periods
    return period_id in item.apply_to_period_ids


def _evaluate_formula(formula: str, measure_values: dict) -> float | None:
    """Safely evaluate a formula like 'FIYAT * MIKTAR'."""
    if not formula:
        return None
    try:
        # Replace measure codes with values
        expr = formula
        for code, val in measure_values.items():
            expr = expr.replace(code, str(val if val is not None else 0))
        # Safe eval with only math operations
        allowed_chars = set("0123456789.+-*/(). ")
        if not all(c in allowed_chars for c in expr):
            return None
        result = eval(expr)
        return float(result)
    except Exception:
        return None


@router.post("/grid/{def_id}/calculate", response_model=CalculateResponse)
def calculate_grid(def_id: int, data: CalculateRequest, db: Session = Depends(get_db)):
    """Apply rule sets and calculate formulas for all cells."""
    definition = db.query(BudgetDefinition).options(
        joinedload(BudgetDefinition.version),
        joinedload(BudgetDefinition.budget_type).joinedload(BudgetType.measures),
    ).filter(BudgetDefinition.id == def_id).first()

    if not definition:
        raise HTTPException(status_code=404, detail="Butce tanimi bulunamadi")

    if definition.status and definition.status.value == "locked":
        raise HTTPException(status_code=400, detail="Kilitli tanim hesaplanamaz")

    # Load periods chronologically
    periods = _get_periods_for_version(db, definition.version)
    if not periods:
        raise HTTPException(status_code=400, detail="Versiyona ait donem bulunamadi")

    # Load all rows
    rows = db.query(BudgetEntryRow).filter(
        BudgetEntryRow.budget_definition_id == def_id,
        BudgetEntryRow.is_active == True
    ).all()

    if not rows:
        return CalculateResponse()

    row_ids = [r.id for r in rows]

    # Load all existing cells
    all_cells = db.query(BudgetEntryCell).filter(
        BudgetEntryCell.row_id.in_(row_ids)
    ).all()

    # ── Snapshot: save current state for undo ──
    snapshot_data = []
    for cell in all_cells:
        snapshot_data.append({
            "id": cell.id,
            "row_id": cell.row_id,
            "period_id": cell.period_id,
            "measure_code": cell.measure_code,
            "value": str(cell.value) if cell.value is not None else None,
            "cell_type": cell.cell_type.value if cell.cell_type else "input",
            "is_manual_override": cell.is_manual_override or False,
            "source_rule_id": cell.source_rule_id,
            "source_param_id": cell.source_param_id,
        })

    snapshot = CalculationSnapshot(
        budget_definition_id=def_id,
        snapshot_data=snapshot_data,
        rule_set_ids=data.rule_set_ids or [],
    )
    db.add(snapshot)
    db.flush()
    snapshot_id = snapshot.id

    # ── Reset Phase: delete all non-input cells (idempotency) ──
    non_input_ids = [
        c.id for c in all_cells
        if c.cell_type != BudgetCellType.input
    ]
    if non_input_ids:
        db.query(BudgetEntryCell).filter(
            BudgetEntryCell.id.in_(non_input_ids)
        ).delete(synchronize_session='fetch')
        db.flush()

    # Reload cells (only input cells remain)
    all_cells = db.query(BudgetEntryCell).filter(
        BudgetEntryCell.row_id.in_(row_ids)
    ).all()

    # Build mutable cell lookup: {row_id: {period_id: {measure_code: cell}}}
    cell_lookup = {}
    for cell in all_cells:
        cell_lookup.setdefault(cell.row_id, {}).setdefault(cell.period_id, {})[cell.measure_code] = cell

    # Load measures
    measures = {m.code: m for m in definition.budget_type.measures if m.is_active}
    input_measure_codes = {code for code, m in measures.items() if m.measure_type == BudgetMeasureType.input}
    calculated_measure_codes = {code for code, m in measures.items() if m.measure_type == BudgetMeasureType.calculated}

    # Load selected rule sets
    rule_set_items = []
    for rs_id in data.rule_set_ids:
        rs = db.query(RuleSet).options(joinedload(RuleSet.items)).filter(
            RuleSet.id == rs_id, RuleSet.is_active == True
        ).first()
        if rs:
            rule_set_items.extend([item for item in rs.items if item.is_active])

    # Sort by priority then sort_order
    rule_set_items.sort(key=lambda x: (x.priority or 0, x.sort_order or 0))

    calculated_cells = 0
    formula_cells = 0
    skipped_manual = 0
    errors = set()

    # Phase 0: Apply currency assignment rules (row-level)
    active_currency_codes = {
        c.code for c in db.query(BudgetCurrency).filter(BudgetCurrency.is_active == True).all()
    }
    currency_items = [item for item in rule_set_items if item.rule_type == RuleType.currency_assign]
    if currency_items:
        for item in currency_items:
            for row in rows:
                if not _check_condition(row, item, db):
                    continue

                code = None
                if item.currency_source_entity_id and item.currency_source_attribute_code:
                    value = _get_row_attribute_value(
                        row, item.currency_source_entity_id, item.currency_source_attribute_code, db
                    )
                    if value:
                        code = str(value).upper().strip()

                if not code and item.currency_code:
                    code = item.currency_code.upper().strip()

                if not code:
                    continue

                if code not in active_currency_codes:
                    errors.add(f"Para birimi aktif degil veya bulunamadi: {code}")
                    continue

                row.currency_code = code

    # Phase 1: Apply rule set items (fixed_value, parameter_multiplier)
    for item in rule_set_items:
        if item.rule_type in (RuleType.formula, RuleType.currency_assign):
            continue  # Formulas handled in Phase 3

        # Pre-compute parameter value for parameter_multiplier items
        param_value = None
        operation = None
        if item.rule_type == RuleType.parameter_multiplier:
            if not item.parameter_id:
                continue
            pv = db.query(ParameterVersion).filter(
                ParameterVersion.parameter_id == item.parameter_id,
                ParameterVersion.version_id == definition.version_id
            ).first()
            if not pv or not pv.value:
                continue
            try:
                param_value = float(pv.value)
            except (ValueError, TypeError):
                continue
            operation = item.parameter_operation or "multiply"

        for row in rows:
            if not _check_condition(row, item, db):
                continue

            # For parameter_multiplier: compute base value per row
            # Base = value in the period just before the first applicable period
            base_value_for_row = None  # None means cascading (no period filter)
            if item.rule_type == RuleType.parameter_multiplier and item.apply_to_period_ids:
                first_applicable_idx = None
                for pidx, p in enumerate(periods):
                    if p.id in item.apply_to_period_ids:
                        first_applicable_idx = pidx
                        break
                if first_applicable_idx is not None and first_applicable_idx > 0:
                    base_period = periods[first_applicable_idx - 1]
                    base_cell = cell_lookup.get(row.id, {}).get(base_period.id, {}).get(item.target_measure_code)
                    base_value_for_row = float(base_cell.value) if base_cell and base_cell.value is not None else 0.0
                else:
                    base_value_for_row = 0.0

            for period_idx, period in enumerate(periods):
                if not _check_period(period.id, item):
                    continue

                # Check manual override
                existing = cell_lookup.get(row.id, {}).get(period.id, {}).get(item.target_measure_code)
                if existing and existing.is_manual_override:
                    skipped_manual += 1
                    continue

                new_value = None

                if item.rule_type == RuleType.fixed_value:
                    new_value = item.fixed_value

                elif item.rule_type == RuleType.parameter_multiplier:
                    # Determine effective base
                    if base_value_for_row is not None:
                        # Period filter active: use fixed base for all applicable periods
                        effective_base = base_value_for_row
                    else:
                        # No period filter: cascading from previous period
                        if period_idx == 0:
                            effective_base = 0.0
                        else:
                            prev_period = periods[period_idx - 1]
                            prev_cell = cell_lookup.get(row.id, {}).get(prev_period.id, {}).get(item.target_measure_code)
                            effective_base = float(prev_cell.value) if prev_cell and prev_cell.value is not None else 0.0

                    if operation == "multiply":
                        new_value = effective_base * (1 + param_value / 100)
                    elif operation == "add":
                        new_value = effective_base + param_value
                    elif operation == "replace":
                        new_value = param_value

                if new_value is not None:
                    cell_type = BudgetCellType.parameter_calculated if item.rule_type == RuleType.parameter_multiplier else BudgetCellType.calculated

                    if existing:
                        existing.value = Decimal(str(new_value))
                        existing.cell_type = cell_type
                        existing.source_rule_id = item.id
                        if item.parameter_id:
                            existing.source_param_id = item.parameter_id
                    else:
                        new_cell = BudgetEntryCell(
                            row_id=row.id,
                            period_id=period.id,
                            measure_code=item.target_measure_code,
                            value=Decimal(str(new_value)),
                            cell_type=cell_type,
                            source_rule_id=item.id,
                            source_param_id=item.parameter_id,
                        )
                        db.add(new_cell)
                        db.flush()
                        cell_lookup.setdefault(row.id, {}).setdefault(period.id, {})[item.target_measure_code] = new_cell
                    calculated_cells += 1

    # Helper: Calculate built-in formula measures (e.g. TUTAR = FIYAT * MIKTAR)
    def _run_formula_measures():
        nonlocal formula_cells, skipped_manual
        for measure_code in calculated_measure_codes:
            measure = measures[measure_code]
            if not measure.formula:
                continue

            for row in rows:
                for period in periods:
                    existing = cell_lookup.get(row.id, {}).get(period.id, {}).get(measure_code)
                    if existing and existing.is_manual_override:
                        skipped_manual += 1
                        continue

                    measure_values = {}
                    for m_code in measures:
                        cell = cell_lookup.get(row.id, {}).get(period.id, {}).get(m_code)
                        measure_values[m_code] = float(cell.value) if cell and cell.value is not None else 0

                    result = _evaluate_formula(measure.formula, measure_values)
                    if result is not None:
                        if existing:
                            existing.value = Decimal(str(result))
                            existing.cell_type = BudgetCellType.calculated
                        else:
                            new_cell = BudgetEntryCell(
                                row_id=row.id,
                                period_id=period.id,
                                measure_code=measure_code,
                                value=Decimal(str(result)),
                                cell_type=BudgetCellType.calculated,
                            )
                            db.add(new_cell)
                            db.flush()
                            cell_lookup.setdefault(row.id, {}).setdefault(period.id, {})[measure_code] = new_cell
                        formula_cells += 1

    # Phase 2: Calculate formula measures (first pass)
    _run_formula_measures()

    # Phase 3: Apply formula-type rule items (may change input measures like FIYAT)
    # When a formula rule has period filter, use base period (period before first
    # applicable period) for measure_values so formulas like "FIYAT * 1.2" use
    # the base value rather than the current period's value from earlier rules.
    formula_items = [item for item in rule_set_items if item.rule_type == RuleType.formula]
    for item in formula_items:
        # Pre-compute base period for this item (if period filter is active)
        base_period_id = None
        if item.apply_to_period_ids:
            first_applicable_idx = None
            for pidx, p in enumerate(periods):
                if p.id in item.apply_to_period_ids:
                    first_applicable_idx = pidx
                    break
            if first_applicable_idx is not None and first_applicable_idx > 0:
                base_period_id = periods[first_applicable_idx - 1].id

        for row in rows:
            if not _check_condition(row, item, db):
                continue
            for period in periods:
                if not _check_period(period.id, item):
                    continue
                existing = cell_lookup.get(row.id, {}).get(period.id, {}).get(item.target_measure_code)
                if existing and existing.is_manual_override:
                    skipped_manual += 1
                    continue

                # Build measure_values from base period if available, else current period
                source_period_id = base_period_id if base_period_id is not None else period.id
                measure_values = {}
                for m_code in measures:
                    cell = cell_lookup.get(row.id, {}).get(source_period_id, {}).get(m_code)
                    measure_values[m_code] = float(cell.value) if cell and cell.value is not None else 0

                result = _evaluate_formula(item.formula, measure_values)
                if result is not None:
                    if existing:
                        existing.value = Decimal(str(result))
                        existing.cell_type = BudgetCellType.calculated
                        existing.source_rule_id = item.id
                    else:
                        new_cell = BudgetEntryCell(
                            row_id=row.id,
                            period_id=period.id,
                            measure_code=item.target_measure_code,
                            value=Decimal(str(result)),
                            cell_type=BudgetCellType.calculated,
                            source_rule_id=item.id,
                        )
                        db.add(new_cell)
                        db.flush()
                        cell_lookup.setdefault(row.id, {}).setdefault(period.id, {})[item.target_measure_code] = new_cell
                    formula_cells += 1

    # Phase 4: Re-calculate formula measures (second pass — picks up changes from Phase 3)
    if formula_items:
        _run_formula_measures()

    db.commit()

    return CalculateResponse(
        calculated_cells=calculated_cells,
        formula_cells=formula_cells,
        skipped_manual=skipped_manual,
        snapshot_id=snapshot_id,
        errors=sorted(errors),
    )


# ============ Undo Calculation ============

@router.post("/grid/{def_id}/undo/{snapshot_id}", response_model=UndoResponse)
def undo_calculation(def_id: int, snapshot_id: int, db: Session = Depends(get_db)):
    """Restore cells to pre-calculation state from a snapshot."""
    snapshot = db.query(CalculationSnapshot).filter(
        CalculationSnapshot.id == snapshot_id,
        CalculationSnapshot.budget_definition_id == def_id,
    ).first()

    if not snapshot:
        raise HTTPException(status_code=404, detail="Snapshot bulunamadi")

    # Get all current rows for this definition
    rows = db.query(BudgetEntryRow).filter(
        BudgetEntryRow.budget_definition_id == def_id,
        BudgetEntryRow.is_active == True
    ).all()
    row_ids = [r.id for r in rows]

    # Delete all current cells
    if row_ids:
        db.query(BudgetEntryCell).filter(
            BudgetEntryCell.row_id.in_(row_ids)
        ).delete(synchronize_session='fetch')
        db.flush()

    # Restore cells from snapshot
    restored = 0
    for cell_data in snapshot.snapshot_data:
        cell = BudgetEntryCell(
            row_id=cell_data["row_id"],
            period_id=cell_data["period_id"],
            measure_code=cell_data["measure_code"],
            value=Decimal(cell_data["value"]) if cell_data["value"] is not None else None,
            cell_type=BudgetCellType(cell_data["cell_type"]),
            is_manual_override=cell_data.get("is_manual_override", False),
            source_rule_id=cell_data.get("source_rule_id"),
            source_param_id=cell_data.get("source_param_id"),
        )
        db.add(cell)
        restored += 1

    # Delete the used snapshot
    db.delete(snapshot)
    db.commit()

    return UndoResponse(restored_cells=restored, snapshot_id=snapshot_id)
