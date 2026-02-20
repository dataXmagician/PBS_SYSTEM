"""
DWH Transfer Service - Staging → DWH Veri Aktarım Servisi

Full, incremental ve append stratejileriyle staging'den DWH'a veri aktarımı.
"""

import logging
from datetime import datetime
from typing import Optional, List, Dict, Any, Tuple
import uuid as uuid_lib

from sqlalchemy.orm import Session
from sqlalchemy import text

from app.models.dwh import (
    DwhTable, DwhColumn, DwhTransfer, DwhTransferLog,
    DwhLoadStrategy, DwhTransferStatus
)
from app.models.data_connection import DataConnectionQuery
from app.services.dwh_table_service import DwhTableService

logger = logging.getLogger(__name__)


class DwhTransferService:
    """Staging → DWH veri aktarım servisi."""

    @staticmethod
    def execute_transfer(
        db: Session,
        transfer: DwhTransfer,
        triggered_by: str
    ) -> DwhTransferLog:
        """
        Staging → DWH veri aktarımını çalıştırır.
        Strateji bazlı: full, incremental veya append.
        """
        # 1. Transfer log oluştur
        transfer_log = DwhTransferLog(
            uuid=str(uuid_lib.uuid4()),
            transfer_id=transfer.id,
            status=DwhTransferStatus.running,
            started_at=datetime.utcnow(),
            triggered_by=triggered_by
        )
        db.add(transfer_log)
        db.commit()
        db.refresh(transfer_log)

        try:
            dwh_table = transfer.dwh_table
            source_query = transfer.source_query

            if not source_query:
                raise ValueError("Kaynak sorgu bulunamadı.")

            if not source_query.staging_table_created:
                raise ValueError("Staging tablosu henüz oluşturulmamış. Önce sync yapın.")

            # 2. DWH fiziksel tablosu yoksa oluştur
            if not dwh_table.table_created:
                DwhTableService.create_physical_table(db, dwh_table)

            staging_table = source_query.staging_table_name
            dwh_table_name = dwh_table.table_name
            column_map = transfer.column_mapping  # {staging_col: dwh_col} veya None

            # 3. Strateji bazlı çalıştır
            strategy = transfer.load_strategy
            if hasattr(strategy, 'value'):
                strategy = strategy.value

            if strategy == "full":
                total, inserted, updated, deleted = DwhTransferService._full_load(
                    db, staging_table, dwh_table_name, dwh_table.columns, column_map
                )
            elif strategy == "incremental":
                total, inserted, updated, deleted = DwhTransferService._incremental_load(
                    db, transfer, staging_table, dwh_table_name, dwh_table.columns, column_map
                )
            elif strategy == "append":
                total, inserted, updated, deleted = DwhTransferService._append_load(
                    db, staging_table, dwh_table_name, dwh_table.columns, column_map
                )
            else:
                raise ValueError(f"Bilinmeyen yükleme stratejisi: {strategy}")

            # 4. Başarılı log
            transfer_log.status = DwhTransferStatus.success
            transfer_log.completed_at = datetime.utcnow()
            transfer_log.total_rows = total
            transfer_log.inserted_rows = inserted
            transfer_log.updated_rows = updated
            transfer_log.deleted_rows = deleted
            db.commit()

            logger.info(
                f"DWH transfer başarılı: {dwh_table_name}, "
                f"toplam={total}, eklenen={inserted}, güncellenen={updated}"
            )
            return transfer_log

        except Exception as e:
            logger.error(f"DWH transfer hatası: {e}")
            transfer_log.status = DwhTransferStatus.failed
            transfer_log.completed_at = datetime.utcnow()
            transfer_log.error_message = str(e)[:2000]
            db.commit()
            return transfer_log

    # ============ Load Strategies ============

    @staticmethod
    def _full_load(
        db: Session,
        staging_table: str,
        dwh_table_name: str,
        dwh_columns: List[DwhColumn],
        column_map: Optional[Dict] = None
    ) -> Tuple[int, int, int, int]:
        """
        Full load: TRUNCATE + INSERT.
        Staging'deki tüm veriyi DWH'a aktarır.
        """
        # TRUNCATE DWH
        db.execute(text(f'TRUNCATE TABLE "{dwh_table_name}"'))
        db.commit()

        # Kolon eşlemesi hazırla
        dwh_col_names = [col.column_name for col in dwh_columns]
        staging_col_names = DwhTransferService._resolve_column_mapping(
            dwh_col_names, column_map
        )

        # Staging'den veri oku
        staging_col_list = ", ".join(f'"{c}"' for c in staging_col_names)
        count_result = db.execute(text(f'SELECT COUNT(*) FROM "{staging_table}"'))
        total = count_result.scalar() or 0

        if total == 0:
            return (0, 0, 0, 0)

        # Batch INSERT
        dwh_col_list = ", ".join(f'"{c}"' for c in dwh_col_names)
        param_list = ", ".join(f":p{i}" for i in range(len(dwh_col_names)))
        insert_sql = f'INSERT INTO "{dwh_table_name}" ({dwh_col_list}) VALUES ({param_list})'

        select_sql = f'SELECT {staging_col_list} FROM "{staging_table}" ORDER BY "_staging_id"'
        result = db.execute(text(select_sql))

        inserted = 0
        batch_size = 500
        batch = []

        for row in result:
            params = {}
            for i, val in enumerate(row):
                params[f"p{i}"] = val
            batch.append(params)

            if len(batch) >= batch_size:
                for p in batch:
                    db.execute(text(insert_sql), p)
                inserted += len(batch)
                batch = []

        # Kalan batch
        if batch:
            for p in batch:
                db.execute(text(insert_sql), p)
            inserted += len(batch)

        db.commit()
        return (total, inserted, 0, total)  # deleted=total çünkü truncate edildi

    @staticmethod
    def _incremental_load(
        db: Session,
        transfer: DwhTransfer,
        staging_table: str,
        dwh_table_name: str,
        dwh_columns: List[DwhColumn],
        column_map: Optional[Dict] = None
    ) -> Tuple[int, int, int, int]:
        """
        Incremental load: Delta bazlı.
        incremental_column > last_incremental_value olan satırları aktarır.
        """
        incr_col = transfer.incremental_column
        if not incr_col:
            raise ValueError("Artımlı yükleme için incremental_column gerekli.")

        last_value = transfer.last_incremental_value

        # Kolon eşlemesi
        dwh_col_names = [col.column_name for col in dwh_columns]
        staging_col_names = DwhTransferService._resolve_column_mapping(
            dwh_col_names, column_map
        )

        # Staging'den delta veri oku
        staging_col_list = ", ".join(f'"{c}"' for c in staging_col_names)

        if last_value:
            where_clause = f'WHERE "{incr_col}" > :last_val'
            select_sql = (
                f'SELECT {staging_col_list} FROM "{staging_table}" '
                f'{where_clause} ORDER BY "{incr_col}"'
            )
            count_sql = f'SELECT COUNT(*) FROM "{staging_table}" {where_clause}'
            total = db.execute(text(count_sql), {"last_val": last_value}).scalar() or 0
        else:
            select_sql = (
                f'SELECT {staging_col_list} FROM "{staging_table}" ORDER BY "{incr_col}"'
            )
            count_sql = f'SELECT COUNT(*) FROM "{staging_table}"'
            total = db.execute(text(count_sql)).scalar() or 0

        if total == 0:
            return (0, 0, 0, 0)

        # INSERT (delta satırlar)
        dwh_col_list = ", ".join(f'"{c}"' for c in dwh_col_names)
        param_list = ", ".join(f":p{i}" for i in range(len(dwh_col_names)))
        insert_sql = f'INSERT INTO "{dwh_table_name}" ({dwh_col_list}) VALUES ({param_list})'

        if last_value:
            result = db.execute(text(select_sql), {"last_val": last_value})
        else:
            result = db.execute(text(select_sql))

        inserted = 0
        max_incr_value = None
        batch = []

        # incr_col'un staging_col_names içindeki indeksi
        # column_map varsa staging adını çöz
        if column_map:
            # column_map: {staging_col: dwh_col} - ters çevir
            reverse_map = {v: k for k, v in column_map.items()}
            staging_incr_col = reverse_map.get(incr_col, incr_col)
        else:
            staging_incr_col = incr_col

        try:
            incr_idx = staging_col_names.index(staging_incr_col)
        except ValueError:
            incr_idx = None

        for row in result:
            params = {}
            for i, val in enumerate(row):
                params[f"p{i}"] = val
            batch.append(params)

            # Max incremental değeri takip et
            if incr_idx is not None and row[incr_idx] is not None:
                val_str = str(row[incr_idx])
                if max_incr_value is None or val_str > max_incr_value:
                    max_incr_value = val_str

            if len(batch) >= 500:
                for p in batch:
                    db.execute(text(insert_sql), p)
                inserted += len(batch)
                batch = []

        if batch:
            for p in batch:
                db.execute(text(insert_sql), p)
            inserted += len(batch)

        db.commit()

        # last_incremental_value güncelle
        if max_incr_value:
            transfer.last_incremental_value = max_incr_value
            db.commit()

        return (total, inserted, 0, 0)

    @staticmethod
    def _append_load(
        db: Session,
        staging_table: str,
        dwh_table_name: str,
        dwh_columns: List[DwhColumn],
        column_map: Optional[Dict] = None
    ) -> Tuple[int, int, int, int]:
        """
        Append load: Sadece INSERT (truncate yok, dedup yok).
        Staging'deki tüm veriyi DWH'a ekler.
        """
        dwh_col_names = [col.column_name for col in dwh_columns]
        staging_col_names = DwhTransferService._resolve_column_mapping(
            dwh_col_names, column_map
        )

        staging_col_list = ", ".join(f'"{c}"' for c in staging_col_names)
        count_result = db.execute(text(f'SELECT COUNT(*) FROM "{staging_table}"'))
        total = count_result.scalar() or 0

        if total == 0:
            return (0, 0, 0, 0)

        dwh_col_list = ", ".join(f'"{c}"' for c in dwh_col_names)
        param_list = ", ".join(f":p{i}" for i in range(len(dwh_col_names)))
        insert_sql = f'INSERT INTO "{dwh_table_name}" ({dwh_col_list}) VALUES ({param_list})'

        select_sql = f'SELECT {staging_col_list} FROM "{staging_table}" ORDER BY "_staging_id"'
        result = db.execute(text(select_sql))

        inserted = 0
        batch = []

        for row in result:
            params = {}
            for i, val in enumerate(row):
                params[f"p{i}"] = val
            batch.append(params)

            if len(batch) >= 500:
                for p in batch:
                    db.execute(text(insert_sql), p)
                inserted += len(batch)
                batch = []

        if batch:
            for p in batch:
                db.execute(text(insert_sql), p)
            inserted += len(batch)

        db.commit()
        return (total, inserted, 0, 0)

    # ============ Preview ============

    @staticmethod
    def preview_transfer(
        db: Session,
        transfer: DwhTransfer,
        limit: int = 20
    ) -> Dict:
        """
        Transfer önizleme: aktarılacak satırları gösterir (kuru çalıştırma).
        """
        source_query = transfer.source_query
        if not source_query or not source_query.staging_table_created:
            return {"columns": [], "rows": [], "total": 0}

        staging_table = source_query.staging_table_name
        dwh_columns = transfer.dwh_table.columns
        column_map = transfer.column_mapping

        dwh_col_names = [col.column_name for col in dwh_columns]
        staging_col_names = DwhTransferService._resolve_column_mapping(
            dwh_col_names, column_map
        )

        staging_col_list = ", ".join(f'"{c}"' for c in staging_col_names)

        # Incremental filtre
        strategy = transfer.load_strategy
        if hasattr(strategy, 'value'):
            strategy = strategy.value

        if strategy == "incremental" and transfer.incremental_column and transfer.last_incremental_value:
            incr_col = transfer.incremental_column
            where = f'WHERE "{incr_col}" > :last_val'
            count_sql = f'SELECT COUNT(*) FROM "{staging_table}" {where}'
            total = db.execute(text(count_sql), {"last_val": transfer.last_incremental_value}).scalar() or 0
            select_sql = (
                f'SELECT {staging_col_list} FROM "{staging_table}" {where} '
                f'ORDER BY "{incr_col}" LIMIT :lim'
            )
            result = db.execute(text(select_sql), {
                "last_val": transfer.last_incremental_value, "lim": limit
            })
        else:
            count_sql = f'SELECT COUNT(*) FROM "{staging_table}"'
            total = db.execute(text(count_sql)).scalar() or 0
            select_sql = (
                f'SELECT {staging_col_list} FROM "{staging_table}" '
                f'ORDER BY "_staging_id" LIMIT :lim'
            )
            result = db.execute(text(select_sql), {"lim": limit})

        rows = []
        for row in result:
            row_dict = {}
            for i, col_name in enumerate(dwh_col_names):
                val = row[i]
                row_dict[col_name] = str(val) if val is not None else None
            rows.append(row_dict)

        return {"columns": dwh_col_names, "rows": rows, "total": total}

    # ============ Helpers ============

    @staticmethod
    def _resolve_column_mapping(
        dwh_col_names: List[str],
        column_map: Optional[Dict] = None
    ) -> List[str]:
        """
        Kolon eşlemesini çözer.
        column_map: {staging_col: dwh_col} formatında.
        DWH kolon adlarına karşılık gelen staging kolon adlarını döndürür.
        """
        if not column_map:
            return dwh_col_names  # 1:1 aynı isimler

        # column_map: {staging_col: dwh_col} -> ters çevir: {dwh_col: staging_col}
        reverse_map = {v: k for k, v in column_map.items()}

        staging_cols = []
        for dwh_col in dwh_col_names:
            staging_col = reverse_map.get(dwh_col, dwh_col)
            staging_cols.append(staging_col)

        return staging_cols
