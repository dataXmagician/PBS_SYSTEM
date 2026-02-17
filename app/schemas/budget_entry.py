"""
Budget Entry Schemas - Butce Girisleri Pydantic Semalari
"""

from pydantic import BaseModel, ConfigDict
from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime


# ============ Budget Type ============

class BudgetTypeMeasureResponse(BaseModel):
    id: int
    code: str
    name: str
    measure_type: str
    data_type: str
    formula: Optional[str] = None
    decimal_places: int = 2
    unit: Optional[str] = None
    default_value: Optional[str] = "0"
    sort_order: int = 0
    is_active: bool = True

    model_config = ConfigDict(from_attributes=True)


class BudgetTypeResponse(BaseModel):
    id: int
    uuid: UUID
    code: str
    name: str
    description: Optional[str] = None
    measures: List[BudgetTypeMeasureResponse] = []
    is_active: bool = True
    sort_order: int = 0

    model_config = ConfigDict(from_attributes=True)


class BudgetTypeListResponse(BaseModel):
    items: List[BudgetTypeResponse]
    total: int


# ============ Budget Definition ============

class DimensionInfo(BaseModel):
    id: int
    entity_id: int
    entity_code: str
    entity_name: str
    sort_order: int = 0


class BudgetDefinitionCreate(BaseModel):
    version_id: int
    budget_type_id: int
    code: Optional[str] = None
    name: Optional[str] = None
    description: Optional[str] = None
    dimension_entity_ids: List[int]


class BudgetDefinitionUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None


class BudgetDefinitionResponse(BaseModel):
    id: int
    uuid: UUID
    code: str
    name: str
    description: Optional[str] = None
    version_id: int
    version_code: Optional[str] = None
    version_name: Optional[str] = None
    budget_type_id: int
    budget_type_code: Optional[str] = None
    budget_type_name: Optional[str] = None
    dimensions: List[DimensionInfo] = []
    status: str = "draft"
    is_active: bool = True
    row_count: int = 0
    created_by: Optional[str] = None
    created_date: Optional[datetime] = None
    updated_date: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class BudgetDefinitionListResponse(BaseModel):
    items: List[BudgetDefinitionResponse]
    total: int


# ============ Budget Grid ============

class PeriodInfo(BaseModel):
    id: int
    code: str
    name: str
    year: int
    month: int
    quarter: int


class CellData(BaseModel):
    value: Optional[float] = None
    cell_type: str = "input"


class BudgetGridRow(BaseModel):
    row_id: int
    dimension_values: Dict[str, Any]  # {entity_id: {id, code, name}}
    currency_code: Optional[str] = "TL"
    cells: Dict[str, Dict[str, CellData]]  # {period_id: {measure_code: CellData}}


class BudgetGridResponse(BaseModel):
    definition: BudgetDefinitionResponse
    periods: List[PeriodInfo]
    measures: List[BudgetTypeMeasureResponse]
    rows: List[BudgetGridRow]
    total_rows: int = 0


class BudgetCellUpdate(BaseModel):
    row_id: int
    period_id: int
    measure_code: str
    value: Optional[float] = None


class BudgetBulkSaveRequest(BaseModel):
    cells: List[BudgetCellUpdate]


class BudgetBulkSaveResponse(BaseModel):
    saved_count: int = 0
    errors: List[str] = []


class BudgetRowCurrencyUpdate(BaseModel):
    row_id: int
    currency_code: Optional[str] = None


class BudgetRowCurrencyBulkUpdate(BaseModel):
    rows: List[BudgetRowCurrencyUpdate]


class BudgetRowCurrencyBulkResponse(BaseModel):
    updated_count: int = 0
    errors: List[str] = []


class GenerateRowsResponse(BaseModel):
    created_count: int = 0
    existing_count: int = 0
    total_count: int = 0


# ============ Rule Sets ============

class RuleSetItemCreate(BaseModel):
    rule_type: str  # fixed_value, parameter_multiplier, formula
    target_measure_code: str
    condition_entity_id: Optional[int] = None
    condition_attribute_code: Optional[str] = None
    condition_operator: str = "eq"
    condition_value: Optional[str] = None
    apply_to_period_ids: Optional[List[int]] = None
    fixed_value: Optional[float] = None
    parameter_id: Optional[int] = None
    parameter_operation: str = "multiply"
    formula: Optional[str] = None
    currency_code: Optional[str] = None
    currency_source_entity_id: Optional[int] = None
    currency_source_attribute_code: Optional[str] = None
    priority: int = 0
    is_active: bool = True
    sort_order: int = 0


class RuleSetItemResponse(BaseModel):
    id: int
    rule_type: str
    target_measure_code: str
    condition_entity_id: Optional[int] = None
    condition_entity_code: Optional[str] = None
    condition_entity_name: Optional[str] = None
    condition_attribute_code: Optional[str] = None
    condition_operator: str = "eq"
    condition_value: Optional[str] = None
    apply_to_period_ids: Optional[List[int]] = None
    fixed_value: Optional[float] = None
    parameter_id: Optional[int] = None
    parameter_code: Optional[str] = None
    parameter_name: Optional[str] = None
    parameter_operation: str = "multiply"
    formula: Optional[str] = None
    currency_code: Optional[str] = None
    currency_source_entity_id: Optional[int] = None
    currency_source_attribute_code: Optional[str] = None
    priority: int = 0
    is_active: bool = True
    sort_order: int = 0

    model_config = ConfigDict(from_attributes=True)


class RuleSetCreate(BaseModel):
    budget_type_id: int
    code: str
    name: str
    description: Optional[str] = None
    items: List[RuleSetItemCreate] = []


class RuleSetUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None
    items: Optional[List[RuleSetItemCreate]] = None


class RuleSetResponse(BaseModel):
    id: int
    uuid: UUID
    budget_type_id: int
    code: str
    name: str
    description: Optional[str] = None
    items: List[RuleSetItemResponse] = []
    is_active: bool = True
    sort_order: int = 0
    created_date: Optional[datetime] = None
    updated_date: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class RuleSetListResponse(BaseModel):
    items: List[RuleSetResponse]
    total: int


class CalculateRequest(BaseModel):
    rule_set_ids: Optional[List[int]] = []


class CalculateResponse(BaseModel):
    calculated_cells: int = 0
    formula_cells: int = 0
    skipped_manual: int = 0
    snapshot_id: Optional[int] = None
    errors: List[str] = []


class UndoResponse(BaseModel):
    restored_cells: int = 0
    snapshot_id: int = 0
