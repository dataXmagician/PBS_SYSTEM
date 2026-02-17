"""
System Data Models - Sistem Verileri (Versiyon, Dönem, Parametre)
"""

from sqlalchemy import Column, String, Integer, Boolean, DateTime, ForeignKey, Enum, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
import enum
from app.db.base import Base


class ParameterValueType(str, enum.Enum):
    tutar = "tutar"
    miktar = "miktar"
    sayi = "sayi"
    yuzde = "yuzde"


class BudgetVersion(Base):
    """
    Bütçe Versiyon modeli
    - Versiyon kodu (ör: V2024, V2024_REV1)
    - Versiyon adı (ör: 2024 Bütçesi, 2024 Revize 1)
    - Başlangıç ve bitiş dönemleri
    """
    __tablename__ = "budget_versions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    uuid = Column(UUID(as_uuid=True), default=uuid.uuid4, unique=True, nullable=False)
    code = Column(String(50), unique=True, nullable=False, index=True, comment="Versiyon Kodu")
    name = Column(String(200), nullable=False, comment="Versiyon Adı")
    description = Column(String(500), comment="Açıklama")
    start_period_id = Column(Integer, ForeignKey("budget_periods.id"), nullable=True, comment="Başlangıç Dönemi")
    end_period_id = Column(Integer, ForeignKey("budget_periods.id"), nullable=True, comment="Bitiş Dönemi")
    is_active = Column(Boolean, default=True, nullable=False)
    is_locked = Column(Boolean, default=False, nullable=False, comment="Kilitli (değişiklik yapılamaz)")
    copied_from_id = Column(Integer, ForeignKey("budget_versions.id"), nullable=True, comment="Kopyalandığı versiyon")
    sort_order = Column(Integer, default=0)
    created_date = Column(DateTime, default=func.now(), nullable=False)
    updated_date = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    start_period = relationship("BudgetPeriod", foreign_keys=[start_period_id])
    end_period = relationship("BudgetPeriod", foreign_keys=[end_period_id])
    copied_from = relationship("BudgetVersion", remote_side=[id], foreign_keys=[copied_from_id])

    def __repr__(self):
        return f"<BudgetVersion(id={self.id}, code={self.code}, name={self.name})>"


class BudgetPeriod(Base):
    """
    Bütçe Dönem modeli
    - Dönem kodu yyyy-MM formatında (ör: 2024-01, 2024-12)
    - Dönem adı otomatik (ör: Ocak 2024, Aralık 2024)
    """
    __tablename__ = "budget_periods"

    id = Column(Integer, primary_key=True, autoincrement=True)
    uuid = Column(UUID(as_uuid=True), default=uuid.uuid4, unique=True, nullable=False)
    code = Column(String(7), unique=True, nullable=False, index=True, comment="Dönem Kodu (yyyy-MM)")
    name = Column(String(100), nullable=False, comment="Dönem Adı (ör: Ocak 2024)")
    year = Column(Integer, nullable=False, index=True, comment="Yıl")
    month = Column(Integer, nullable=False, comment="Ay (1-12)")
    quarter = Column(Integer, nullable=False, comment="Çeyrek (1-4)")
    is_active = Column(Boolean, default=True, nullable=False)
    sort_order = Column(Integer, default=0)
    created_date = Column(DateTime, default=func.now(), nullable=False)
    updated_date = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)

    def __repr__(self):
        return f"<BudgetPeriod(id={self.id}, code={self.code}, name={self.name})>"

    @staticmethod
    def generate_name(year: int, month: int) -> str:
        """Ay ve yıla göre dönem adı oluştur"""
        month_names = {
            1: "Ocak", 2: "Şubat", 3: "Mart", 4: "Nisan",
            5: "Mayıs", 6: "Haziran", 7: "Temmuz", 8: "Ağustos",
            9: "Eylül", 10: "Ekim", 11: "Kasım", 12: "Aralık"
        }
        return f"{month_names.get(month, '')} {year}"

    @staticmethod
    def get_quarter(month: int) -> int:
        """Aya göre çeyrek dönem hesapla"""
        return (month - 1) // 3 + 1


class BudgetParameter(Base):
    """
    Bütçe Parametre modeli (tanım)
    - Parametre kodu (ör: ENFLASYON, KUR_USD)
    - Değer tipi: tutar, miktar, sayi, yuzde
    - Değerler versiyon bazlı: parameter_versions ara tablosunda tutulur
    """
    __tablename__ = "budget_parameters"

    id = Column(Integer, primary_key=True, autoincrement=True)
    uuid = Column(UUID(as_uuid=True), default=uuid.uuid4, unique=True, nullable=False)
    code = Column(String(50), unique=True, nullable=False, index=True, comment="Parametre Kodu")
    name = Column(String(200), nullable=False, comment="Parametre Adı")
    description = Column(String(500), comment="Açıklama")
    value_type = Column(
        Enum(ParameterValueType, name="parametervaluetype", create_type=False),
        nullable=False,
        comment="Değer Tipi (tutar, miktar, sayi, yuzde)"
    )
    is_active = Column(Boolean, default=True, nullable=False)
    sort_order = Column(Integer, default=0)
    created_date = Column(DateTime, default=func.now(), nullable=False)
    updated_date = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    version_values = relationship("ParameterVersion", back_populates="parameter", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<BudgetParameter(id={self.id}, code={self.code}, name={self.name})>"


class BudgetCurrency(Base):
    """
    Para Birimi modeli (global)
    - Kod (USD, EUR, TRY)
    - Ad/Metin (US Dollar, Euro, Turkish Lira)
    - Varsayilan olarak pasif
    """
    __tablename__ = "budget_currencies"

    id = Column(Integer, primary_key=True, autoincrement=True)
    uuid = Column(UUID(as_uuid=True), default=uuid.uuid4, unique=True, nullable=False)
    code = Column(String(10), unique=True, nullable=False, index=True, comment="Para Birimi Kodu")
    name = Column(String(200), nullable=False, comment="Para Birimi Adi")
    is_active = Column(Boolean, default=False, nullable=False)
    sort_order = Column(Integer, default=0)
    created_date = Column(DateTime, default=func.now(), nullable=False)
    updated_date = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)

    def __repr__(self):
        return f"<BudgetCurrency(id={self.id}, code={self.code}, name={self.name})>"


class ParameterVersion(Base):
    """
    Parametre-Versiyon ara tablosu
    - Bir parametre birden fazla versiyonda farklı değerlerle kullanılabilir
    - Örn: ENFLASYON → V2024: %12.5, V2025: %8.0
    """
    __tablename__ = "parameter_versions"
    __table_args__ = (
        UniqueConstraint('parameter_id', 'version_id', name='uq_parameter_version'),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    parameter_id = Column(Integer, ForeignKey("budget_parameters.id", ondelete="CASCADE"), nullable=False)
    version_id = Column(Integer, ForeignKey("budget_versions.id", ondelete="CASCADE"), nullable=False)
    value = Column(String(500), nullable=True, comment="Bu versiyondaki parametre değeri")

    # Relationships
    parameter = relationship("BudgetParameter", back_populates="version_values")
    version = relationship("BudgetVersion")
