"""
System Data API - Sistem Verileri (Versiyon, Dönem, Parametre)
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
import logging

from app.db.session import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.models.system_data import BudgetVersion, BudgetPeriod, BudgetParameter, ParameterVersion, BudgetCurrency
from app.schemas.system_data import (
    BudgetPeriodCreate,
    BudgetPeriodResponse,
    BudgetPeriodListResponse,
    BudgetVersionCreate,
    BudgetVersionUpdate,
    BudgetVersionCopy,
    BudgetVersionResponse,
    BudgetVersionListResponse,
    BudgetParameterCreate,
    BudgetParameterUpdate,
    BudgetParameterResponse,
    BudgetParameterListResponse,
    BudgetCurrencyCreate,
    BudgetCurrencyUpdate,
    BudgetCurrencyResponse,
    BudgetCurrencyListResponse,
    VersionValueResponse,
    SystemDataSummary,
)

VALID_VALUE_TYPES = ["tutar", "miktar", "sayi", "yuzde"]

router = APIRouter(prefix="/system-data", tags=["System Data - Sistem Verileri"])


def _build_version_values(parameter: BudgetParameter, db: Session) -> list:
    """Parametre için versiyon-değer listesi oluştur"""
    result = []
    for pv in parameter.version_values:
        version = db.query(BudgetVersion).filter(BudgetVersion.id == pv.version_id).first()
        if version:
            result.append(VersionValueResponse(
                version_id=version.id,
                version_code=version.code,
                version_name=version.name,
                value=pv.value,
            ))
    return result


def _build_parameter_response(parameter: BudgetParameter, db: Session) -> dict:
    """Parametre response dict'i oluştur"""
    return BudgetParameterResponse(
        id=parameter.id,
        uuid=parameter.uuid,
        code=parameter.code,
        name=parameter.name,
        description=parameter.description,
        value_type=parameter.value_type.value if hasattr(parameter.value_type, 'value') else parameter.value_type,
        version_values=_build_version_values(parameter, db),
        is_active=parameter.is_active,
        sort_order=parameter.sort_order,
        created_date=parameter.created_date,
        updated_date=parameter.updated_date,
    )
logger = logging.getLogger(__name__)

# Türkçe ay isimleri
MONTH_NAMES = {
    1: "Ocak", 2: "Şubat", 3: "Mart", 4: "Nisan",
    5: "Mayıs", 6: "Haziran", 7: "Temmuz", 8: "Ağustos",
    9: "Eylül", 10: "Ekim", 11: "Kasım", 12: "Aralık"
}


def get_quarter(month: int) -> int:
    """Aya göre çeyrek hesapla"""
    return (month - 1) // 3 + 1


def generate_period_name(year: int, month: int) -> str:
    """Dönem adı oluştur"""
    return f"{MONTH_NAMES.get(month, '')} {year}"


# ============ System Data Summary ============

@router.get("/summary", response_model=List[SystemDataSummary])
async def get_system_data_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Sistem verileri özet listesi"""
    version_count = db.query(func.count(BudgetVersion.id)).scalar() or 0
    period_count = db.query(func.count(BudgetPeriod.id)).scalar() or 0
    parameter_count = db.query(func.count(BudgetParameter.id)).scalar() or 0
    currency_count = db.query(func.count(BudgetCurrency.id)).scalar() or 0

    return [
        SystemDataSummary(
            entity_type="version",
            code="VERSION",
            name="Versiyon",
            icon="layers",
            color="purple",
            description="Bütçe versiyonları (Ana bütçe, revizyonlar)",
            record_count=version_count
        ),
        SystemDataSummary(
            entity_type="period",
            code="PERIOD",
            name="Dönem",
            icon="calendar",
            color="blue",
            description="Bütçe dönemleri (yyyy-MM formatında)",
            record_count=period_count
        ),
        SystemDataSummary(
            entity_type="parameter",
            code="PARAMETER",
            name="Parametre",
            icon="settings",
            color="orange",
            description="Bütçe parametreleri (tutar, miktar, sayı, yüzde)",
            record_count=parameter_count
        ),
        SystemDataSummary(
            entity_type="currency",
            code="CURRENCY",
            name="Para Birimi",
            icon="dollar-sign",
            color="green",
            description="Global para birimleri (versiyon bagimsiz)",
            record_count=currency_count
        ),
    ]


# ============ Budget Period Endpoints ============

@router.get("/periods", response_model=BudgetPeriodListResponse)
async def list_periods(
    year: Optional[int] = None,
    is_active: bool = True,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Dönem listesi"""
    try:
        query = db.query(BudgetPeriod)

        if year:
            query = query.filter(BudgetPeriod.year == year)

        if is_active is not None:
            query = query.filter(BudgetPeriod.is_active == is_active)

        total = query.count()
        items = query.order_by(BudgetPeriod.code).all()

        return BudgetPeriodListResponse(items=items, total=total)
    except Exception as e:
        logger.exception("Error in list_periods")
        raise HTTPException(status_code=500, detail="Server error while listing periods")


