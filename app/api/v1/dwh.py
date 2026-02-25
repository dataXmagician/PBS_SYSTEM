"""
DWH API - Veri Ambari Yonetimi

DWH tablo CRUD, transfer, zamanlama ve esleme endpointleri.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session, joinedload
from typing import Optional, List

from app.db.session import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.models.dwh import (
    DwhTable, DwhColumn, DwhTransfer, DwhTransferLog,
    DwhSchedule, DwhMapping, DwhFieldMapping,
    DwhTableSourceType, DwhLoadStrategy, DwhScheduleFrequency
)
from app.models.data_connection import DataConnectionQuery
from app.schemas.dwh import (
    DwhTableCreate, DwhTableFromStaging, DwhTableUpdate, DwhTableResponse, DwhTableListResponse,
    DwhColumnCreate, DwhColumnResponse, DwhColumnsBulkSave,
    DwhTransferCreate, DwhTransferUpdate, DwhTransferResponse, DwhTransferLogResponse,
    DwhScheduleUpdate, DwhScheduleResponse,
    DwhMappingCreate, DwhMappingUpdate, DwhMappingResponse,
    DwhFieldMappingCreate, DwhFieldMappingResponse, DwhFieldMappingsBulkSave,
    DwhTransferExecutionResult, DwhMappingExecutionResult, DwhMappingPreview,
    DwhTableStats
)
from app.schemas.data_connection import DataPreviewResponse
from app.services.dwh_table_service import DwhTableService
from app.services.dwh_transfer_service import DwhTransferService
from app.services.dwh_mapping_service import DwhMappingService

router = APIRouter(prefix="/dwh", tags=["DWH - Veri Ambari"])


# =============================================
# DWH TABLE CRUD
# =============================================

@router.get("/tables", response_model=DwhTableListResponse)
async def list_dwh_tables(
    search: Optional[str] = None,
    is_active: Optional[bool] = None,
    source_query_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """DWH tablo listesi."""
    query = db.query(DwhTable).options(joinedload(DwhTable.columns))

    if search:
        query = query.filter(
            (DwhTable.code.ilike(f"%{search}%")) |
            (DwhTable.name.ilike(f"%{search}%"))
        )
    if is_active is not None:
        query = query.filter(DwhTable.is_active == is_active)
    if source_query_id is not None:
        query = query.filter(DwhTable.source_query_id == source_query_id)

    total = query.count()
    items = query.order_by(DwhTable.sort_order, DwhTable.code).all()

    result_items = []
    for tbl in items:
        resp = _table_to_response(tbl)
        result_items.append(resp)

    return DwhTableListResponse(items=result_items, total=total)


@router.get("/tables/{table_id}", response_model=DwhTableResponse)
async def get_dwh_table(
    table_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """DWH tablo detayi (kolonlarla birlikte)."""
    tbl = db.query(DwhTable)\
        .options(joinedload(DwhTable.columns))\
        .filter(DwhTable.id == table_id)\
        .first()
    if not tbl:
        raise HTTPException(status_code=404, detail="DWH tablosu bulunamadi.")
    return _table_to_response(tbl)


@router.post("/tables", response_model=DwhTableResponse, status_code=status.HTTP_201_CREATED)
async def create_dwh_table(
    data: DwhTableCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Custom DWH tablosu olustur."""
    # Kod benzersizlik kontrolu
    existing = db.query(DwhTable).filter(DwhTable.code == data.code.upper()).first()
    if existing:
        raise HTTPException(status_code=409, detail=f"'{data.code}' kodu zaten kullaniliyor.")

    tbl = DwhTableService.create_custom(
        db, code=data.code, name=data.name, description=data.description
    )
    return _table_to_response(tbl)


