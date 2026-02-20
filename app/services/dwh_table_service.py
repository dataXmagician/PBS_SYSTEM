"""
DWH Table Service - Veri Ambarı Tablo Yönetim Servisi

DWH tablo oluşturma, fiziksel tablo DDL, veri önizleme ve istatistik.
"""

import logging
import re
from datetime import datetime
from typing import Optional, List, Dict, Any

from sqlalchemy.orm import Session
from sqlalchemy import text

from app.models.dwh import (
    DwhTable, DwhColumn, DwhTableSourceType
)
from app.models.data_connection import (
    DataConnectionQuery, DataConnectionColumn, ColumnDataType
)
from app.schemas.data_connection import DataPreviewResponse
from app.schemas.dwh import DwhTableStats

logger = logging.getLogger(__name__)


class DwhTableService:
    """DWH tablo yönetim servisi."""

    # ============ Table Creation ============

    @staticmethod
    def create_from_staging(
        db: Session,
        query: DataConnectionQuery,
        code: str,
        name: str,
        description: Optional[str] = None
    ) -> DwhTable:
        """
        Staging sorgu yapısını kopyalayarak DWH tablosu oluşturur.
        Kolonlar staging kolonlarından kopyalanır.
        """
        import uuid as uuid_lib

        table_name = DwhTableService._generate_table_name(code)

        dwh_table = DwhTable(
            uuid=str(uuid_lib.uuid4()),
            code=code.upper(),
            name=name,
            description=description,
            source_type=DwhTableSourceType.staging_copy,
            source_query_id=query.id,
            table_name=table_name,
            table_created=False,
        )
        db.add(dwh_table)
        db.flush()  # ID al

        # Staging kolonlarını kopyala
        for col in query.columns:
            if not col.is_included:
                continue
            dwh_col = DwhColumn(
                dwh_table_id=dwh_table.id,
                column_name=col.target_name,
                data_type=col.data_type,
                is_nullable=col.is_nullable,
                is_primary_key=col.is_primary_key,
                is_incremental_key=False,
                max_length=col.max_length,
                sort_order=col.sort_order,
            )
            db.add(dwh_col)

        db.commit()
        db.refresh(dwh_table)

        logger.info(f"DWH tablosu oluşturuldu (staging'den): {dwh_table.code} -> {table_name}")
        return dwh_table

    @staticmethod
    def create_custom(
        db: Session,
        code: str,
        name: str,
        description: Optional[str] = None,
        columns: Optional[List[Dict]] = None
    ) -> DwhTable:
        """Kullanıcı tanımlı DWH tablosu oluşturur."""
        import uuid as uuid_lib

        table_name = DwhTableService._generate_table_name(code)

        dwh_table = DwhTable(
            uuid=str(uuid_lib.uuid4()),
            code=code.upper(),
            name=name,
            description=description,
            source_type=DwhTableSourceType.custom,
            source_query_id=None,
            table_name=table_name,
            table_created=False,
        )
        db.add(dwh_table)
        db.flush()

        if columns:
            for i, col_data in enumerate(columns):
                dwh_col = DwhColumn(
                    dwh_table_id=dwh_table.id,
                    column_name=col_data.get("column_name", f"column_{i}"),
                    data_type=col_data.get("data_type", ColumnDataType.string),
                    is_nullable=col_data.get("is_nullable", True),
                    is_primary_key=col_data.get("is_primary_key", False),
                    is_incremental_key=col_data.get("is_incremental_key", False),
                    max_length=col_data.get("max_length"),
                    sort_order=col_data.get("sort_order", i),
                )
                db.add(dwh_col)

        db.commit()
        db.refresh(dwh_table)

        logger.info(f"DWH tablosu oluşturuldu (custom): {dwh_table.code} -> {table_name}")
        return dwh_table

    # ============ Physical Table DDL ============

    @staticmethod
    def create_physical_table(db: Session, dwh_table: DwhTable) -> None:
        """
        DWH tablosu için fiziksel PostgreSQL tablosu oluşturur.
        CREATE TABLE IF NOT EXISTS kullanır (mevcut veriyi korur).
        """
        if not dwh_table.columns:
            raise ValueError("Kolon tanımları boş. Önce kolon tanımlayın.")

        table_name = dwh_table.table_name
        if not table_name:
            raise ValueError("Tablo adı boş.")

        # Kolon DDL oluştur
        col_defs = [
            "_dwh_id SERIAL PRIMARY KEY",
            "_loaded_at TIMESTAMP DEFAULT NOW()"
        ]

        for col in dwh_table.columns:
            pg_type = DwhTableService._column_type_to_pg(col.data_type, col.max_length)
            nullable = "" if col.is_nullable else " NOT NULL"
            col_defs.append(f'"{col.column_name}" {pg_type}{nullable}')

        create_sql = f'CREATE TABLE IF NOT EXISTS "{table_name}" ({", ".join(col_defs)})'

        db.execute(text(create_sql))
        db.commit()

        dwh_table.table_created = True
        db.commit()

        logger.info(f"DWH fiziksel tablo oluşturuldu: {table_name}")

    @staticmethod
    def drop_physical_table(db: Session, dwh_table: DwhTable) -> None:
        """DWH fiziksel tablosunu siler."""
        if dwh_table.table_name:
            db.execute(text(f'DROP TABLE IF EXISTS "{dwh_table.table_name}" CASCADE'))
            db.commit()
            dwh_table.table_created = False
            db.commit()
            logger.info(f"DWH fiziksel tablo silindi: {dwh_table.table_name}")

    # ============ Data Preview ============

    @staticmethod
    def get_data(
        db: Session,
        dwh_table: DwhTable,
        limit: int = 100,
        offset: int = 0
    ) -> DataPreviewResponse:
        """DWH tablosundaki verileri önizler."""
        table_name = dwh_table.table_name

        if not dwh_table.table_created:
            return DataPreviewResponse(columns=[], rows=[], total=0)

        try:
            # Toplam satır sayısı
            count_result = db.execute(text(f'SELECT COUNT(*) FROM "{table_name}"'))
            total = count_result.scalar() or 0

            # Kolon isimleri
            col_names = [col.column_name for col in dwh_table.columns]
            all_cols = ["_dwh_id", "_loaded_at"] + col_names
            col_list = ", ".join(f'"{c}"' for c in all_cols)

            # Veri çek
            data_sql = f'SELECT {col_list} FROM "{table_name}" ORDER BY "_dwh_id" LIMIT :lim OFFSET :off'
            result = db.execute(text(data_sql), {"lim": limit, "off": offset})
            rows_data = result.fetchall()

            rows = []
            for row in rows_data:
                row_dict = {}
                for i, col_name in enumerate(all_cols):
                    val = row[i]
                    if val is not None:
                        row_dict[col_name] = str(val)
                    else:
                        row_dict[col_name] = None
                rows.append(row_dict)

            return DataPreviewResponse(columns=all_cols, rows=rows, total=total)

        except Exception as e:
            logger.error(f"DWH veri önizleme hatası: {e}")
            return DataPreviewResponse(columns=[], rows=[], total=0)

    @staticmethod
    def get_stats(db: Session, dwh_table: DwhTable) -> DwhTableStats:
        """DWH tablosu istatistiklerini döndürür."""
        if not dwh_table.table_created:
            return DwhTableStats(row_count=0, last_loaded_at=None, table_exists=False)

        try:
            table_name = dwh_table.table_name

            # Satır sayısı
            count_result = db.execute(text(f'SELECT COUNT(*) FROM "{table_name}"'))
            row_count = count_result.scalar() or 0

            # Son yükleme tarihi
            last_result = db.execute(
                text(f'SELECT MAX("_loaded_at") FROM "{table_name}"')
            )
            last_loaded = last_result.scalar()

            return DwhTableStats(
                row_count=row_count,
                last_loaded_at=last_loaded,
                table_exists=True
            )
        except Exception as e:
            logger.error(f"DWH istatistik hatası: {e}")
            return DwhTableStats(row_count=0, last_loaded_at=None, table_exists=False)

    # ============ Helpers ============

    @staticmethod
    def _generate_table_name(code: str) -> str:
        """DWH tablo adı üretir: dwh_{sanitized_code}"""
        sanitized = re.sub(r'[^a-z0-9_]', '_', code.lower())
        sanitized = re.sub(r'_+', '_', sanitized).strip('_')
        return f"dwh_{sanitized}"[:100]

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
