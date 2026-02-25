"""
Data Flow API - Veri Akışı Birleşik Görünüm

Tüm veri pipeline'ını (bağlantılar → staging → DWH → hedef sistemler)
tek endpoint'ten sunan read-only overview API.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func
from typing import List, Optional

from app.db.session import get_db
from app.dependencies import get_current_user

from app.models.data_connection import (
    DataConnection, DataConnectionQuery, DataConnectionColumn,
    DataConnectionMapping, DataConnectionFieldMapping
)
from app.models.dwh import (
    DwhTable, DwhColumn, DwhTransfer, DwhMapping, DwhFieldMapping
)
from app.models.dynamic.meta_entity import MetaEntity
from app.models.dynamic.fact_definition import FactDefinition
from app.models.system_data import BudgetVersion

router = APIRouter(prefix="/data-flows", tags=["Veri Akışı"])


@router.get("/overview")
def get_data_flow_overview(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """
    Tüm veri akış pipeline'ının özet görünümü.
    Pipeline kartlarını doldurmak için birleşik veri döner.
    """

    # 1. Bağlantılar
    connections_raw = db.query(DataConnection).order_by(DataConnection.sort_order).all()
    connections = []
    for c in connections_raw:
        ct = c.connection_type.value if hasattr(c.connection_type, 'value') else str(c.connection_type)
        query_count = db.query(func.count(DataConnectionQuery.id)).filter(
            DataConnectionQuery.connection_id == c.id
        ).scalar() or 0
        connections.append({
            "id": c.id,
            "code": c.code,
            "name": c.name,
            "connection_type": ct,
            "is_active": c.is_active,
            "query_count": query_count,
        })

    # 2. Staging tabloları (staging_table_created olan sorgular)
    staging_queries = db.query(DataConnectionQuery).options(
        joinedload(DataConnectionQuery.connection)
    ).filter(
        DataConnectionQuery.staging_table_created == True
    ).order_by(DataConnectionQuery.id).all()

    staging_tables = []
    for sq in staging_queries:
        col_count = db.query(func.count(DataConnectionColumn.id)).filter(
            DataConnectionColumn.query_id == sq.id
        ).scalar() or 0
        mapping_count = db.query(func.count(DataConnectionMapping.id)).filter(
            DataConnectionMapping.query_id == sq.id
        ).scalar() or 0
        staging_tables.append({
            "query_id": sq.id,
            "connection_id": sq.connection_id,
            "connection_code": sq.connection.code if sq.connection else None,
            "query_code": sq.code,
            "query_name": sq.name,
            "staging_table_name": sq.staging_table_name,
            "staging_table_created": sq.staging_table_created,
            "column_count": col_count,
            "mapping_count": mapping_count,
        })

    # 3. DWH tabloları
    dwh_tables_raw = db.query(DwhTable).order_by(DwhTable.sort_order).all()
    dwh_tables = []
    for dt in dwh_tables_raw:
        st = dt.source_type.value if hasattr(dt.source_type, 'value') else str(dt.source_type)
        transfer_count = db.query(func.count(DwhTransfer.id)).filter(
            DwhTransfer.dwh_table_id == dt.id
        ).scalar() or 0
        dwh_mapping_count = db.query(func.count(DwhMapping.id)).filter(
            DwhMapping.dwh_table_id == dt.id
        ).scalar() or 0
        dwh_tables.append({
            "id": dt.id,
            "code": dt.code,
            "name": dt.name,
            "source_type": st,
            "source_query_id": dt.source_query_id,
            "table_name": dt.table_name,
            "table_created": dt.table_created,
            "transfer_count": transfer_count,
            "mapping_count": dwh_mapping_count,
        })

    # 4. Staging eşlemeleri
    staging_mappings_raw = db.query(DataConnectionMapping).options(
        joinedload(DataConnectionMapping.field_mappings),
        joinedload(DataConnectionMapping.query)
    ).order_by(DataConnectionMapping.id).all()

    staging_mappings = []
    for sm in staging_mappings_raw:
        tt = sm.target_type.value if hasattr(sm.target_type, 'value') else str(sm.target_type)
        staging_mappings.append({
            "id": sm.id,
            "uuid": sm.uuid,
            "name": sm.name,
            "query_id": sm.query_id,
            "connection_id": sm.query.connection_id if sm.query else None,
            "target_type": tt,
            "target_entity_id": sm.target_entity_id,
            "target_definition_id": sm.target_definition_id,
            "target_version_id": sm.target_version_id,
            "is_active": sm.is_active,
            "field_count": len(sm.field_mappings) if sm.field_mappings else 0,
        })

    # 5. DWH eşlemeleri
    dwh_mappings_raw = db.query(DwhMapping).options(
        joinedload(DwhMapping.field_mappings),
        joinedload(DwhMapping.dwh_table)
    ).order_by(DwhMapping.id).all()

    dwh_mappings = []
    for dm in dwh_mappings_raw:
        tt = dm.target_type.value if hasattr(dm.target_type, 'value') else str(dm.target_type)
        dwh_mappings.append({
            "id": dm.id,
            "uuid": dm.uuid,
            "name": dm.name,
            "dwh_table_id": dm.dwh_table_id,
            "dwh_table_name": dm.dwh_table.name if dm.dwh_table else None,
            "target_type": tt,
            "target_entity_id": dm.target_entity_id,
            "target_definition_id": dm.target_definition_id,
            "target_version_id": dm.target_version_id,
            "is_active": dm.is_active,
            "field_count": len(dm.field_mappings) if dm.field_mappings else 0,
        })

    # 6. Meta entities (hedef dropdown'lar için)
    entities = db.query(MetaEntity).order_by(MetaEntity.id).all()
    meta_entities = [
        {"id": e.id, "code": e.code, "default_name": e.default_name}
        for e in entities
    ]

    # 7. Fact definitions (budget_entry hedefi için)
    fact_defs = db.query(FactDefinition).order_by(FactDefinition.id).all()
    fact_definitions = [
        {"id": fd.id, "code": fd.code, "name": fd.name}
        for fd in fact_defs
    ]

    # 8. Budget versions (system_version/parameter hedefi için)
    versions = db.query(BudgetVersion).order_by(BudgetVersion.id).all()
    budget_versions = [
        {"id": v.id, "code": v.code, "name": v.name}
        for v in versions
    ]

    return {
        "connections": connections,
        "staging_tables": staging_tables,
        "dwh_tables": dwh_tables,
        "staging_mappings": staging_mappings,
        "dwh_mappings": dwh_mappings,
        "meta_entities": meta_entities,
        "fact_definitions": fact_definitions,
        "budget_versions": budget_versions,
    }