@router.post("/tables/from-staging/{query_id}", response_model=DwhTableResponse, status_code=status.HTTP_201_CREATED)
async def create_dwh_table_from_staging(
    query_id: int,
    data: DwhTableFromStaging,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Staging sorgu yapisindan DWH tablosu olustur."""
    query_obj = db.query(DataConnectionQuery)\
        .options(joinedload(DataConnectionQuery.columns))\
        .filter(DataConnectionQuery.id == query_id)\
        .first()
    if not query_obj:
        raise HTTPException(status_code=404, detail="Sorgu bulunamadi.")

    existing = db.query(DwhTable).filter(DwhTable.code == data.code.upper()).first()
    if existing:
        raise HTTPException(status_code=409, detail=f"'{data.code}' kodu zaten kullaniliyor.")

    tbl = DwhTableService.create_from_staging(
        db, query=query_obj, code=data.code, name=data.name, description=data.description
    )
    return _table_to_response(tbl)


@router.put("/tables/{table_id}", response_model=DwhTableResponse)
async def update_dwh_table(
    table_id: int,
    data: DwhTableUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """DWH tablosunu guncelle."""
    tbl = db.query(DwhTable).filter(DwhTable.id == table_id).first()
    if not tbl:
        raise HTTPException(status_code=404, detail="DWH tablosu bulunamadi.")

    if data.name is not None:
        tbl.name = data.name
    if data.description is not None:
        tbl.description = data.description
    if data.is_active is not None:
        tbl.is_active = data.is_active

    db.commit()
    db.refresh(tbl)
    return _table_to_response(tbl)


@router.delete("/tables/{table_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_dwh_table(
    table_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """DWH tablosunu sil (fiziksel tablo da DROP edilir)."""
    tbl = db.query(DwhTable)\
        .options(joinedload(DwhTable.columns))\
        .filter(DwhTable.id == table_id)\
        .first()
    if not tbl:
        raise HTTPException(status_code=404, detail="DWH tablosu bulunamadi.")

    # Fiziksel tabloyu sil
    DwhTableService.drop_physical_table(db, tbl)

    db.delete(tbl)
    db.commit()


@router.put("/tables/{table_id}/columns", response_model=List[DwhColumnResponse])
async def save_dwh_columns(
    table_id: int,
    data: DwhColumnsBulkSave,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Kolon tanimlarini toplu kaydet (mevcut kolonlari sil, yenilerini olustur)."""
    tbl = db.query(DwhTable).filter(DwhTable.id == table_id).first()
    if not tbl:
        raise HTTPException(status_code=404, detail="DWH tablosu bulunamadi.")

    # Mevcut kolonlari sil
    db.query(DwhColumn).filter(DwhColumn.dwh_table_id == table_id).delete()

    # Yeni kolonlari ekle
    new_cols = []
    for i, col_data in enumerate(data.columns):
        col = DwhColumn(
            dwh_table_id=table_id,
            column_name=col_data.column_name,
            data_type=col_data.data_type,
            is_nullable=col_data.is_nullable,
            is_primary_key=col_data.is_primary_key,
            is_incremental_key=col_data.is_incremental_key,
            max_length=col_data.max_length,
            sort_order=col_data.sort_order if col_data.sort_order else i,
        )
        db.add(col)
        new_cols.append(col)

    # Kolon yapisi degistiyse fiziksel tabloyu yeniden olusturulmaya ihtiyac var
    if tbl.table_created:
        tbl.source_type = DwhTableSourceType.staging_modified
    db.commit()

    for c in new_cols:
        db.refresh(c)

    return [DwhColumnResponse.model_validate(c) for c in new_cols]


@router.post("/tables/{table_id}/create-physical")
async def create_physical_table(
    table_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Fiziksel PostgreSQL tablosunu olustur."""
    tbl = db.query(DwhTable)\
        .options(joinedload(DwhTable.columns))\
        .filter(DwhTable.id == table_id)\
        .first()
    if not tbl:
        raise HTTPException(status_code=404, detail="DWH tablosu bulunamadi.")

    try:
        DwhTableService.create_physical_table(db, tbl)
        return {"message": f"Fiziksel tablo olusturuldu: {tbl.table_name}", "table_created": True}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/tables/{table_id}/preview", response_model=DataPreviewResponse)
async def preview_dwh_data(
    table_id: int,
    limit: int = Query(default=100, le=1000),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """DWH tablo verisi onizleme."""
    tbl = db.query(DwhTable)\
        .options(joinedload(DwhTable.columns))\
        .filter(DwhTable.id == table_id)\
        .first()
    if not tbl:
        raise HTTPException(status_code=404, detail="DWH tablosu bulunamadi.")

    return DwhTableService.get_data(db, tbl, limit=limit, offset=offset)


@router.get("/tables/{table_id}/stats", response_model=DwhTableStats)
async def get_dwh_stats(
    table_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """DWH tablo istatistikleri."""
    tbl = db.query(DwhTable)\
        .options(joinedload(DwhTable.columns))\
        .filter(DwhTable.id == table_id)\
        .first()
    if not tbl:
        raise HTTPException(status_code=404, detail="DWH tablosu bulunamadi.")

    return DwhTableService.get_stats(db, tbl)


# =============================================
# DWH TRANSFERS
# =============================================

@router.get("/tables/{table_id}/transfers", response_model=List[DwhTransferResponse])
async def list_transfers(
    table_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """DWH tablosu icin transfer listesi."""
    transfers = db.query(DwhTransfer)\
        .options(
            joinedload(DwhTransfer.schedule),
            joinedload(DwhTransfer.logs)
        )\
        .filter(DwhTransfer.dwh_table_id == table_id)\
        .order_by(DwhTransfer.sort_order)\
        .all()

    return [_transfer_to_response(t) for t in transfers]


@router.get("/tables/{table_id}/transfers/{transfer_id}", response_model=DwhTransferResponse)
async def get_transfer(
    table_id: int,
    transfer_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Transfer detayi."""
    transfer = db.query(DwhTransfer)\
        .options(
            joinedload(DwhTransfer.schedule),
            joinedload(DwhTransfer.logs)
        )\
        .filter(
            DwhTransfer.id == transfer_id,
            DwhTransfer.dwh_table_id == table_id
        ).first()
    if not transfer:
        raise HTTPException(status_code=404, detail="Transfer bulunamadi.")
    return _transfer_to_response(transfer)


@router.post("/tables/{table_id}/transfers", response_model=DwhTransferResponse, status_code=status.HTTP_201_CREATED)
async def create_transfer(
    table_id: int,
    data: DwhTransferCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Transfer tanimla."""
    tbl = db.query(DwhTable).filter(DwhTable.id == table_id).first()
    if not tbl:
        raise HTTPException(status_code=404, detail="DWH tablosu bulunamadi.")

    # Kaynak sorgu kontrolu
    source_query = db.query(DataConnectionQuery).filter(
        DataConnectionQuery.id == data.source_query_id
    ).first()
    if not source_query:
        raise HTTPException(status_code=404, detail="Kaynak sorgu bulunamadi.")

    import uuid as uuid_lib
    transfer = DwhTransfer(
        uuid=str(uuid_lib.uuid4()),
        dwh_table_id=table_id,
        source_query_id=data.source_query_id,
        name=data.name,
        description=data.description,
        load_strategy=data.load_strategy,
        incremental_column=data.incremental_column,
        column_mapping=data.column_mapping,
        is_active=data.is_active,
    )
    db.add(transfer)
    db.commit()
    db.refresh(transfer)

    return _transfer_to_response(transfer)


@router.put("/tables/{table_id}/transfers/{transfer_id}", response_model=DwhTransferResponse)
async def update_transfer(
    table_id: int,
    transfer_id: int,
    data: DwhTransferUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Transfer guncelle."""
    transfer = db.query(DwhTransfer).filter(
        DwhTransfer.id == transfer_id, DwhTransfer.dwh_table_id == table_id
    ).first()
    if not transfer:
        raise HTTPException(status_code=404, detail="Transfer bulunamadi.")

    if data.source_query_id is not None:
        transfer.source_query_id = data.source_query_id
    if data.name is not None:
        transfer.name = data.name
    if data.description is not None:
        transfer.description = data.description
    if data.load_strategy is not None:
        transfer.load_strategy = data.load_strategy
    if data.incremental_column is not None:
        transfer.incremental_column = data.incremental_column
    if data.column_mapping is not None:
        transfer.column_mapping = data.column_mapping
    if data.is_active is not None:
        transfer.is_active = data.is_active

    db.commit()
    db.refresh(transfer)
    return _transfer_to_response(transfer)


@router.delete("/tables/{table_id}/transfers/{transfer_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_transfer(
    table_id: int,
    transfer_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Transfer sil."""
    transfer = db.query(DwhTransfer).filter(
        DwhTransfer.id == transfer_id, DwhTransfer.dwh_table_id == table_id
    ).first()
    if not transfer:
        raise HTTPException(status_code=404, detail="Transfer bulunamadi.")

    # APScheduler job kaldir
    from app.services.dwh_schedule_service import unregister_schedule
    unregister_schedule(transfer_id)

    db.delete(transfer)
    db.commit()


@router.post("/tables/{table_id}/transfers/{transfer_id}/execute", response_model=DwhTransferExecutionResult)
async def execute_transfer(
    table_id: int,
    transfer_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Transfer'i manuel calistir."""
    transfer = db.query(DwhTransfer)\
        .options(
            joinedload(DwhTransfer.dwh_table).joinedload(DwhTable.columns),
            joinedload(DwhTransfer.source_query)
        )\
        .filter(
            DwhTransfer.id == transfer_id,
            DwhTransfer.dwh_table_id == table_id
        ).first()
    if not transfer:
        raise HTTPException(status_code=404, detail="Transfer bulunamadi.")

    log = DwhTransferService.execute_transfer(db, transfer, triggered_by="manual")

    status_val = log.status
    if hasattr(status_val, 'value'):
        status_val = status_val.value

    return DwhTransferExecutionResult(
        success=status_val == "success",
        message=log.error_message if status_val == "failed" else "Transfer basariyla tamamlandi.",
        total_rows=log.total_rows or 0,
        inserted_rows=log.inserted_rows or 0,
        updated_rows=log.updated_rows or 0,
        deleted_rows=log.deleted_rows or 0,
    )


@router.post("/tables/{table_id}/transfers/{transfer_id}/preview", response_model=DataPreviewResponse)
async def preview_transfer(
    table_id: int,
    transfer_id: int,
    limit: int = Query(default=20, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Transfer onizleme (kuru calistirma)."""
    transfer = db.query(DwhTransfer)\
        .options(
            joinedload(DwhTransfer.dwh_table).joinedload(DwhTable.columns),
            joinedload(DwhTransfer.source_query)
        )\
        .filter(
            DwhTransfer.id == transfer_id,
            DwhTransfer.dwh_table_id == table_id
        ).first()
    if not transfer:
        raise HTTPException(status_code=404, detail="Transfer bulunamadi.")

    result = DwhTransferService.preview_transfer(db, transfer, limit=limit)
    return DataPreviewResponse(
        columns=result.get("columns", []),
        rows=result.get("rows", []),
        total=result.get("total", 0)
    )


@router.get("/tables/{table_id}/transfers/{transfer_id}/logs", response_model=List[DwhTransferLogResponse])
async def list_transfer_logs(
    table_id: int,
    transfer_id: int,
    limit: int = Query(default=20, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Transfer loglari."""
    logs = db.query(DwhTransferLog)\
        .filter(DwhTransferLog.transfer_id == transfer_id)\
        .order_by(DwhTransferLog.created_date.desc())\
        .limit(limit)\
        .all()

    return [DwhTransferLogResponse.model_validate(l) for l in logs]


# =============================================
# DWH SCHEDULE
# =============================================

@router.get("/transfers/{transfer_id}/schedule", response_model=Optional[DwhScheduleResponse])
async def get_schedule(
    transfer_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Zamanlama bilgisi al."""
    schedule = db.query(DwhSchedule).filter(
        DwhSchedule.transfer_id == transfer_id
    ).first()
    if not schedule:
        return None
    return DwhScheduleResponse.model_validate(schedule)


@router.put("/transfers/{transfer_id}/schedule", response_model=DwhScheduleResponse)
async def update_schedule(
    transfer_id: int,
    data: DwhScheduleUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Zamanlama olustur/guncelle."""
    transfer = db.query(DwhTransfer).filter(DwhTransfer.id == transfer_id).first()
    if not transfer:
        raise HTTPException(status_code=404, detail="Transfer bulunamadi.")

    schedule = db.query(DwhSchedule).filter(
        DwhSchedule.transfer_id == transfer_id
    ).first()

    if schedule:
        schedule.frequency = data.frequency
        schedule.cron_expression = data.cron_expression
        schedule.hour = data.hour
        schedule.minute = data.minute
        schedule.day_of_week = data.day_of_week
        schedule.day_of_month = data.day_of_month
        schedule.is_enabled = data.is_enabled
    else:
        from app.services.dwh_schedule_service import calculate_next_run
        schedule = DwhSchedule(
            transfer_id=transfer_id,
            frequency=data.frequency,
            cron_expression=data.cron_expression,
            hour=data.hour,
            minute=data.minute,
            day_of_week=data.day_of_week,
            day_of_month=data.day_of_month,
            is_enabled=data.is_enabled,
        )
        db.add(schedule)

    db.commit()
    db.refresh(schedule)

    # APScheduler guncelle
    from app.services.dwh_schedule_service import register_schedule, unregister_schedule, calculate_next_run
    if schedule.is_enabled:
        register_schedule(schedule)
        schedule.next_run_at = calculate_next_run(schedule)
        db.commit()
    else:
        unregister_schedule(transfer_id)

    return DwhScheduleResponse.model_validate(schedule)


@router.post("/transfers/{transfer_id}/schedule/enable")
async def enable_schedule(
    transfer_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Zamanlamayi etkinlestir."""
    schedule = db.query(DwhSchedule).filter(
        DwhSchedule.transfer_id == transfer_id
    ).first()
    if not schedule:
        raise HTTPException(status_code=404, detail="Zamanlama bulunamadi.")

    schedule.is_enabled = True
    db.commit()

    from app.services.dwh_schedule_service import register_schedule, calculate_next_run
    register_schedule(schedule)
    schedule.next_run_at = calculate_next_run(schedule)
    db.commit()

    return {"message": "Zamanlama etkinlestirildi.", "is_enabled": True}


@router.post("/transfers/{transfer_id}/schedule/disable")
async def disable_schedule(
    transfer_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Zamanlamayi devre disi birak."""
    schedule = db.query(DwhSchedule).filter(
        DwhSchedule.transfer_id == transfer_id
    ).first()
    if not schedule:
        raise HTTPException(status_code=404, detail="Zamanlama bulunamadi.")

    schedule.is_enabled = False
    schedule.next_run_at = None
    db.commit()

    from app.services.dwh_schedule_service import unregister_schedule
    unregister_schedule(transfer_id)

    return {"message": "Zamanlama devre disi birakildi.", "is_enabled": False}


# =============================================
# DWH MAPPINGS
# =============================================

@router.get("/tables/{table_id}/mappings", response_model=List[DwhMappingResponse])
async def list_mappings(
    table_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """DWH tablo esleme listesi."""
    mappings = db.query(DwhMapping)\
        .options(joinedload(DwhMapping.field_mappings))\
        .filter(DwhMapping.dwh_table_id == table_id)\
        .order_by(DwhMapping.sort_order)\
        .all()

    return [DwhMappingResponse.model_validate(m) for m in mappings]


@router.get("/tables/{table_id}/mappings/{mapping_id}", response_model=DwhMappingResponse)
async def get_mapping(
    table_id: int,
    mapping_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Esleme detayi."""
    mapping = db.query(DwhMapping)\
        .options(joinedload(DwhMapping.field_mappings))\
        .filter(
            DwhMapping.id == mapping_id,
            DwhMapping.dwh_table_id == table_id
        ).first()
    if not mapping:
        raise HTTPException(status_code=404, detail="Esleme bulunamadi.")
    return DwhMappingResponse.model_validate(mapping)


@router.post("/tables/{table_id}/mappings", response_model=DwhMappingResponse, status_code=status.HTTP_201_CREATED)
async def create_mapping(
    table_id: int,
    data: DwhMappingCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Esleme olustur."""
    tbl = db.query(DwhTable).filter(DwhTable.id == table_id).first()
    if not tbl:
        raise HTTPException(status_code=404, detail="DWH tablosu bulunamadi.")

    import uuid as uuid_lib
    mapping = DwhMapping(
        uuid=str(uuid_lib.uuid4()),
        dwh_table_id=table_id,
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

    return DwhMappingResponse.model_validate(mapping)


@router.put("/tables/{table_id}/mappings/{mapping_id}", response_model=DwhMappingResponse)
async def update_mapping(
    table_id: int,
    mapping_id: int,
    data: DwhMappingUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Esleme guncelle."""
    mapping = db.query(DwhMapping).filter(
        DwhMapping.id == mapping_id, DwhMapping.dwh_table_id == table_id
    ).first()
    if not mapping:
        raise HTTPException(status_code=404, detail="Esleme bulunamadi.")

    if data.target_type is not None:
        mapping.target_type = data.target_type
    if data.target_entity_id is not None:
        mapping.target_entity_id = data.target_entity_id
    if data.target_definition_id is not None:
        mapping.target_definition_id = data.target_definition_id
    if data.target_version_id is not None:
        mapping.target_version_id = data.target_version_id
    if data.name is not None:
        mapping.name = data.name
    if data.description is not None:
        mapping.description = data.description
    if data.is_active is not None:
        mapping.is_active = data.is_active

    db.commit()
    db.refresh(mapping)
    return DwhMappingResponse.model_validate(mapping)


@router.delete("/tables/{table_id}/mappings/{mapping_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_mapping(
    table_id: int,
    mapping_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Esleme sil."""
    mapping = db.query(DwhMapping).filter(
        DwhMapping.id == mapping_id, DwhMapping.dwh_table_id == table_id
    ).first()
    if not mapping:
        raise HTTPException(status_code=404, detail="Esleme bulunamadi.")
    db.delete(mapping)
    db.commit()


@router.put("/tables/{table_id}/mappings/{mapping_id}/fields", response_model=List[DwhFieldMappingResponse])
async def save_field_mappings(
    table_id: int,
    mapping_id: int,
    data: DwhFieldMappingsBulkSave,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Alan eslemelerini toplu kaydet."""
    mapping = db.query(DwhMapping).filter(
        DwhMapping.id == mapping_id, DwhMapping.dwh_table_id == table_id
    ).first()
    if not mapping:
        raise HTTPException(status_code=404, detail="Esleme bulunamadi.")

    # Mevcut field mapping'leri sil
    db.query(DwhFieldMapping).filter(DwhFieldMapping.mapping_id == mapping_id).delete()

    # Yeni field mapping'leri ekle
    new_fields = []
    for i, fm_data in enumerate(data.field_mappings):
        fm = DwhFieldMapping(
            mapping_id=mapping_id,
            source_column=fm_data.source_column,
            target_field=fm_data.target_field,
            transform_type=fm_data.transform_type,
            transform_config=fm_data.transform_config,
            is_key_field=fm_data.is_key_field,
            sort_order=fm_data.sort_order if fm_data.sort_order else i,
        )
        db.add(fm)
        new_fields.append(fm)

    db.commit()
    for f in new_fields:
        db.refresh(f)

    return [DwhFieldMappingResponse.model_validate(f) for f in new_fields]


@router.post("/tables/{table_id}/mappings/{mapping_id}/execute", response_model=DwhMappingExecutionResult)
async def execute_mapping(
    table_id: int,
    mapping_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Eslemeyi calistir."""
    mapping = db.query(DwhMapping)\
        .options(
            joinedload(DwhMapping.dwh_table).joinedload(DwhTable.columns),
            joinedload(DwhMapping.field_mappings)
        )\
        .filter(
            DwhMapping.id == mapping_id,
            DwhMapping.dwh_table_id == table_id
        ).first()
    if not mapping:
        raise HTTPException(status_code=404, detail="Esleme bulunamadi.")

    return DwhMappingService.execute_mapping(db, mapping, triggered_by="manual")


@router.post("/tables/{table_id}/mappings/{mapping_id}/preview", response_model=DwhMappingPreview)
async def preview_mapping(
    table_id: int,
    mapping_id: int,
    limit: int = Query(default=20, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Esleme onizleme (kuru calistirma)."""
    mapping = db.query(DwhMapping)\
        .options(
            joinedload(DwhMapping.dwh_table).joinedload(DwhTable.columns),
            joinedload(DwhMapping.field_mappings)
        )\
        .filter(
            DwhMapping.id == mapping_id,
            DwhMapping.dwh_table_id == table_id
        ).first()
    if not mapping:
        raise HTTPException(status_code=404, detail="Esleme bulunamadi.")

    return DwhMappingService.preview_mapping(db, mapping, limit=limit)


# =============================================
# HELPERS
# =============================================

def _table_to_response(tbl: DwhTable) -> DwhTableResponse:
    """DwhTable -> DwhTableResponse donusumu."""
    source_type = tbl.source_type
    if hasattr(source_type, 'value'):
        source_type = source_type.value

    return DwhTableResponse(
        id=tbl.id,
        uuid=tbl.uuid,
        code=tbl.code,
        name=tbl.name,
        description=tbl.description,
        source_type=source_type,
        source_query_id=tbl.source_query_id,
        table_name=tbl.table_name,
        table_created=tbl.table_created,
        is_active=tbl.is_active,
        sort_order=tbl.sort_order,
        columns=[DwhColumnResponse.model_validate(c) for c in (tbl.columns or [])],
        transfer_count=len(tbl.transfers) if tbl.transfers else 0,
        mapping_count=len(tbl.mappings) if tbl.mappings else 0,
        created_date=tbl.created_date,
        updated_date=tbl.updated_date,
    )


def _transfer_to_response(t: DwhTransfer) -> DwhTransferResponse:
    """DwhTransfer -> DwhTransferResponse donusumu."""
    load_strategy = t.load_strategy
    if hasattr(load_strategy, 'value'):
        load_strategy = load_strategy.value

    schedule_resp = None
    if t.schedule:
        schedule_resp = DwhScheduleResponse.model_validate(t.schedule)

    last_log = None
    if t.logs:
        last_log = DwhTransferLogResponse.model_validate(t.logs[0])

    return DwhTransferResponse(
        id=t.id,
        uuid=t.uuid,
        dwh_table_id=t.dwh_table_id,
        source_query_id=t.source_query_id,
        name=t.name,
        description=t.description,
        load_strategy=load_strategy,
        incremental_column=t.incremental_column,
        last_incremental_value=t.last_incremental_value,
        column_mapping=t.column_mapping,
        is_active=t.is_active,
        sort_order=t.sort_order,
        schedule=schedule_resp,
        last_log=last_log,
        created_date=t.created_date,
        updated_date=t.updated_date,
    )
