"""
DWH (Data Warehouse) Schemas - Veri Ambarı Pydantic Şemaları
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Any
from datetime import datetime


# ============ DwhTable Schemas ============

class DwhTableCreate(BaseModel):
    code: str = Field(..., min_length=1, max_length=100)
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=500)
    is_active: bool = True


class DwhTableFromStaging(BaseModel):
    code: str = Field(..., min_length=1, max_length=100)
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=500)


class DwhTableUpdate(BaseModel):
    code: Optional[str] = Field(None, min_length=1, max_length=100)
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=500)
    is_active: Optional[bool] = None


class DwhColumnResponse(BaseModel):
    id: int
    dwh_table_id: int
    column_name: str
    data_type: str
    is_nullable: bool
    is_primary_key: bool
    is_incremental_key: bool
    max_length: Optional[int] = None
    sort_order: int

    class Config:
        from_attributes = True


class DwhTableResponse(BaseModel):
    id: int
    uuid: str
    code: str
    name: str
    description: Optional[str] = None
    source_type: str
    source_query_id: Optional[int] = None
    table_name: str
    table_created: bool
    is_active: bool
    sort_order: int
    columns: List[DwhColumnResponse] = []
    transfer_count: int = 0
    mapping_count: int = 0
    row_count: Optional[int] = None
    created_date: datetime
    updated_date: datetime

    class Config:
        from_attributes = True


class DwhTableListResponse(BaseModel):
    items: List[DwhTableResponse]
    total: int


# ============ DwhColumn Schemas ============

class DwhColumnCreate(BaseModel):
    column_name: str = Field(..., min_length=1, max_length=200)
    data_type: str = Field(default="string")
    is_nullable: bool = True
    is_primary_key: bool = False
    is_incremental_key: bool = False
    max_length: Optional[int] = None
    sort_order: int = 0


class DwhColumnsBulkSave(BaseModel):
    columns: List[DwhColumnCreate]


# ============ DwhTransfer Schemas ============

class DwhTransferCreate(BaseModel):
    source_query_id: int
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=500)
    load_strategy: str = Field(default="full", description="full, incremental, append")
    incremental_column: Optional[str] = None
    column_mapping: Optional[dict] = None
    is_active: bool = True


class DwhTransferUpdate(BaseModel):
    source_query_id: Optional[int] = None
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=500)
    load_strategy: Optional[str] = None
    incremental_column: Optional[str] = None
    column_mapping: Optional[dict] = None
    is_active: Optional[bool] = None


class DwhTransferLogResponse(BaseModel):
    id: int
    uuid: str
    transfer_id: int
    status: str
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    total_rows: Optional[int] = None
    inserted_rows: Optional[int] = None
    updated_rows: Optional[int] = None
    deleted_rows: Optional[int] = None
    error_message: Optional[str] = None
    triggered_by: Optional[str] = None
    created_date: datetime

    class Config:
        from_attributes = True


class DwhScheduleResponse(BaseModel):
    id: int
    transfer_id: int
    frequency: str
    cron_expression: Optional[str] = None
    hour: Optional[int] = None
    minute: int = 0
    day_of_week: Optional[int] = None
    day_of_month: Optional[int] = None
    is_enabled: bool
    last_run_at: Optional[datetime] = None
    next_run_at: Optional[datetime] = None
    created_date: datetime
    updated_date: datetime

    class Config:
        from_attributes = True


class DwhTransferResponse(BaseModel):
    id: int
    uuid: str
    dwh_table_id: int
    source_query_id: Optional[int] = None
    name: str
    description: Optional[str] = None
    load_strategy: str
    incremental_column: Optional[str] = None
    last_incremental_value: Optional[str] = None
    column_mapping: Optional[dict] = None
    is_active: bool
    sort_order: int
    schedule: Optional[DwhScheduleResponse] = None
    last_log: Optional[DwhTransferLogResponse] = None
    created_date: datetime
    updated_date: datetime

    class Config:
        from_attributes = True


# ============ DwhSchedule Schemas ============

class DwhScheduleUpdate(BaseModel):
    frequency: str = Field(default="manual", description="manual, hourly, daily, weekly, monthly, cron")
    cron_expression: Optional[str] = None
    hour: Optional[int] = None
    minute: int = 0
    day_of_week: Optional[int] = None
    day_of_month: Optional[int] = None
    is_enabled: bool = False


# ============ DwhMapping Schemas ============

class DwhMappingCreate(BaseModel):
    target_type: str = Field(..., description="master_data, system_version, system_period, system_parameter, budget_entry")
    target_entity_id: Optional[int] = None
    target_definition_id: Optional[int] = None
    target_version_id: Optional[int] = None
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=500)
    is_active: bool = True


class DwhMappingUpdate(BaseModel):
    target_type: Optional[str] = None
    target_entity_id: Optional[int] = None
    target_definition_id: Optional[int] = None
    target_version_id: Optional[int] = None
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=500)
    is_active: Optional[bool] = None


class DwhFieldMappingCreate(BaseModel):
    source_column: str = Field(..., min_length=1, max_length=200)
    target_field: str = Field(..., min_length=1, max_length=200)
    transform_type: Optional[str] = "none"
    transform_config: Optional[dict] = None
    is_key_field: bool = False
    sort_order: int = 0


class DwhFieldMappingResponse(BaseModel):
    id: int
    mapping_id: int
    source_column: str
    target_field: str
    transform_type: Optional[str] = "none"
    transform_config: Optional[dict] = None
    is_key_field: bool
    sort_order: int

    class Config:
        from_attributes = True


class DwhMappingResponse(BaseModel):
    id: int
    uuid: str
    dwh_table_id: int
    target_type: str
    target_entity_id: Optional[int] = None
    target_definition_id: Optional[int] = None
    target_version_id: Optional[int] = None
    name: str
    description: Optional[str] = None
    is_active: bool
    sort_order: int
    field_mappings: List[DwhFieldMappingResponse] = []
    created_date: datetime
    updated_date: datetime

    class Config:
        from_attributes = True


class DwhFieldMappingsBulkSave(BaseModel):
    field_mappings: List[DwhFieldMappingCreate]


# ============ Transfer Execution ============

class DwhTransferExecutionResult(BaseModel):
    success: bool
    message: Optional[str] = None
    total_rows: int = 0
    inserted_rows: int = 0
    updated_rows: int = 0
    deleted_rows: int = 0
    error_details: Optional[List[str]] = None


class DwhMappingExecutionResult(BaseModel):
    success: bool
    message: Optional[str] = None
    processed: int = 0
    inserted: int = 0
    updated: int = 0
    errors: int = 0
    error_details: Optional[List[str]] = None


class DwhMappingPreview(BaseModel):
    columns: List[str] = []
    rows: List[dict] = []
    total: int = 0
    target_info: Optional[str] = None


class DwhTableStats(BaseModel):
    row_count: int = 0
    last_loaded_at: Optional[datetime] = None
    table_exists: bool = False
