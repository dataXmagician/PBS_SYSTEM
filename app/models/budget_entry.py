"""
Budget Entry Models - Butce Girisleri
Butce tipi, tanim, satir, hucre, kural seti modelleri
"""

from sqlalchemy import (
    Column, String, Integer, Boolean, DateTime, ForeignKey,
    Enum, UniqueConstraint, Index, Numeric, Text, func
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
import uuid
import enum
from app.db.base import Base


# ============ Enums ============

class BudgetMeasureType(str, enum.Enum):
    input = "input"
    calculated = "calculated"


class MeasureDataType(str, enum.Enum):
    decimal = "decimal"
    integer = "integer"
    currency = "currency"
    percentage = "percentage"


class BudgetDefinitionStatus(str, enum.Enum):
    draft = "draft"
    active = "active"
    locked = "locked"
    archived = "archived"


class BudgetCellType(str, enum.Enum):
    input = "input"
    calculated = "calculated"
    parameter_calculated = "parameter_calculated"


class RuleType(str, enum.Enum):
    fixed_value = "fixed_value"
    parameter_multiplier = "parameter_multiplier"
    formula = "formula"
    currency_assign = "currency_assign"


# ============ Models ============

class BudgetType(Base):
    """
    Butce Tipi modeli
    - SALES (Satis Butcesi), EXPENSE (Gider), INVESTMENT (Yatirim), FINANCE (Finansman)
    - Her tip sabit olculere sahip (BudgetTypeMeasure)
    """
    __tablename__ = "budget_types"

    id = Column(Integer, primary_key=True, autoincrement=True)
    uuid = Column(UUID(as_uuid=True), default=uuid.uuid4, unique=True, nullable=False)
    code = Column(String(50), unique=True, nullable=False, index=True, comment="Butce Tipi Kodu")
    name = Column(String(200), nullable=False, comment="Butce Tipi Adi")
    description = Column(String(500), comment="Aciklama")
    is_active = Column(Boolean, default=True, nullable=False)
    sort_order = Column(Integer, default=0)
    created_date = Column(DateTime, default=func.now(), nullable=False)
    updated_date = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    measures = relationship("BudgetTypeMeasure", back_populates="budget_type", cascade="all, delete-orphan",
                            order_by="BudgetTypeMeasure.sort_order")

    def __repr__(self):
        return f"<BudgetType(id={self.id}, code={self.code})>"


class BudgetTypeMeasure(Base):
    """
    Butce Tipi Olcu modeli
    - Her butce tipinin sabit olculeri (ornek: Satis -> FIYAT, MIKTAR, TUTAR)
    - measure_type: input (kullanici girer) / calculated (formul ile hesaplanir)
    """
    __tablename__ = "budget_type_measures"
    __table_args__ = (
        UniqueConstraint('budget_type_id', 'code', name='uq_budget_type_measure'),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    budget_type_id = Column(Integer, ForeignKey("budget_types.id", ondelete="CASCADE"), nullable=False)
    code = Column(String(50), nullable=False, comment="Olcu Kodu (FIYAT, MIKTAR, TUTAR)")
    name = Column(String(200), nullable=False, comment="Olcu Adi")
    measure_type = Column(
        Enum(BudgetMeasureType, name="budgetmeasuretype", create_type=False),
        nullable=False, comment="input veya calculated"
    )
    data_type = Column(
        Enum(MeasureDataType, name="measuredatatype", create_type=False),
        nullable=False, default=MeasureDataType.decimal, comment="Veri tipi"
    )
    formula = Column(String(500), nullable=True, comment="Hesaplama formulu (ornek: FIYAT * MIKTAR)")
    decimal_places = Column(Integer, default=2, comment="Ondalik basamak sayisi")
    unit = Column(String(20), nullable=True, comment="Birim (TL, adet, %)")
    default_value = Column(String(50), default="0", comment="Varsayilan deger")
    sort_order = Column(Integer, default=0)
    is_active = Column(Boolean, default=True, nullable=False)
    created_date = Column(DateTime, default=func.now(), nullable=False)
    updated_date = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    budget_type = relationship("BudgetType", back_populates="measures")

    def __repr__(self):
        return f"<BudgetTypeMeasure(id={self.id}, code={self.code}, type={self.measure_type})>"


class BudgetDefinition(Base):
    """
    Butce Tanimi modeli
    - Bir versiyon + bir butce tipi + secilen boyut entity'leri
    - Grid'in yapisini belirler
    """
    __tablename__ = "budget_definitions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    uuid = Column(UUID(as_uuid=True), default=uuid.uuid4, unique=True, nullable=False)
    version_id = Column(Integer, ForeignKey("budget_versions.id"), nullable=False, comment="Butce Versiyonu")
    budget_type_id = Column(Integer, ForeignKey("budget_types.id"), nullable=False, comment="Butce Tipi")
    code = Column(String(50), unique=True, nullable=False, index=True, comment="Tanim Kodu")
    name = Column(String(200), nullable=False, comment="Tanim Adi")
    description = Column(String(500), comment="Aciklama")
    status = Column(
        Enum(BudgetDefinitionStatus, name="budgetdefinitionstatus", create_type=False),
        nullable=False, default=BudgetDefinitionStatus.draft, comment="Durum"
    )
    is_active = Column(Boolean, default=True, nullable=False)
    created_by = Column(String(100), nullable=True, comment="Olusturan kullanici")
    sort_order = Column(Integer, default=0)
    created_date = Column(DateTime, default=func.now(), nullable=False)
    updated_date = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    version = relationship("BudgetVersion")
    budget_type = relationship("BudgetType")
    dimensions = relationship("BudgetDefinitionDimension", back_populates="budget_definition",
                              cascade="all, delete-orphan", order_by="BudgetDefinitionDimension.sort_order")
    rows = relationship("BudgetEntryRow", back_populates="budget_definition",
                        cascade="all, delete-orphan")

    def __repr__(self):
        return f"<BudgetDefinition(id={self.id}, code={self.code})>"


class BudgetDefinitionDimension(Base):
    """
    Butce Tanimi Boyut modeli
    - Hangi MetaEntity tipleri bu butcede boyut olarak kullaniliyor
    - Ornek: Product + Product_Group
    """
    __tablename__ = "budget_definition_dimensions"
    __table_args__ = (
        UniqueConstraint('budget_definition_id', 'entity_id', name='uq_budget_def_entity'),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    budget_definition_id = Column(Integer, ForeignKey("budget_definitions.id", ondelete="CASCADE"), nullable=False)
    entity_id = Column(Integer, ForeignKey("meta_entities.id"), nullable=False, comment="Anaveri Tipi")
    sort_order = Column(Integer, default=0)
    is_required = Column(Boolean, default=True)
    created_date = Column(DateTime, default=func.now(), nullable=False)
    updated_date = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    budget_definition = relationship("BudgetDefinition", back_populates="dimensions")
    entity = relationship("MetaEntity")

    def __repr__(self):
        return f"<BudgetDefinitionDimension(id={self.id}, entity_id={self.entity_id})>"


class BudgetEntryRow(Base):
    """
    Butce Giris Satiri modeli
    - Grid'deki bir satir = bir anaveri kombinasyonu
    - dimension_values: {"entity_id_1": master_data_id_1, "entity_id_2": master_data_id_2}
    """
    __tablename__ = "budget_entry_rows"

    id = Column(Integer, primary_key=True, autoincrement=True)
    uuid = Column(UUID(as_uuid=True), default=uuid.uuid4, unique=True, nullable=False)
    budget_definition_id = Column(Integer, ForeignKey("budget_definitions.id", ondelete="CASCADE"),
                                  nullable=False, index=True)
    dimension_values = Column(JSONB, nullable=False, comment="Boyut degerleri JSON: {entity_id: master_data_id}")
    currency_code = Column(String(10), nullable=True, default="TL", comment="Para birimi")
    is_active = Column(Boolean, default=True, nullable=False)
    sort_order = Column(Integer, default=0)
    created_date = Column(DateTime, default=func.now(), nullable=False)
    updated_date = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    budget_definition = relationship("BudgetDefinition", back_populates="rows")
    cells = relationship("BudgetEntryCell", back_populates="row", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<BudgetEntryRow(id={self.id}, dims={self.dimension_values})>"


class BudgetEntryCell(Base):
    """
    Butce Giris Hucresi modeli
    - Bir satir + bir donem + bir olcu = bir hucre degeri
    - value: Numeric(20,4) gercek sayisal deger
    - cell_type: input / calculated / parameter_calculated
    """
    __tablename__ = "budget_entry_cells"
    __table_args__ = (
        UniqueConstraint('row_id', 'period_id', 'measure_code', name='uq_cell_row_period_measure'),
        Index('ix_cell_row_period', 'row_id', 'period_id'),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    row_id = Column(Integer, ForeignKey("budget_entry_rows.id", ondelete="CASCADE"), nullable=False)
    period_id = Column(Integer, ForeignKey("budget_periods.id"), nullable=False)
    measure_code = Column(String(50), nullable=False, comment="Olcu kodu (FIYAT, MIKTAR, TUTAR)")
    value = Column(Numeric(20, 4), nullable=True, comment="Hucre degeri")
    cell_type = Column(
        Enum(BudgetCellType, name="budgetcelltype", create_type=False),
        nullable=False, default=BudgetCellType.input, comment="Hucre tipi"
    )
    source_rule_id = Column(Integer, ForeignKey("rule_set_items.id", ondelete="SET NULL"), nullable=True,
                            comment="Kaynak kural")
    source_param_id = Column(Integer, ForeignKey("budget_parameters.id", ondelete="SET NULL"), nullable=True,
                             comment="Kaynak parametre")
    is_manual_override = Column(Boolean, default=False, comment="Kullanici tarafindan override edildi mi")
    created_date = Column(DateTime, default=func.now(), nullable=False)
    updated_date = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    row = relationship("BudgetEntryRow", back_populates="cells")
    period = relationship("BudgetPeriod")
    source_rule = relationship("RuleSetItem")
    source_param = relationship("BudgetParameter")

    def __repr__(self):
        return f"<BudgetEntryCell(id={self.id}, measure={self.measure_code}, value={self.value})>"


class RuleSet(Base):
    """
    Kural Seti modeli
    - Adi verilen, yeniden kullanilabilir kural gruplari
    - Bir butce tipine bagli
    """
    __tablename__ = "rule_sets"

    id = Column(Integer, primary_key=True, autoincrement=True)
    uuid = Column(UUID(as_uuid=True), default=uuid.uuid4, unique=True, nullable=False)
    budget_type_id = Column(Integer, ForeignKey("budget_types.id"), nullable=False, comment="Butce Tipi")
    code = Column(String(50), unique=True, nullable=False, index=True, comment="Kural Seti Kodu")
    name = Column(String(200), nullable=False, comment="Kural Seti Adi")
    description = Column(String(500), comment="Aciklama")
    is_active = Column(Boolean, default=True, nullable=False)
    sort_order = Column(Integer, default=0)
    created_date = Column(DateTime, default=func.now(), nullable=False)
    updated_date = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    budget_type = relationship("BudgetType")
    items = relationship("RuleSetItem", back_populates="rule_set", cascade="all, delete-orphan",
                         order_by="RuleSetItem.priority, RuleSetItem.sort_order")

    def __repr__(self):
        return f"<RuleSet(id={self.id}, code={self.code})>"


class RuleSetItem(Base):
    """
    Kural Seti Kalemi modeli
    - fixed_value: Sabit deger ata
    - parameter_multiplier: Onceki donem * (1 + parametre degeri)
    - formula: Formul hesapla (ornek: FIYAT * MIKTAR)
    """
    __tablename__ = "rule_set_items"

    id = Column(Integer, primary_key=True, autoincrement=True)
    rule_set_id = Column(Integer, ForeignKey("rule_sets.id", ondelete="CASCADE"), nullable=False)
    rule_type = Column(
        Enum(RuleType, name="ruletype", create_type=False),
        nullable=False, comment="Kural tipi"
    )
    target_measure_code = Column(String(50), nullable=False, comment="Hedef olcu (FIYAT, MIKTAR, TUTAR)")

    # Dimension condition (anaveri attribute filtresi)
    condition_entity_id = Column(Integer, ForeignKey("meta_entities.id"), nullable=True,
                                 comment="Kosul entity tipi")
    condition_attribute_code = Column(String(50), nullable=True, comment="Kosul attribute kodu")
    condition_operator = Column(String(20), default="eq", comment="Kosul operatoru (eq, in, ne)")
    condition_value = Column(String(500), nullable=True, comment="Kosul degeri (tekil veya JSON array)")

    # Period condition
    apply_to_period_ids = Column(JSONB, nullable=True, comment="Uygulanacak donem ID'leri (null=hepsi)")

    # Rule values
    fixed_value = Column(Numeric(20, 4), nullable=True, comment="Sabit deger (fixed_value tipi icin)")
    parameter_id = Column(Integer, ForeignKey("budget_parameters.id"), nullable=True,
                          comment="Parametre (parameter_multiplier tipi icin)")
    parameter_operation = Column(String(20), nullable=True, default="multiply",
                                 comment="Parametre islemi (multiply, add, replace)")
    formula = Column(String(500), nullable=True, comment="Formul (formula tipi icin)")
    currency_code = Column(String(10), nullable=True, comment="Sabit para birimi (currency_assign)")
    currency_source_entity_id = Column(Integer, ForeignKey("meta_entities.id"), nullable=True,
                                       comment="Para birimi kaynagi entity")
    currency_source_attribute_code = Column(String(50), nullable=True, comment="Para birimi kaynagi attribute kodu")

    # Execution
    priority = Column(Integer, default=0, comment="Oncelik (dusuk = once)")
    is_active = Column(Boolean, default=True, nullable=False)
    sort_order = Column(Integer, default=0)
    created_date = Column(DateTime, default=func.now(), nullable=False)
    updated_date = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    rule_set = relationship("RuleSet", back_populates="items")
    condition_entity = relationship("MetaEntity", foreign_keys=[condition_entity_id])
    parameter = relationship("BudgetParameter")
    currency_source_entity = relationship("MetaEntity", foreign_keys=[currency_source_entity_id])

    def __repr__(self):
        return f"<RuleSetItem(id={self.id}, type={self.rule_type}, target={self.target_measure_code})>"


class CalculationSnapshot(Base):
    """Hesaplama oncesi snapshot - Geri alma (undo) icin"""
    __tablename__ = "calculation_snapshots"

    id = Column(Integer, primary_key=True, autoincrement=True)
    budget_definition_id = Column(Integer, ForeignKey("budget_definitions.id", ondelete="CASCADE"), nullable=False, index=True)
    snapshot_data = Column(JSONB, nullable=False, comment="Pre-calculation cell values")
    rule_set_ids = Column(JSONB, nullable=True, comment="Applied rule set IDs")
    created_date = Column(DateTime, default=func.now(), nullable=False)

    definition = relationship("BudgetDefinition")

    def __repr__(self):
        return f"<CalculationSnapshot(id={self.id}, def_id={self.budget_definition_id})>"
