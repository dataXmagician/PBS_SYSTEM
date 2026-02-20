"""
Data Connection Schemas - Veri Baglantilari Pydantic Semalari
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Any
from datetime import datetime
from uuid import UUID


# ============ DataConnection Schemas ============

class DataConnectionCreate(BaseModel):
    code: str = Field(..., min_length=1, max_length=50)
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=500)
    connection_type: str = Field(..., description="sap_odata, hana_db, file_upload")
    host: Optional[str] = Field(None, max_length=500)
    port: Optional[int] = None
    database_name: Optional[str] = Field(None, max_length=200)
    username: Optional[str] = Field(None, max_length=200)
    password: Optional[str] = Field(None, max_length=500)
    sap_client: Optional[str] = Field(None, max_length=10)
    sap_service_path: Optional[str] = Field(None, max_length=500)
    extra_config: Optional[dict] = None
    is_active: bool = True


class DataConnectionUpdate(BaseModel):
    code: Optional[str] = Field(None, min_length=1, max_length=50)
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=500)
    connection_type: Optional[str] = None
    host: Optional[str] = Field(None, max_length=500)
    port: Optional[int] = None
    database_name: Optional[str] = Field(None, max_length=200)
    username: Optional[str] = Field(None, max_length=200)
    password: Optional[str] = Field(None, max_length=500)
    sap_client: Optional[str] = Field(None, max_length=10)
    sap_service_path: Optional[str] = Field(None, max_length=500)
    extra_config: Optional[dict] = None
    is_active: Optional[bool] = None


class DataConnectionResponse(BaseModel):
    id: int
    uuid: str
    code: str
    name: str
    description: Optional[str] = None
    connection_type: str
    host: Optional[str] = None
    port: Optional[int] = None
    database_name: Optional[str] = None
    username: Optional[str] = None
    # password kasitli olarak response'a dahil edilmez
    sap_client: Optional[str] = None
    sap_service_path: Optional[str] = None
    extra_config: Optional[dict] = None
    is_active: bool
    sort_order: int
    query_count: int = 0
    last_sync_status: Optional[str] = None
    last_sync_date: Optional[str] = None
    created_date: datetime
    updated_date: datetime

    class Config:
        from_attributes = True


class DataConnectionListResponse(BaseModel):
    items: List[DataConnectionResponse]
    total: int


# ============ DataConnectionQuery Schemas ============

class DataConnectionQueryCreate(BaseModel):
    code: str = Field(..., min_length=1, max_length=50)
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=500)
    query_text: Optional[str] = None
    odata_entity: Optional[str] = Field(None, max_length=500)
    odata_select: Optional[str] = Field(None, max_length=1000)
    odata_filter: Optional[str] = Field(None, max_length=1000)
    odata_top: Optional[int] = None
    file_parse_config: Optional[dict] = None


class DataConnectionQueryUpdate(BaseModel):
    code: Optional[str] = Field(None, min_length=1, max_length=50)
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=500)
    query_text: Optional[str] = None
    odata_entity: Optional[str] = Field(None, max_length=500)
    odata_select: Optional[str] = Field(None, max_length=1000)
    odata_filter: Optional[str] = Field(None, max_length=1000)
    odata_top: Optional[int] = None
    file_parse_config: Optional[dict] = None
    is_active: Optional[bool] = None


class DataConnectionColumnResponse(BaseModel):
    id: int
    query_id: int
    source_name: str
    target_name: str
    data_type: str
    is_nullable: bool
    is_primary_key: bool
    is_included: bool
    max_length: Optional[int] = None
    sort_order: int

    class Config:
        from_attributes = True


class DataConnectionQueryResponse(BaseModel):
    id: int
    uuid: str
    connection_id: int
    code: str
    name: str
    description: Optional[str] = None
    query_text: Optional[str] = None
    odata_entity: Optional[str] = None
    odata_select: Optional[str] = None
    odata_filter: Optional[str] = None
    odata_top: Optional[int] = None
    file_parse_config: Optional[dict] = None
    staging_table_name: Optional[str] = None
    staging_table_created: bool
    columns: List[DataConnectionColumnResponse] = []
    is_active: bool
    sort_order: int
    created_date: datetime
    updated_date: datetime

    class Config:
        from_attributes = True


class DataConnectionQueryListResponse(BaseModel):
    items: List[DataConnectionQueryResponse]
    total: int


# ============ DataConnectionColumn Schemas ============

class DataConnectionColumnCreate(BaseModel):
    source_name: str = Field(..., max_length=200)
    target_name: str = Field(..., max_length=200)
    data_type: str = Field(default="string")
    is_nullable: bool = True
    is_primary_key: bool = False
    is_included: bool = True
    max_length: Optional[int] = None
    sort_order: int = 0


class DataConnectionColumnUpdate(BaseModel):
    target_name: Optional[str] = Field(None, max_length=200)
    data_type: Optional[str] = None
    is_nullable: Optional[bool] = None
    is_primary_key: Optional[bool] = None
    is_included: Optional[bool] = None
    max_length: Optional[int] = None
    sort_order: Optional[int] = None


class ColumnsBulkSave(BaseModel):
    columns: List[DataConnectionColumnCreate]


# ============ DataSyncLog Schemas ============

class DataSyncLogResponse(BaseModel):
    id: int
    uuid: str
    connection_id: int
    query_id: Optional[int] = None
    status: str
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    total_rows: Optional[int] = None
    inserted_rows: Optional[int] = None
    error_message: Optional[str] = None
    triggered_by: Optional[str] = None
    created_date: datetime

    class Config:
        from_attributes = True


class DataSyncLogListResponse(BaseModel):
    items: List[DataSyncLogResponse]
    total: int


# ============ Test Connection Schemas ============

class TestConnectionRequest(BaseModel):
    connection_type: str
    host: Optional[str] = None
    port: Optional[int] = None
    database_name: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    sap_client: Optional[str] = None
    sap_service_path: Optional[str] = None


class TestConnectionResponse(BaseModel):
    success: bool
    message: str
    details: Optional[dict] = None


# ============ Column Detection Schemas ============

class DetectedColumn(BaseModel):
    source_name: str
    suggested_target_name: str
    detected_data_type: str
    sample_values: List[str] = []
    is_nullable: bool = True
    max_length: Optional[int] = None


class ColumnDetectionResponse(BaseModel):
    columns: List[DetectedColumn]
    sample_row_count: int
    source_info: Optional[dict] = None


# ============ Sync Trigger Schemas ============

class SyncTriggerResponse(BaseModel):
    sync_log_id: int
    status: str
    message: str


# ============ Data Preview Schemas ============

class DataPreviewResponse(BaseModel):
    columns: List[str]
    rows: List[dict]
    total: int


# ============ Mapping Schemas ============

class DataConnectionFieldMappingCreate(BaseModel):
    source_column: str = Field(..., max_length=200)
    target_field: str = Field(..., max_length=200)
    transform_type: Optional[str] = Field("none", max_length=50)
    transform_config: Optional[dict] = None
    is_key_field: bool = False
    sort_order: int = 0


class DataConnectionFieldMappingResponse(BaseModel):
    id: int
    mapping_id: int
    source_column: str
    target_field: str
    transform_type: Optional[str] = None
    transform_config: Optional[dict] = None
    is_key_field: bool
    sort_order: int

    class Config:
        from_attributes = True


class DataConnectionMappingCreate(BaseModel):
    target_type: str = Field(..., description="master_data, system_version, system_period, system_parameter, budget_entry")
    target_entity_id: Optional[int] = None
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=500)
    is_active: bool = True


class DataConnectionMappingUpdate(BaseModel):
    target_type: Optional[str] = None
    target_entity_id: Optional[int] = None
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=500)
    is_active: Optional[bool] = None


class DataConnectionMappingResponse(BaseModel):
    id: int
    uuid: str
    query_id: int
    target_type: str
    target_entity_id: Optional[int] = None
    name: str
    description: Optional[str] = None
    is_active: bool
    sort_order: int
    field_mappings: List[DataConnectionFieldMappingResponse] = []
    created_date: datetime
    updated_date: datetime

    class Config:
        from_attributes = True


class DataConnectionMappingListResponse(BaseModel):
    items: List[DataConnectionMappingResponse]
    total: int


class FieldMappingsBulkSave(BaseModel):
    field_mappings: List[DataConnectionFieldMappingCreate]


class MappingExecutionResult(BaseModel):
    success: bool
    message: str
    processed: int = 0
    inserted: int = 0
    updated: int = 0
    errors: int = 0
    error_details: List[str] = []


class MappingPreviewResponse(BaseModel):
    columns: List[str]
    rows: List[dict]
    total: int
    target_info: Optional[dict] = None