@router.get("/periods/{period_id}", response_model=BudgetPeriodResponse)
async def get_period(
    period_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Dönem detayı"""
    period = db.query(BudgetPeriod).filter(BudgetPeriod.id == period_id).first()
    if not period:
        raise HTTPException(status_code=404, detail="Dönem bulunamadı")
    return period


@router.post("/periods/expand", response_model=BudgetPeriodListResponse)
async def expand_periods(
    data: BudgetPeriodCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Dönem aralığını genişlet/oluştur.
    Başlangıç ve bitiş dönemleri arasındaki tüm dönemleri oluşturur.
    Mevcut dönemler atlanır.
    """
    # Parse start and end periods
    start_year, start_month = map(int, data.start_period.split('-'))
    end_year, end_month = map(int, data.end_period.split('-'))

    # Validate
    if start_year > end_year or (start_year == end_year and start_month > end_month):
        raise HTTPException(
            status_code=400,
            detail="Başlangıç dönemi bitiş döneminden sonra olamaz"
        )

    created_periods = []
    current_year = start_year
    current_month = start_month

    while (current_year < end_year) or (current_year == end_year and current_month <= end_month):
        code = f"{current_year}-{current_month:02d}"

        # Check if period already exists
        existing = db.query(BudgetPeriod).filter(BudgetPeriod.code == code).first()
        if not existing:
            period = BudgetPeriod(
                code=code,
                name=generate_period_name(current_year, current_month),
                year=current_year,
                month=current_month,
                quarter=get_quarter(current_month),
                sort_order=current_year * 100 + current_month
            )
            db.add(period)
            created_periods.append(period)

        # Move to next month
        current_month += 1
        if current_month > 12:
            current_month = 1
            current_year += 1

    db.commit()

    # Refresh and return all periods in range
    all_periods = db.query(BudgetPeriod).filter(
        BudgetPeriod.code >= data.start_period,
        BudgetPeriod.code <= data.end_period
    ).order_by(BudgetPeriod.code).all()

    return BudgetPeriodListResponse(items=all_periods, total=len(all_periods))


@router.delete("/periods/{period_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_period(
    period_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Dönem sil"""
    period = db.query(BudgetPeriod).filter(BudgetPeriod.id == period_id).first()
    if not period:
        raise HTTPException(status_code=404, detail="Dönem bulunamadı")

    # Check if period is used in any version
    used_in_version = db.query(BudgetVersion).filter(
        (BudgetVersion.start_period_id == period_id) |
        (BudgetVersion.end_period_id == period_id)
    ).first()

    if used_in_version:
        raise HTTPException(
            status_code=400,
            detail=f"Bu dönem '{used_in_version.name}' versiyonunda kullanılıyor"
        )

    db.delete(period)
    db.commit()
    return None


# ============ Budget Version Endpoints ============

@router.get("/versions", response_model=BudgetVersionListResponse)
async def list_versions(
    is_active: Optional[bool] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Versiyon listesi"""
    try:
        query = db.query(BudgetVersion)

        if is_active is not None:
            query = query.filter(BudgetVersion.is_active == is_active)

        total = query.count()
        items = query.order_by(BudgetVersion.sort_order, BudgetVersion.code).all()

        # Enrich with period info
        for item in items:
            if item.start_period_id:
                item.start_period = db.query(BudgetPeriod).filter(BudgetPeriod.id == item.start_period_id).first()
            if item.end_period_id:
                item.end_period = db.query(BudgetPeriod).filter(BudgetPeriod.id == item.end_period_id).first()

        return BudgetVersionListResponse(items=items, total=total)
    except Exception as e:
        logger.exception("Error in list_versions")
        raise HTTPException(status_code=500, detail="Server error while listing versions")


@router.get("/versions/{version_id}", response_model=BudgetVersionResponse)
async def get_version(
    version_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Versiyon detayı"""
    version = db.query(BudgetVersion).filter(BudgetVersion.id == version_id).first()
    if not version:
        raise HTTPException(status_code=404, detail="Versiyon bulunamadı")

    # Enrich with period info
    if version.start_period_id:
        version.start_period = db.query(BudgetPeriod).filter(BudgetPeriod.id == version.start_period_id).first()
    if version.end_period_id:
        version.end_period = db.query(BudgetPeriod).filter(BudgetPeriod.id == version.end_period_id).first()

    return version


@router.post("/versions", response_model=BudgetVersionResponse, status_code=status.HTTP_201_CREATED)
async def create_version(
    data: BudgetVersionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Yeni versiyon oluştur"""
    # Check unique code
    existing = db.query(BudgetVersion).filter(BudgetVersion.code == data.code.upper()).first()
    if existing:
        raise HTTPException(status_code=400, detail=f"'{data.code}' kodu zaten mevcut")

    # Validate period IDs
    if data.start_period_id:
        start_period = db.query(BudgetPeriod).filter(BudgetPeriod.id == data.start_period_id).first()
        if not start_period:
            raise HTTPException(status_code=400, detail="Başlangıç dönemi bulunamadı")

    if data.end_period_id:
        end_period = db.query(BudgetPeriod).filter(BudgetPeriod.id == data.end_period_id).first()
        if not end_period:
            raise HTTPException(status_code=400, detail="Bitiş dönemi bulunamadı")

    version = BudgetVersion(
        code=data.code.upper(),
        name=data.name,
        description=data.description,
        start_period_id=data.start_period_id,
        end_period_id=data.end_period_id,
        is_active=data.is_active
    )

    db.add(version)
    db.commit()
    db.refresh(version)

    # Enrich with period info
    if version.start_period_id:
        version.start_period = db.query(BudgetPeriod).filter(BudgetPeriod.id == version.start_period_id).first()
    if version.end_period_id:
        version.end_period = db.query(BudgetPeriod).filter(BudgetPeriod.id == version.end_period_id).first()

    return version


@router.put("/versions/{version_id}", response_model=BudgetVersionResponse)
async def update_version(
    version_id: int,
    data: BudgetVersionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Versiyon güncelle"""
    version = db.query(BudgetVersion).filter(BudgetVersion.id == version_id).first()
    if not version:
        raise HTTPException(status_code=404, detail="Versiyon bulunamadı")

    if version.is_locked and not data.is_locked:
        # Only unlock is allowed on locked versions
        pass
    elif version.is_locked:
        raise HTTPException(status_code=400, detail="Kilitli versiyon değiştirilemez")

    update_data = data.dict(exclude_unset=True)

    # Check unique code if changed
    if 'code' in update_data and update_data['code']:
        existing = db.query(BudgetVersion).filter(
            BudgetVersion.code == update_data['code'].upper(),
            BudgetVersion.id != version_id
        ).first()
        if existing:
            raise HTTPException(status_code=400, detail=f"'{update_data['code']}' kodu zaten mevcut")
        update_data['code'] = update_data['code'].upper()

    for field, value in update_data.items():
        setattr(version, field, value)

    db.commit()
    db.refresh(version)

    # Enrich with period info
    if version.start_period_id:
        version.start_period = db.query(BudgetPeriod).filter(BudgetPeriod.id == version.start_period_id).first()
    if version.end_period_id:
        version.end_period = db.query(BudgetPeriod).filter(BudgetPeriod.id == version.end_period_id).first()

    return version


@router.post("/versions/{version_id}/copy", response_model=BudgetVersionResponse, status_code=status.HTTP_201_CREATED)
async def copy_version(
    version_id: int,
    data: BudgetVersionCopy,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Versiyonu kopyala"""
    source = db.query(BudgetVersion).filter(BudgetVersion.id == version_id).first()
    if not source:
        raise HTTPException(status_code=404, detail="Kaynak versiyon bulunamadı")

    # Check unique code
    existing = db.query(BudgetVersion).filter(BudgetVersion.code == data.new_code.upper()).first()
    if existing:
        raise HTTPException(status_code=400, detail=f"'{data.new_code}' kodu zaten mevcut")

    new_version = BudgetVersion(
        code=data.new_code.upper(),
        name=data.new_name,
        description=data.description or source.description,
        start_period_id=source.start_period_id,
        end_period_id=source.end_period_id,
        is_active=True,
        is_locked=False,
        copied_from_id=source.id
    )

    db.add(new_version)
    db.commit()
    db.refresh(new_version)

    # Copy parameters if requested
    if data.copy_parameters:
        source_pvs = db.query(ParameterVersion).filter(
            ParameterVersion.version_id == version_id
        ).all()
        for pv in source_pvs:
            new_pv = ParameterVersion(
                parameter_id=pv.parameter_id,
                version_id=new_version.id,
                value=pv.value,
            )
            db.add(new_pv)
        db.commit()
        logger.info(f"Copied {len(source_pvs)} parameter values from {source.code} to {new_version.code}")

    logger.info(f"Version {source.code} copied to {new_version.code}")

    # Enrich with period info
    if new_version.start_period_id:
        new_version.start_period = db.query(BudgetPeriod).filter(BudgetPeriod.id == new_version.start_period_id).first()
    if new_version.end_period_id:
        new_version.end_period = db.query(BudgetPeriod).filter(BudgetPeriod.id == new_version.end_period_id).first()

    return new_version


@router.delete("/versions/{version_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_version(
    version_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Versiyon sil"""
    version = db.query(BudgetVersion).filter(BudgetVersion.id == version_id).first()
    if not version:
        raise HTTPException(status_code=404, detail="Versiyon bulunamadı")

    if version.is_locked:
        raise HTTPException(status_code=400, detail="Kilitli versiyon silinemez")

    db.delete(version)
    db.commit()
    return None


# ============ Budget Parameter Endpoints ============

@router.get("/parameters", response_model=BudgetParameterListResponse)
async def list_parameters(
    version_id: Optional[int] = None,
    is_active: Optional[bool] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Parametre listesi. version_id verilirse sadece o versiyonda değeri olan parametreler döner."""
    try:
        query = db.query(BudgetParameter)

        if version_id is not None:
            query = query.filter(
                BudgetParameter.id.in_(
                    db.query(ParameterVersion.parameter_id).filter(ParameterVersion.version_id == version_id)
                )
            )

        if is_active is not None:
            query = query.filter(BudgetParameter.is_active == is_active)

        total = query.count()
        items = query.order_by(BudgetParameter.sort_order, BudgetParameter.code).all()

        return BudgetParameterListResponse(
            items=[_build_parameter_response(item, db) for item in items],
            total=total,
        )
    except Exception as e:
        logger.exception("Error in list_parameters")
        raise HTTPException(status_code=500, detail="Server error while listing parameters")


@router.get("/parameters/{parameter_id}", response_model=BudgetParameterResponse)
async def get_parameter(
    parameter_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Parametre detayı"""
    parameter = db.query(BudgetParameter).filter(BudgetParameter.id == parameter_id).first()
    if not parameter:
        raise HTTPException(status_code=404, detail="Parametre bulunamadı")
    return _build_parameter_response(parameter, db)


@router.post("/parameters", response_model=BudgetParameterResponse, status_code=status.HTTP_201_CREATED)
async def create_parameter(
    data: BudgetParameterCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Yeni parametre oluştur"""
    # Validate value_type
    if data.value_type not in VALID_VALUE_TYPES:
        raise HTTPException(status_code=400, detail=f"Geçersiz değer tipi. Geçerli tipler: {', '.join(VALID_VALUE_TYPES)}")

    # Check unique code
    existing = db.query(BudgetParameter).filter(BudgetParameter.code == data.code.upper()).first()
    if existing:
        raise HTTPException(status_code=400, detail=f"'{data.code}' kodu zaten mevcut")

    # Validate version_ids
    for vv in data.version_values:
        version = db.query(BudgetVersion).filter(BudgetVersion.id == vv.version_id).first()
        if not version:
            raise HTTPException(status_code=400, detail=f"Versiyon bulunamadı (id={vv.version_id})")

    parameter = BudgetParameter(
        code=data.code.upper(),
        name=data.name,
        description=data.description,
        value_type=data.value_type,
        is_active=data.is_active,
    )

    db.add(parameter)
    db.flush()  # get parameter.id

    # Create version-value entries
    for vv in data.version_values:
        pv = ParameterVersion(
            parameter_id=parameter.id,
            version_id=vv.version_id,
            value=vv.value,
        )
        db.add(pv)

    db.commit()
    db.refresh(parameter)

    return _build_parameter_response(parameter, db)


@router.put("/parameters/{parameter_id}", response_model=BudgetParameterResponse)
async def update_parameter(
    parameter_id: int,
    data: BudgetParameterUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Parametre güncelle"""
    parameter = db.query(BudgetParameter).filter(BudgetParameter.id == parameter_id).first()
    if not parameter:
        raise HTTPException(status_code=404, detail="Parametre bulunamadı")

    # Update simple fields
    if data.code is not None:
        existing = db.query(BudgetParameter).filter(
            BudgetParameter.code == data.code.upper(),
            BudgetParameter.id != parameter_id
        ).first()
        if existing:
            raise HTTPException(status_code=400, detail=f"'{data.code}' kodu zaten mevcut")
        parameter.code = data.code.upper()

    if data.name is not None:
        parameter.name = data.name

    if data.description is not None:
        parameter.description = data.description

    if data.value_type is not None:
        if data.value_type not in VALID_VALUE_TYPES:
            raise HTTPException(status_code=400, detail=f"Geçersiz değer tipi. Geçerli tipler: {', '.join(VALID_VALUE_TYPES)}")
        parameter.value_type = data.value_type

    if data.is_active is not None:
        parameter.is_active = data.is_active

    # Update version_values if provided (replace all)
    if data.version_values is not None:
        # Validate version_ids
        for vv in data.version_values:
            version = db.query(BudgetVersion).filter(BudgetVersion.id == vv.version_id).first()
            if not version:
                raise HTTPException(status_code=400, detail=f"Versiyon bulunamadı (id={vv.version_id})")

        # Delete existing and recreate
        db.query(ParameterVersion).filter(ParameterVersion.parameter_id == parameter_id).delete()
        for vv in data.version_values:
            pv = ParameterVersion(
                parameter_id=parameter_id,
                version_id=vv.version_id,
                value=vv.value,
            )
            db.add(pv)

    db.commit()
    db.refresh(parameter)

    return _build_parameter_response(parameter, db)


@router.delete("/parameters/{parameter_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_parameter(
    parameter_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Parametre sil (cascade ile version_values da silinir)"""
    parameter = db.query(BudgetParameter).filter(BudgetParameter.id == parameter_id).first()
    if not parameter:
        raise HTTPException(status_code=404, detail="Parametre bulunamadı")

    db.delete(parameter)
    db.commit()
    return None


# ============ Budget Currency Endpoints ============

@router.get("/currencies", response_model=BudgetCurrencyListResponse)
async def list_currencies(
    is_active: Optional[bool] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Para birimi listesi"""
    try:
        query = db.query(BudgetCurrency)
        if is_active is not None:
            query = query.filter(BudgetCurrency.is_active == is_active)
        total = query.count()
        items = query.order_by(BudgetCurrency.sort_order, BudgetCurrency.code).all()
        return BudgetCurrencyListResponse(items=items, total=total)
    except Exception:
        logger.exception("Error in list_currencies")
        raise HTTPException(status_code=500, detail="Server error while listing currencies")


@router.get("/currencies/{currency_id}", response_model=BudgetCurrencyResponse)
async def get_currency(
    currency_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Para birimi detayÄ±"""
    currency = db.query(BudgetCurrency).filter(BudgetCurrency.id == currency_id).first()
    if not currency:
        raise HTTPException(status_code=404, detail="Para birimi bulunamadÄ±")
    return currency


@router.post("/currencies", response_model=BudgetCurrencyResponse, status_code=status.HTTP_201_CREATED)
async def create_currency(
    data: BudgetCurrencyCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Yeni para birimi oluÅŸtur"""
    existing = db.query(BudgetCurrency).filter(BudgetCurrency.code == data.code.upper()).first()
    if existing:
        raise HTTPException(status_code=400, detail=f"'{data.code}' kodu zaten mevcut")

    currency = BudgetCurrency(
        code=data.code.upper(),
        name=data.name,
        is_active=data.is_active,
    )
    db.add(currency)
    db.commit()
    db.refresh(currency)
    return currency


@router.put("/currencies/{currency_id}", response_model=BudgetCurrencyResponse)
async def update_currency(
    currency_id: int,
    data: BudgetCurrencyUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Para birimi gÃ¼ncelle"""
    currency = db.query(BudgetCurrency).filter(BudgetCurrency.id == currency_id).first()
    if not currency:
        raise HTTPException(status_code=404, detail="Para birimi bulunamadÄ±")

    update_data = data.dict(exclude_unset=True)

    if "code" in update_data and update_data["code"]:
        existing = db.query(BudgetCurrency).filter(
            BudgetCurrency.code == update_data["code"].upper(),
            BudgetCurrency.id != currency_id
        ).first()
        if existing:
            raise HTTPException(status_code=400, detail=f"'{update_data['code']}' kodu zaten mevcut")
        update_data["code"] = update_data["code"].upper()

    for field, value in update_data.items():
        setattr(currency, field, value)

    db.commit()
    db.refresh(currency)
    return currency


@router.delete("/currencies/{currency_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_currency(
    currency_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Para birimi sil"""
    currency = db.query(BudgetCurrency).filter(BudgetCurrency.id == currency_id).first()
    if not currency:
        raise HTTPException(status_code=404, detail="Para birimi bulunamadÄ±")

    db.delete(currency)
    db.commit()
    return None
