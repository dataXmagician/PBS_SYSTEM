"""
Data Connections API - Veri Baglantilari Yonetimi

Dis kaynak sistemlerden (SAP OData, HANA DB, Excel/CSV/TXT, Parquet)
veri cekip PostgreSQL staging tablolarina yazmak icin API endpointleri.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func
from typing import Optional, List

from app.db.session import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.models.data_connection import (
    DataConnection, DataConnectionQuery, DataConnectionColumn,
    DataSyncLog, DataConnectionMapping, DataConnectionFieldMapping
)
from app.schemas.data_connection import (
    DataConnectionCreate, DataConnectionUpdate, DataConnectionResponse, DataConnectionListResponse,
    DataConnectionQueryCreate, DataConnectionQueryUpdate,
    DataConnectionQueryResponse, DataConnectionQueryListResponse,
    DataConnectionColumnCreate, DataConnectionColumnResponse,
    ColumnsBulkSave,
    DataSyncLogResponse, DataSyncLogListResponse,
    TestConnectionRequest, TestConnectionResponse,
    ColumnDetectionResponse,
    SyncTriggerResponse,
    DataPreviewResponse,
    DataConnectionMappingCreate, DataConnectionMappingUpdate,
    DataConnectionMappingResponse, DataConnectionMappingListResponse,
    DataConnectionFieldMappingCreate,
    FieldMappingsBulkSave,
    MappingExecutionResult,
    MappingPreviewResponse,
)
from app.services.connection_manager import ConnectionManager
from app.services.data_sync_service import DataSyncService
from app.services.data_mapping_service import DataMappingService

router = APIRouter(prefix="/data-connections", tags=["Data Connections - Veri Baglantilari"])


# =============================================
# CONNECTION CRUD
# =============================================

@router.get("", response_model=DataConnectionListResponse)
async def list_connections(
    search: Optional[str] = None,
    is_active: Optional[bool] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Tum veri baglantilerini listele."""
    query = db.query(DataConnection)

    if search:
        query = query.filter(
            (DataConnection.code.ilike(f"%{search}%")) |
            (DataConnection.name.ilike(f"%{search}%"))
        )
    if is_active is not None:
        query = query.filter(DataConnection.is_active == is_active)

    total = query.count()
    items = query.order_by(DataConnection.sort_order, DataConnection.code).all()

    # Her baglanti icin query count ve son sync bilgisi ekle
    result_items = []
    for conn in items:
        resp = _connection_to_response(db, conn)
        result_items.append(resp)

    return DataConnectionListResponse(items=result_items, total=total)


