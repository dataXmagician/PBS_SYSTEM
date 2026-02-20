"""
Data Sync Service - Veri senkronizasyon servisi

Kolon tespiti, staging tablo olusturma, veri senkronizasyonu
ve staging veri onizleme islemlerini yonetir.
"""

import logging
import re
from datetime import datetime
from typing import Optional, List, Dict, Any

from sqlalchemy.orm import Session
from sqlalchemy import text

from app.models.data_connection import (
    DataConnection, DataConnectionQuery, DataConnectionColumn,
    DataSyncLog, SyncStatus, ColumnDataType
)
from app.schemas.data_connection import (
    DetectedColumn, ColumnDetectionResponse, DataPreviewResponse
)
from app.services.connection_manager import ConnectionManager

logger = logging.getLogger(__name__)


class DataSyncService:
    """Veri senkronizasyon islemlerini yoneten sinif."""

    # ============ Column Detection ============

    @staticmethod
    def detect_columns(
        connection: DataConnection,
        query: DataConnectionQuery,
        file_bytes: Optional[bytes] = None,
        file_name: Optional[str] = None
    ) -> ColumnDetectionResponse:
        """
        Kolon tiplerini otomatik tespit eder.
        SAP/HANA icin ornek veri ceker, dosya icin dosya icerigini okur.
        """
        config = DataSyncService._build_connection_config(connection)
        query_config = DataSyncService._build_query_config(query)

        if file_bytes:
            query_config["file_bytes"] = file_bytes
            query_config["file_name"] = file_name or "upload.csv"

        rows, column_names = ConnectionManager.fetch_sample_data(
            conn_type=connection.connection_type.value if hasattr(connection.connection_type, 'value') else str(connection.connection_type),
            config=config,
            query_config=query_config,
            limit=100
        )

        detected_columns = []
        for i, col_name in enumerate(column_names):
            # Kolon degerlerini topla
            sample_values = []
            non_null_values = []
            for row in rows:
                val = row.get(col_name)
                if val is not None:
                    sample_values.append(str(val))
                    non_null_values.append(str(val))
                else:
                    sample_values.append("")

            # Tip tespiti
            detected_type = DataSyncService._detect_column_type(non_null_values)

            # Max uzunluk
            max_len = max((len(str(v)) for v in non_null_values), default=0)

            # Nullable kontrolu
            has_nulls = len(non_null_values) < len(rows) if rows else True

            # Target name: kucuk harf, bosluk yerine alt cizgi, ozel karakter temizle
            target_name = DataSyncService._sanitize_column_name(col_name)

            detected_columns.append(DetectedColumn(
                source_name=col_name,
                suggested_target_name=target_name,
                detected_data_type=detected_type,
                sample_values=sample_values[:5],
                is_nullable=has_nulls,
                max_length=max_len if max_len > 0 else None
            ))

        return ColumnDetectionResponse(
            columns=detected_columns,
            sample_row_count=len(rows),
            source_info={
                "connection_type": connection.connection_type.value if hasattr(connection.connection_type, 'value') else str(connection.connection_type),
                "connection_code": connection.code
            }
        )

    @staticmethod
    def _detect_column_type(values: List[str]) -> str:
        """Ornek degerlerden kolon tipini tespit eder."""
        if not values:
            return "string"

        # Integer kontrolu
        int_count = 0
        for v in values:
            try:
                int(v.strip())
                int_count += 1
            except (ValueError, AttributeError):
                pass

        if int_count >= len(values) * 0.9:
            return "integer"

        # Decimal kontrolu
        decimal_count = 0
        for v in values:
            try:
                float(v.strip().replace(",", "."))
                decimal_count += 1
            except (ValueError, AttributeError):
                pass

        if decimal_count >= len(values) * 0.9:
            return "decimal"

        # Boolean kontrolu
        bool_values = {"true", "false", "1", "0", "yes", "no", "evet", "hayir"}
        bool_count = sum(1 for v in values if v.strip().lower() in bool_values)
        if bool_count >= len(values) * 0.9:
            return "boolean"

        # Date kontrolu (YYYY-MM-DD, DD.MM.YYYY, DD/MM/YYYY)
        date_patterns = [
            r'^\d{4}-\d{2}-\d{2}$',
            r'^\d{2}\.\d{2}\.\d{4}$',
            r'^\d{2}/\d{2}/\d{4}$',
        ]
        date_count = 0
        for v in values:
            v_stripped = v.strip()
            for pattern in date_patterns:
                if re.match(pattern, v_stripped):
                    date_count += 1
                    break

        if date_count >= len(values) * 0.8:
            return "date"

        # Datetime kontrolu
        datetime_patterns = [
            r'^\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}',
            r'^\d{2}\.\d{2}\.\d{4} \d{2}:\d{2}',
        ]
        dt_count = 0
        for v in values:
            v_stripped = v.strip()
            for pattern in datetime_patterns:
                if re.match(pattern, v_stripped):
                    dt_count += 1
                    break

        if dt_count >= len(values) * 0.8:
            return "datetime"

        return "string"

    @staticmethod
    def _sanitize_column_name(name: str) -> str:
        """Kolon ismini PostgreSQL uyumlu hale getirir."""
        # Kucuk harf
        result = name.lower()
        # Bosluk ve ozel karakterleri alt cizgiye cevir
        result = re.sub(r'[^a-z0-9_]', '_', result)
        # Basta rakam varsa _ ekle
        if result and result[0].isdigit():
            result = f"_{result}"
        # Ard arda alt cizgileri teke dusur
        result = re.sub(r'_+', '_', result)
        # Bastan ve sondan alt cizgi temizle
        result = result.strip('_')
        return result or "column"

    # ============ Staging Table ============

    @staticmethod
    def create_staging_table(db: Session, query: DataConnectionQuery) -> None:
        """
        Query kolonlarina gore staging tablosu olusturur.
        Tablo adi: staging_{conn_code}_{query_code} (lowercase)
        """
        if not query.columns:
            raise ValueError("Kolon tanimlari bos. Once kolon tespiti yapin.")

        table_name = query.staging_table_name
        if not table_name:
            raise ValueError("Staging tablo adi bos.")

        # Kolon DDL olustur
        col_defs = ["_staging_id SERIAL PRIMARY KEY", "_synced_at TIMESTAMP DEFAULT NOW()"]

        for col in query.columns:
            if not col.is_included:
                continue
            pg_type = DataSyncService._column_type_to_pg(col.data_type, col.max_length)
            nullable = "" if col.is_nullable else " NOT NULL"
            col_defs.append(f'"{col.target_name}" {pg_type}{nullable}')

        # Tabloyu olustur (varsa sil)
        drop_sql = f'DROP TABLE IF EXISTS "{table_name}" CASCADE'
        create_sql = f'CREATE TABLE "{table_name}" ({", ".join(col_defs)})'

        db.execute(text(drop_sql))
        db.execute(text(create_sql))
        db.commit()

        # Query'yi guncelle
        query.staging_table_created = True
        db.commit()

        logger.info(f"Staging tablosu olusturuldu: {table_name}")

    @staticmethod
    def _column_type_to_pg(data_type, max_length: Optional[int] = None) -> str:
        """ColumnDataType -> PostgreSQL type mapping."""
        dt = data_type.value if hasattr(data_type, 'value') else str(data_type)
        mapping = {
            "string": f"VARCHAR({max_length})" if max_length and max_length <= 1000 else "TEXT",
            "integer": "BIGINT",
            "decimal": "NUMERIC(20,4)",
            "boolean": "BOOLEAN",
            "date": "DATE",
            "datetime": "TIMESTAMP",
        }
        return mapping.get(dt, "TEXT")

    # ============ Execute Sync ============

    @staticmethod
    def execute_sync(
        db: Session,
        connection: DataConnection,
        query: DataConnectionQuery,
        triggered_by: str,
        file_bytes: Optional[bytes] = None,
        file_name: Optional[str] = None
    ) -> DataSyncLog:
        """
        Veri senkronizasyonunu calistirir.
        1. Log olustur
        2. Staging tablosu yoksa olustur
        3. TRUNCATE (full refresh)
        4. Veri cek
        5. Batch INSERT
        6. Log guncelle
        """
        import uuid

        # 1. Sync log olustur
        sync_log = DataSyncLog(
            uuid=str(uuid.uuid4()),
            connection_id=connection.id,
            query_id=query.id,
            status=SyncStatus.running,
            started_at=datetime.utcnow(),
            triggered_by=triggered_by
        )
        db.add(sync_log)
        db.commit()
        db.refresh(sync_log)

        try:
            # 2. Staging tablo kontrolu
            if not query.staging_table_created:
                DataSyncService.create_staging_table(db, query)

            table_name = query.staging_table_name

            # 3. TRUNCATE
            db.execute(text(f'TRUNCATE TABLE "{table_name}"'))
            db.commit()

            # 4. Veri cek
            config = DataSyncService._build_connection_config(connection)
            query_config = DataSyncService._build_query_config(query)

            if file_bytes:
                query_config["file_bytes"] = file_bytes
                query_config["file_name"] = file_name or "upload.csv"

            conn_type = connection.connection_type.value if hasattr(connection.connection_type, 'value') else str(connection.connection_type)
            rows = ConnectionManager.fetch_all_data(conn_type, config, query_config)

            logger.info(f"Fetch sonucu: {len(rows) if rows else 0} satir")
            if rows:
                logger.info(f"Ilk satir keys: {list(rows[0].keys())}")
                logger.info(f"Ilk satir values (ilk 5): {dict(list(rows[0].items())[:5])}")

            if not rows:
                sync_log.status = SyncStatus.success
                sync_log.completed_at = datetime.utcnow()
                sync_log.total_rows = 0
                sync_log.inserted_rows = 0
                db.commit()
                logger.warning("Fetch sonucu bos — 0 satir dondu.")
                return sync_log

            # 5. Batch INSERT
            included_columns = [col for col in query.columns if col.is_included]
            if not included_columns:
                raise ValueError("Dahil edilen kolon yok.")

            target_names = [col.target_name for col in included_columns]
            source_names = [col.source_name for col in included_columns]
            logger.info(f"Source names (DB'den): {source_names}")
            logger.info(f"Target names (staging kolon): {target_names}")

            # Kolon ismi uyumsuzlugu kontrolu
            row_keys = set(rows[0].keys()) if rows else set()
            missing_sources = [s for s in source_names if s not in row_keys]
            if missing_sources:
                logger.warning(
                    f"KOLON UYUMSUZLUGU! Dosyadaki kolonlar: {sorted(row_keys)}, "
                    f"Bulunamayan source_name'ler: {missing_sources}"
                )

            col_list = ", ".join(f'"{tn}"' for tn in target_names)
            param_list = ", ".join(f":p{i}" for i in range(len(target_names)))
            insert_sql = f'INSERT INTO "{table_name}" ({col_list}) VALUES ({param_list})'

            inserted = 0
            batch_size = 500
            for batch_start in range(0, len(rows), batch_size):
                batch = rows[batch_start:batch_start + batch_size]
                params_list = []
                for row in batch:
                    params = {}
                    for i, (src, tgt) in enumerate(zip(source_names, target_names)):
                        val = row.get(src)
                        params[f"p{i}"] = val
                    params_list.append(params)

                for params in params_list:
                    db.execute(text(insert_sql), params)

                inserted += len(batch)

            db.commit()

            # 6. Basarili log
            sync_log.status = SyncStatus.success
            sync_log.completed_at = datetime.utcnow()
            sync_log.total_rows = len(rows)
            sync_log.inserted_rows = inserted
            db.commit()

            logger.info(f"Sync basarili: {table_name}, {inserted} satir eklendi.")
            return sync_log

        except Exception as e:
            logger.error(f"Sync hatasi: {e}")
            sync_log.status = SyncStatus.failed
            sync_log.completed_at = datetime.utcnow()
            sync_log.error_message = str(e)[:2000]
            db.commit()
            return sync_log

    # ============ Preview Staging Data ============

    @staticmethod
    def get_staging_data(
        db: Session,
        query: DataConnectionQuery,
        limit: int = 100,
        offset: int = 0
    ) -> DataPreviewResponse:
        """Staging tablosundan veri onizleme."""
        table_name = query.staging_table_name
        if not table_name or not query.staging_table_created:
            return DataPreviewResponse(columns=[], rows=[], total=0)

        # Total count
        count_result = db.execute(text(f'SELECT COUNT(*) FROM "{table_name}"'))
        total = count_result.scalar() or 0

        # Rows
        result = db.execute(
            text(f'SELECT * FROM "{table_name}" ORDER BY _staging_id LIMIT :lim OFFSET :off'),
            {"lim": limit, "off": offset}
        )
        col_names = list(result.keys())
        raw_rows = result.fetchall()

        rows = []
        for raw_row in raw_rows:
            row = {}
            for i, col_name in enumerate(col_names):
                val = raw_row[i]
                row[col_name] = str(val) if val is not None else None
            rows.append(row)

        return DataPreviewResponse(columns=col_names, rows=rows, total=total)

    # ============ Helpers ============

    @staticmethod
    def _build_connection_config(connection: DataConnection) -> dict:
        """DataConnection modelinden config dict olusturur."""
        return {
            "host": connection.host,
            "port": connection.port,
            "database_name": connection.database_name,
            "username": connection.username,
            "password": connection.password,
            "sap_client": connection.sap_client,
            "sap_service_path": connection.sap_service_path,
        }

    @staticmethod
    def _build_query_config(query: DataConnectionQuery) -> dict:
        """DataConnectionQuery modelinden query config dict olusturur."""
        return {
            "query_text": query.query_text,
            "odata_entity": query.odata_entity,
            "odata_select": query.odata_select,
            "odata_filter": query.odata_filter,
            "odata_top": query.odata_top,
            "file_parse_config": query.file_parse_config,
        }

    @staticmethod
    def generate_staging_table_name(conn_code: str, query_code: str) -> str:
        """Staging tablo adi olusturur."""
        name = f"staging_{conn_code}_{query_code}".lower()
        # Ozel karakterleri temizle
        name = re.sub(r'[^a-z0-9_]', '_', name)
        name = re.sub(r'_+', '_', name)
        return name[:100]  # Max 100 karakter
