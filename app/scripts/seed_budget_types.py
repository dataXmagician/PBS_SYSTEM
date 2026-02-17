"""
Seed script: SALES butce tipini ve olculerini olusturur.
Calistirma: python -m app.scripts.seed_budget_types
"""

import sys
sys.path.insert(0, '.')

from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from app.config import settings
from app.models.budget_entry import (
    BudgetType, BudgetTypeMeasure,
    BudgetMeasureType, MeasureDataType
)
# Import related models so SQLAlchemy can resolve relationships
from app.models.system_data import BudgetVersion, BudgetPeriod, BudgetParameter
from app.models.dynamic.meta_entity import MetaEntity

def seed():
    engine = create_engine(settings.DATABASE_URL)
    with Session(engine) as db:
        # Check if SALES already exists
        existing = db.query(BudgetType).filter(BudgetType.code == "SALES").first()
        if existing:
            print(f"SALES budget type already exists (id={existing.id}). Skipping.")
            return

        # Create SALES budget type
        sales_type = BudgetType(
            code="SALES",
            name="Satis Butcesi",
            description="Urun bazli satis butcesi: Fiyat x Miktar = Tutar",
            is_active=True,
            sort_order=1,
        )
        db.add(sales_type)
        db.flush()  # Get the id

        # Create measures for SALES
        measures = [
            BudgetTypeMeasure(
                budget_type_id=sales_type.id,
                code="FIYAT",
                name="Fiyat",
                measure_type=BudgetMeasureType.input,
                data_type=MeasureDataType.currency,
                formula=None,
                decimal_places=2,
                unit="TL",
                default_value="0",
                sort_order=1,
                is_active=True,
            ),
            BudgetTypeMeasure(
                budget_type_id=sales_type.id,
                code="MIKTAR",
                name="Miktar",
                measure_type=BudgetMeasureType.input,
                data_type=MeasureDataType.integer,
                formula=None,
                decimal_places=0,
                unit="adet",
                default_value="0",
                sort_order=2,
                is_active=True,
            ),
            BudgetTypeMeasure(
                budget_type_id=sales_type.id,
                code="TUTAR",
                name="Tutar",
                measure_type=BudgetMeasureType.calculated,
                data_type=MeasureDataType.currency,
                formula="FIYAT * MIKTAR",
                decimal_places=2,
                unit="TL",
                default_value="0",
                sort_order=3,
                is_active=True,
            ),
        ]
        db.add_all(measures)
        db.commit()
        print(f"Created SALES budget type (id={sales_type.id}) with 3 measures: FIYAT, MIKTAR, TUTAR")


if __name__ == "__main__":
    seed()