@router.get("/{connection_id}", response_model=DataConnectionResponse)
async def get_connection(
    connection_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Baglanti detayi (query'lerle birlikte)."""
    conn = db.query(DataConnection)\
        .options(joinedload(DataConnection.queries))\
        .filter(DataConnection.id == connection_id)\
        .first()
    if not conn:
        raise HTTPException(status_code=404, detail="Baglanti bulunamadi.")

    return _connection_to_response(db, conn)


@router.post("", response_model=DataConnectionResponse, status_code=status.HTTP_201_CREATED)
async def create_connection(
    data: DataConnectionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Yeni veri baglantisi olustur."""
    code = data.code.upper()
    existing = db.query(DataConnection).filter(DataConnection.code == code).first()
    if existing:
        raise HTTPException(status_code=400, detail=f"'{code}' kodu zaten kullanimda.")

    conn = DataConnection(
        code=code,
        name=data.name,
        description=data.description,
        connection_type=data.connection_type,
        host=data.host,
        port=data.port,
        database_name=data.database_name,
        username=data.username,
        password=data.password,
        sap_client=data.sap_client,
        sap_service_path=data.sap_service_path,
        extra_config=data.extra_config,
        is_active=data.is_active,
    )
    db.add(conn)
    db.commit()
    db.refresh(conn)

    return _connection_to_response(db, conn)


@router.put("/{connection_id}", response_model=DataConnectionResponse)
async def update_connection(
    connection_id: int,
    data: DataConnectionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Baglanti guncelle."""
    conn = db.query(DataConnection).filter(DataConnection.id == connection_id).first()
    if not conn:
        raise HTTPException(status_code=404, detail="Baglanti bulunamadi.")

    update_data = data.dict(exclude_unset=True)

    # Code degistiriliyorsa kontrol
    if "code" in update_data and update_data["code"]:
        new_code = update_data["code"].upper()
        if new_code != conn.code:
            existing = db.query(DataConnection).filter(DataConnection.code == new_code).first()
            if existing:
                raise HTTPException(status_code=400, detail=f"'{new_code}' kodu zaten kullanimda.")
        update_data["code"] = new_code

    for field, value in update_data.items():
        setattr(conn, field, value)

    db.commit()
    db.refresh(conn)

    return _connection_to_response(db, conn)


@router.delete("/{connection_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_connection(
    connection_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Baglanti sil (cascade ile tum query, column, sync log da silinir)."""
    conn = db.query(DataConnection).filter(DataConnection.id == connection_id).first()
    if not conn:
        raise HTTPException(status_code=404, detail="Baglanti bulunamadi.")

    # Staging tablolarini da sil
    queries = db.query(DataConnectionQuery).filter(
        DataConnectionQuery.connection_id == connection_id
    ).all()
    for q in queries:
        if q.staging_table_name and q.staging_table_created:
            try:
                from sqlalchemy import text
                db.execute(text(f'DROP TABLE IF EXISTS "{q.staging_table_name}" CASCADE'))
            except Exception:
                pass

    db.delete(conn)
    db.commit()
    return None


# =============================================
# TEST CONNECTION
# =============================================

@router.post("/test", response_model=TestConnectionResponse)
async def test_connection_unsaved(
    data: TestConnectionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Kaydedilmemis baglanti bilgileriyle test yap."""
    config = {
        "host": data.host,
        "port": data.port,
        "database_name": data.database_name,
        "username": data.username,
        "password": data.password,
        "sap_client": data.sap_client,
        "sap_service_path": data.sap_service_path,
    }
    result = ConnectionManager.test_connection(data.connection_type, config)
    return TestConnectionResponse(**result)


@router.post("/{connection_id}/test", response_model=TestConnectionResponse)
async def test_connection_saved(
    connection_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Kaydedilmis baglanti ile test yap."""
    conn = db.query(DataConnection).filter(DataConnection.id == connection_id).first()
    if not conn:
        raise HTTPException(status_code=404, detail="Baglanti bulunamadi.")

    config = {
        "host": conn.host,
        "port": conn.port,
        "database_name": conn.database_name,
        "username": conn.username,
        "password": conn.password,
        "sap_client": conn.sap_client,
        "sap_service_path": conn.sap_service_path,
    }
    conn_type = conn.connection_type.value if hasattr(conn.connection_type, 'value') else str(conn.connection_type)
    result = ConnectionManager.test_connection(conn_type, config)
    return TestConnectionResponse(**result)


# =============================================
# QUERY CRUD
# =============================================

@router.get("/{connection_id}/queries", response_model=DataConnectionQueryListResponse)
async def list_queries(
    connection_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Baglantinin sorgularini listele."""
    conn = db.query(DataConnection).filter(DataConnection.id == connection_id).first()
    if not conn:
        raise HTTPException(status_code=404, detail="Baglanti bulunamadi.")

    queries = db.query(DataConnectionQuery)\
        .options(joinedload(DataConnectionQuery.columns))\
        .filter(DataConnectionQuery.connection_id == connection_id)\
        .order_by(DataConnectionQuery.sort_order, DataConnectionQuery.code)\
        .all()

    return DataConnectionQueryListResponse(items=queries, total=len(queries))


@router.get("/{connection_id}/queries/{query_id}", response_model=DataConnectionQueryResponse)
async def get_query(
    connection_id: int,
    query_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Sorgu detayi (kolonlarla birlikte)."""
    q = db.query(DataConnectionQuery)\
        .options(joinedload(DataConnectionQuery.columns))\
        .filter(
            DataConnectionQuery.id == query_id,
            DataConnectionQuery.connection_id == connection_id
        ).first()
    if not q:
        raise HTTPException(status_code=404, detail="Sorgu bulunamadi.")
    return q


@router.post("/{connection_id}/queries", response_model=DataConnectionQueryResponse, status_code=status.HTTP_201_CREATED)
async def create_query(
    connection_id: int,
    data: DataConnectionQueryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Yeni sorgu olustur."""
    conn = db.query(DataConnection).filter(DataConnection.id == connection_id).first()
    if not conn:
        raise HTTPException(status_code=404, detail="Baglanti bulunamadi.")

    code = data.code.upper()
    existing = db.query(DataConnectionQuery).filter(
        DataConnectionQuery.connection_id == connection_id,
        DataConnectionQuery.code == code
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail=f"'{code}' sorgu kodu bu baglantida zaten mevcut.")

    # Staging tablo adi olustur
    staging_name = DataSyncService.generate_staging_table_name(conn.code, code)

    q = DataConnectionQuery(
        connection_id=connection_id,
        code=code,
        name=data.name,
        description=data.description,
        query_text=data.query_text,
        odata_entity=data.odata_entity,
        odata_select=data.odata_select,
        odata_filter=data.odata_filter,
        odata_top=data.odata_top,
        file_parse_config=data.file_parse_config,
        staging_table_name=staging_name,
    )
    db.add(q)
    db.commit()
    db.refresh(q)

    return q


@router.put("/{connection_id}/queries/{query_id}", response_model=DataConnectionQueryResponse)
async def update_query(
    connection_id: int,
    query_id: int,
    data: DataConnectionQueryUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Sorgu guncelle."""
    q = db.query(DataConnectionQuery).filter(
        DataConnectionQuery.id == query_id,
        DataConnectionQuery.connection_id == connection_id
    ).first()
    if not q:
        raise HTTPException(status_code=404, detail="Sorgu bulunamadi.")

    update_data = data.dict(exclude_unset=True)

    # Code degistiriliyorsa staging tablo adini da guncelle
    if "code" in update_data and update_data["code"]:
        new_code = update_data["code"].upper()
        if new_code != q.code:
            existing = db.query(DataConnectionQuery).filter(
                DataConnectionQuery.connection_id == connection_id,
                DataConnectionQuery.code == new_code
            ).first()
            if existing:
                raise HTTPException(status_code=400, detail=f"'{new_code}' kodu bu baglantida zaten mevcut.")

            conn = db.query(DataConnection).filter(DataConnection.id == connection_id).first()
            update_data["code"] = new_code
            update_data["staging_table_name"] = DataSyncService.generate_staging_table_name(conn.code, new_code)
            update_data["staging_table_created"] = False

    for field, value in update_data.items():
        setattr(q, field, value)

    db.commit()
    db.refresh(q)
    return q


@router.delete("/{connection_id}/queries/{query_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_query(
    connection_id: int,
    query_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Sorgu sil."""
    q = db.query(DataConnectionQuery).filter(
        DataConnectionQuery.id == query_id,
        DataConnectionQuery.connection_id == connection_id
    ).first()
    if not q:
        raise HTTPException(status_code=404, detail="Sorgu bulunamadi.")

    # Staging tablosunu sil
    if q.staging_table_name and q.staging_table_created:
        try:
            from sqlalchemy import text
            db.execute(text(f'DROP TABLE IF EXISTS "{q.staging_table_name}" CASCADE'))
        except Exception:
            pass

    db.delete(q)
    db.commit()
    return None


# =============================================
# COLUMN DETECTION & MANAGEMENT
# =============================================

@router.post("/{connection_id}/queries/{query_id}/detect-columns", response_model=ColumnDetectionResponse)
async def detect_columns(
    connection_id: int,
    query_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """SAP/HANA sorgusundan kolon tiplerini otomatik tespit et."""
    conn = db.query(DataConnection).filter(DataConnection.id == connection_id).first()
    if not conn:
        raise HTTPException(status_code=404, detail="Baglanti bulunamadi.")

    q = db.query(DataConnectionQuery).filter(
        DataConnectionQuery.id == query_id,
        DataConnectionQuery.connection_id == connection_id
    ).first()
    if not q:
        raise HTTPException(status_code=404, detail="Sorgu bulunamadi.")

    try:
        result = DataSyncService.detect_columns(conn, q)
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Kolon tespiti hatasi: {str(e)}")


@router.post("/{connection_id}/queries/{query_id}/detect-columns/file", response_model=ColumnDetectionResponse)
async def detect_columns_from_file(
    connection_id: int,
    query_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Yuklenen dosyadan kolon tiplerini tespit et."""
    conn = db.query(DataConnection).filter(DataConnection.id == connection_id).first()
    if not conn:
        raise HTTPException(status_code=404, detail="Baglanti bulunamadi.")

    q = db.query(DataConnectionQuery).filter(
        DataConnectionQuery.id == query_id,
        DataConnectionQuery.connection_id == connection_id
    ).first()
    if not q:
        raise HTTPException(status_code=404, detail="Sorgu bulunamadi.")

    file_bytes = await file.read()
    file_name = file.filename or "upload.csv"

    try:
        result = DataSyncService.detect_columns(conn, q, file_bytes=file_bytes, file_name=file_name)
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Dosya kolon tespiti hatasi: {str(e)}")


@router.put("/{connection_id}/queries/{query_id}/columns", response_model=List[DataConnectionColumnResponse])
async def save_columns(
    connection_id: int,
    query_id: int,
    data: ColumnsBulkSave,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Kolon tanimlarini toplu kaydet (mevcut kolonlari siler, yeniden olusturur)."""
    q = db.query(DataConnectionQuery).filter(
        DataConnectionQuery.id == query_id,
        DataConnectionQuery.connection_id == connection_id
    ).first()
    if not q:
        raise HTTPException(status_code=404, detail="Sorgu bulunamadi.")

    # Mevcut kolonlari sil
    db.query(DataConnectionColumn).filter(DataConnectionColumn.query_id == query_id).delete()

    # Yeni kolonlari ekle
    new_columns = []
    for i, col_data in enumerate(data.columns):
        col = DataConnectionColumn(
            query_id=query_id,
            source_name=col_data.source_name,
            target_name=col_data.target_name,
            data_type=col_data.data_type,
            is_nullable=col_data.is_nullable,
            is_primary_key=col_data.is_primary_key,
            is_included=col_data.is_included,
            max_length=col_data.max_length,
            sort_order=col_data.sort_order if col_data.sort_order else i,
        )
        db.add(col)
        new_columns.append(col)

    # Kolon degistiyse staging tablosunu yeniden olusturmak gerekecek
    q.staging_table_created = False

    db.commit()

    # Refresh
    for col in new_columns:
        db.refresh(col)

    return new_columns


# =============================================
# SYNC
# =============================================

@router.post("/{connection_id}/queries/{query_id}/sync", response_model=SyncTriggerResponse)
async def trigger_sync(
    connection_id: int,
    query_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """SAP/HANA sorgusundan veri senkronizasyonu baslat."""
    conn = db.query(DataConnection).filter(DataConnection.id == connection_id).first()
    if not conn:
        raise HTTPException(status_code=404, detail="Baglanti bulunamadi.")

    # Dosya tipi baglantilar icin normal sync kullanilamaz — dosya yuklemesi gerekir
    conn_type_val = conn.connection_type.value if hasattr(conn.connection_type, 'value') else str(conn.connection_type)
    if conn_type_val == "file_upload":
        raise HTTPException(
            status_code=400,
            detail="Dosya tipi baglantilar icin 'Dosya Yukle & Sync' butonunu kullanin."
        )

    q = db.query(DataConnectionQuery)\
        .options(joinedload(DataConnectionQuery.columns))\
        .filter(
            DataConnectionQuery.id == query_id,
            DataConnectionQuery.connection_id == connection_id
        ).first()
    if not q:
        raise HTTPException(status_code=404, detail="Sorgu bulunamadi.")

    if not q.columns:
        raise HTTPException(status_code=400, detail="Kolon tanimlari bos. Once kolon tespiti yapin.")

    triggered_by = getattr(current_user, 'username', 'system')
    sync_log = DataSyncService.execute_sync(db, conn, q, triggered_by=triggered_by)

    status_val = sync_log.status.value if hasattr(sync_log.status, 'value') else str(sync_log.status)
    error_detail = f" Hata: {sync_log.error_message}" if sync_log.error_message else ""
    return SyncTriggerResponse(
        sync_log_id=sync_log.id,
        status=status_val,
        message=f"Sync {'basarili' if status_val == 'success' else 'basarisiz'}: {sync_log.inserted_rows or 0} satir.{error_detail}"
    )


@router.post("/{connection_id}/queries/{query_id}/sync/file", response_model=SyncTriggerResponse)
async def trigger_sync_from_file(
    connection_id: int,
    query_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Dosyadan veri senkronizasyonu baslat."""
    conn = db.query(DataConnection).filter(DataConnection.id == connection_id).first()
    if not conn:
        raise HTTPException(status_code=404, detail="Baglanti bulunamadi.")

    q = db.query(DataConnectionQuery)\
        .options(joinedload(DataConnectionQuery.columns))\
        .filter(
            DataConnectionQuery.id == query_id,
            DataConnectionQuery.connection_id == connection_id
        ).first()
    if not q:
        raise HTTPException(status_code=404, detail="Sorgu bulunamadi.")

    if not q.columns:
        raise HTTPException(status_code=400, detail="Kolon tanimlari bos. Once kolon tespiti yapin.")

    file_bytes = await file.read()
    file_name = file.filename or "upload.csv"
    triggered_by = getattr(current_user, 'username', 'system')

    sync_log = DataSyncService.execute_sync(
        db, conn, q, triggered_by=triggered_by,
        file_bytes=file_bytes, file_name=file_name
    )

    status_val = sync_log.status.value if hasattr(sync_log.status, 'value') else str(sync_log.status)
    error_detail = f" Hata: {sync_log.error_message}" if sync_log.error_message else ""
    return SyncTriggerResponse(
        sync_log_id=sync_log.id,
        status=status_val,
        message=f"Sync {'basarili' if status_val == 'success' else 'basarisiz'}: {sync_log.inserted_rows or 0} satir.{error_detail}"
    )


# =============================================
# SYNC LOGS
# =============================================

@router.get("/{connection_id}/sync-logs", response_model=DataSyncLogListResponse)
async def list_sync_logs(
    connection_id: int,
    query_id: Optional[int] = None,
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Senkronizasyon gecmisini listele."""
    conn = db.query(DataConnection).filter(DataConnection.id == connection_id).first()
    if not conn:
        raise HTTPException(status_code=404, detail="Baglanti bulunamadi.")

    q = db.query(DataSyncLog).filter(DataSyncLog.connection_id == connection_id)
    if query_id:
        q = q.filter(DataSyncLog.query_id == query_id)

    total = q.count()
    logs = q.order_by(DataSyncLog.created_date.desc()).limit(limit).all()

    return DataSyncLogListResponse(items=logs, total=total)


# =============================================
# PREVIEW
# =============================================

@router.get("/{connection_id}/queries/{query_id}/preview", response_model=DataPreviewResponse)
async def preview_staging_data(
    connection_id: int,
    query_id: int,
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Staging tablosundan veri onizleme."""
    q = db.query(DataConnectionQuery).filter(
        DataConnectionQuery.id == query_id,
        DataConnectionQuery.connection_id == connection_id
    ).first()
    if not q:
        raise HTTPException(status_code=404, detail="Sorgu bulunamadi.")

    if not q.staging_table_created:
        return DataPreviewResponse(columns=[], rows=[], total=0)

    return DataSyncService.get_staging_data(db, q, limit=limit, offset=offset)


# =============================================
# MAPPING CRUD
# =============================================

@router.get("/{connection_id}/queries/{query_id}/mappings", response_model=DataConnectionMappingListResponse)
async def list_mappings(
    connection_id: int,
    query_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Sorgunun mapping'lerini listele."""
    q = db.query(DataConnectionQuery).filter(
        DataConnectionQuery.id == query_id,
        DataConnectionQuery.connection_id == connection_id
    ).first()
    if not q:
        raise HTTPException(status_code=404, detail="Sorgu bulunamadi.")

    mappings = db.query(DataConnectionMapping)\
        .options(joinedload(DataConnectionMapping.field_mappings))\
        .filter(DataConnectionMapping.query_id == query_id)\
        .order_by(DataConnectionMapping.sort_order)\
        .all()

    return DataConnectionMappingListResponse(items=mappings, total=len(mappings))


@router.get("/{connection_id}/queries/{query_id}/mappings/{mapping_id}", response_model=DataConnectionMappingResponse)
async def get_mapping(
    connection_id: int,
    query_id: int,
    mapping_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Mapping detayi (field mapping'lerle birlikte)."""
    mapping = db.query(DataConnectionMapping)\
        .options(joinedload(DataConnectionMapping.field_mappings))\
        .filter(
            DataConnectionMapping.id == mapping_id,
            DataConnectionMapping.query_id == query_id
        ).first()
    if not mapping:
        raise HTTPException(status_code=404, detail="Mapping bulunamadi.")
    return mapping


@router.post("/{connection_id}/queries/{query_id}/mappings", response_model=DataConnectionMappingResponse, status_code=status.HTTP_201_CREATED)
async def create_mapping(
    connection_id: int,
    query_id: int,
    data: DataConnectionMappingCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Yeni mapping olustur."""
    q = db.query(DataConnectionQuery).filter(
        DataConnectionQuery.id == query_id,
        DataConnectionQuery.connection_id == connection_id
    ).first()
    if not q:
        raise HTTPException(status_code=404, detail="Sorgu bulunamadi.")

    mapping = DataConnectionMapping(
        query_id=query_id,
        target_type=data.target_type,
        target_entity_id=data.target_entity_id,
        target_definition_id=data.target_definition_id,
        target_version_id=data.target_version_id,
        name=data.name,
        description=data.description,
        is_active=data.is_active,
    )
    db.add(mapping)
    db.commit()
    db.refresh(mapping)

    return mapping


@router.put("/{connection_id}/queries/{query_id}/mappings/{mapping_id}", response_model=DataConnectionMappingResponse)
async def update_mapping(
    connection_id: int,
    query_id: int,
    mapping_id: int,
    data: DataConnectionMappingUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Mapping guncelle."""
    mapping = db.query(DataConnectionMapping).filter(
        DataConnectionMapping.id == mapping_id,
        DataConnectionMapping.query_id == query_id
    ).first()
    if not mapping:
        raise HTTPException(status_code=404, detail="Mapping bulunamadi.")

    update_data = data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(mapping, field, value)

    db.commit()
    db.refresh(mapping)
    return mapping


@router.delete("/{connection_id}/queries/{query_id}/mappings/{mapping_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_mapping(
    connection_id: int,
    query_id: int,
    mapping_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Mapping sil."""
    mapping = db.query(DataConnectionMapping).filter(
        DataConnectionMapping.id == mapping_id,
        DataConnectionMapping.query_id == query_id
    ).first()
    if not mapping:
        raise HTTPException(status_code=404, detail="Mapping bulunamadi.")

    db.delete(mapping)
    db.commit()
    return None


@router.put("/{connection_id}/queries/{query_id}/mappings/{mapping_id}/fields", response_model=DataConnectionMappingResponse)
async def save_field_mappings(
    connection_id: int,
    query_id: int,
    mapping_id: int,
    data: FieldMappingsBulkSave,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Field mapping'leri toplu kaydet (mevcut eslestirmeleri siler, yeniden olusturur)."""
    mapping = db.query(DataConnectionMapping).filter(
        DataConnectionMapping.id == mapping_id,
        DataConnectionMapping.query_id == query_id
    ).first()
    if not mapping:
        raise HTTPException(status_code=404, detail="Mapping bulunamadi.")

    # Mevcut field mapping'leri sil
    db.query(DataConnectionFieldMapping).filter(
        DataConnectionFieldMapping.mapping_id == mapping_id
    ).delete()

    # Yeni field mapping'leri olustur
    for i, fm_data in enumerate(data.field_mappings):
        fm = DataConnectionFieldMapping(
            mapping_id=mapping_id,
            source_column=fm_data.source_column,
            target_field=fm_data.target_field,
            transform_type=fm_data.transform_type or "none",
            transform_config=fm_data.transform_config,
            is_key_field=fm_data.is_key_field,
            sort_order=fm_data.sort_order if fm_data.sort_order else i,
        )
        db.add(fm)

    db.commit()

    # Guncellenmis mapping'i dondur
    mapping = db.query(DataConnectionMapping)\
        .options(joinedload(DataConnectionMapping.field_mappings))\
        .filter(DataConnectionMapping.id == mapping_id)\
        .first()

    return mapping


# =============================================
# MAPPING EXECUTION
# =============================================

@router.post("/{connection_id}/queries/{query_id}/mappings/{mapping_id}/execute", response_model=MappingExecutionResult)
async def execute_mapping(
    connection_id: int,
    query_id: int,
    mapping_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Mapping'i calistir (staging -> hedef tablo aktarimi)."""
    mapping = db.query(DataConnectionMapping)\
        .options(
            joinedload(DataConnectionMapping.field_mappings),
            joinedload(DataConnectionMapping.query)
        )\
        .filter(
            DataConnectionMapping.id == mapping_id,
            DataConnectionMapping.query_id == query_id
        ).first()
    if not mapping:
        raise HTTPException(status_code=404, detail="Mapping bulunamadi.")

    triggered_by = getattr(current_user, 'username', 'system')
    result = DataMappingService.execute_mapping(db, mapping, triggered_by)
    return result


@router.post("/{connection_id}/queries/{query_id}/mappings/{mapping_id}/preview", response_model=MappingPreviewResponse)
async def preview_mapping(
    connection_id: int,
    query_id: int,
    mapping_id: int,
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Mapping sonucunu onizle (dry-run, DB'ye yazmaz)."""
    mapping = db.query(DataConnectionMapping)\
        .options(
            joinedload(DataConnectionMapping.field_mappings),
            joinedload(DataConnectionMapping.query)
        )\
        .filter(
            DataConnectionMapping.id == mapping_id,
            DataConnectionMapping.query_id == query_id
        ).first()
    if not mapping:
        raise HTTPException(status_code=404, detail="Mapping bulunamadi.")

    result = DataMappingService.preview_mapping(db, mapping, limit=limit)
    return result


# =============================================
# HELPERS
# =============================================

def _connection_to_response(db: Session, conn: DataConnection) -> DataConnectionResponse:
    """DataConnection modelini response'a cevirir, ek bilgileri ekler."""
    query_count = db.query(func.count(DataConnectionQuery.id))\
        .filter(DataConnectionQuery.connection_id == conn.id).scalar() or 0

    # Son sync bilgisi
    last_sync = db.query(DataSyncLog)\
        .filter(DataSyncLog.connection_id == conn.id)\
        .order_by(DataSyncLog.created_date.desc())\
        .first()

    last_sync_status = None
    last_sync_date = None
    if last_sync:
        last_sync_status = last_sync.status.value if hasattr(last_sync.status, 'value') else str(last_sync.status)
        last_sync_date = last_sync.completed_at.isoformat() if last_sync.completed_at else last_sync.created_date.isoformat()

    return DataConnectionResponse(
        id=conn.id,
        uuid=conn.uuid,
        code=conn.code,
        name=conn.name,
        description=conn.description,
        connection_type=conn.connection_type.value if hasattr(conn.connection_type, 'value') else str(conn.connection_type),
        host=conn.host,
        port=conn.port,
        database_name=conn.database_name,
        username=conn.username,
        sap_client=conn.sap_client,
        sap_service_path=conn.sap_service_path,
        extra_config=conn.extra_config,
        is_active=conn.is_active,
        sort_order=conn.sort_order or 0,
        query_count=query_count,
        last_sync_status=last_sync_status,
        last_sync_date=last_sync_date,
        created_date=conn.created_date,
        updated_date=conn.updated_date,
    )
