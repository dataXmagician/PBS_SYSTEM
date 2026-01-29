"""
Period API Endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc
from uuid import UUID
from app.schemas.user import UserResponse
from app.dependencies import get_current_user
from app.db.session import get_db
from app.services.period_service import PeriodService
from app.schemas.period import PeriodCreate, PeriodUpdate, PeriodResponse
from app.models.period import Period
import logging

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/periods",
    tags=["Periods"],
    responses={404: {"description": "Not found"}},
)

# GET - Dönemleri listele (company_id opsiyonel)
@router.get("", response_model=dict)
async def list_periods(
    company_id: UUID = Query(None, description="Şirket ID (opsiyonel)"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Dönemleri listele
    - company_id verilirse: O şirkete ait dönemler
    - company_id yoksa: Tüm dönemler
    """
    try:
        if company_id:
            return PeriodService.get_periods_by_company(db, company_id, skip, limit)
        else:
            # Tüm dönemleri getir
            query = db.query(Period).order_by(desc(Period.fiscal_year), desc(Period.period))
            total = query.count()
            periods = query.offset(skip).limit(limit).all()
            logger.info(f"Dönemler listelendi: {len(periods)} / {total}")
            return {
                "data": [PeriodResponse.model_validate(p) for p in periods],
                "total": total,
                "skip": skip,
                "limit": limit
            }
    except Exception as e:
        logger.error(f"Dönemleri listelerken hata: {e}")
        raise HTTPException(status_code=500, detail="Dönemleri listelemek başarısız")

# GET - Mali yıla göre dönemleri listele
@router.get("/fiscal-year/{fiscal_year}", response_model=dict)
async def list_periods_by_fiscal_year(
    fiscal_year: int,
    company_id: UUID = Query(None, description="Şirket ID (opsiyonel)"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Mali yıla göre dönemleri listele
    - company_id verilirse: O şirkete ait dönemler
    - company_id yoksa: Tüm dönemler
    """
    try:
        if company_id:
            return PeriodService.get_periods_by_fiscal_year(db, company_id, fiscal_year, skip, limit)
        else:
            # Tüm dönemleri getir (fiscal_year'a göre filtrele)
            query = db.query(Period).filter(Period.fiscal_year == fiscal_year).order_by(Period.period)
            total = query.count()
            periods = query.offset(skip).limit(limit).all()
            logger.info(f"Dönemler listelendi: {len(periods)} / {total}")
            return {
                "data": [PeriodResponse.model_validate(p) for p in periods],
                "total": total,
                "fiscal_year": fiscal_year
            }
    except Exception as e:
        logger.error(f"Dönemleri listelerken hata: {e}")
        raise HTTPException(status_code=500, detail="Dönemleri listelemek başarısız")

# GET - Dönem detayı
@router.get("/{period_id}", response_model=PeriodResponse)
async def get_period(
    period_id: UUID,
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Dönem detayını getir
    """
    try:
        period = PeriodService.get_period(db, period_id)
        if not period:
            raise HTTPException(status_code=404, detail=f"Dönem bulunamadı: {period_id}")
        return period
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Dönem detayı getirilirken hata: {e}")
        raise HTTPException(status_code=500, detail="Dönem detayı getirilemedi")

# POST - Yeni dönem oluştur
@router.post("", response_model=PeriodResponse, status_code=201)
async def create_period(
    period_in: PeriodCreate,
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Yeni dönem oluştur
    """
    try:
        return PeriodService.create_period(db, period_in)
    except ValueError as e:
        logger.warning(f"Dönem oluşturmada validasyon hatası: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Dönem oluşturulurken hata: {e}")
        raise HTTPException(status_code=500, detail="Dönem oluşturulamadı")

# PUT - Dönem güncelle
@router.put("/{period_id}", response_model=PeriodResponse)
async def update_period(
    period_id: UUID,
    period_in: PeriodUpdate,
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Dönem güncelle
    """
    try:
        period = PeriodService.update_period(db, period_id, period_in)
        if not period:
            raise HTTPException(status_code=404, detail=f"Dönem bulunamadı: {period_id}")
        return period
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Dönem güncellenirken hata: {e}")
        raise HTTPException(status_code=500, detail="Dönem güncellenemedi")

# DELETE - Dönem sil
@router.delete("/{period_id}", status_code=204)
async def delete_period(
    period_id: UUID,
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Dönem sil
    """
    try:
        success = PeriodService.delete_period(db, period_id)
        if not success:
            raise HTTPException(status_code=404, detail=f"Dönem bulunamadı: {period_id}")
        return None
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Dönem silinirken hata: {e}")
        raise HTTPException(status_code=500, detail="Dönem silinemedi")

# GET - Dönem sayısı
@router.get("/stats/count", response_model=dict)
async def get_period_count(
    company_id: UUID = Query(None, description="Şirket ID (opsiyonel)"),
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Dönem sayısını getir
    - company_id verilirse: O şirkete ait dönem sayısı
    - company_id yoksa: Toplam dönem sayısı
    """
    try:
        if company_id:
            count = PeriodService.get_period_count_by_company(db, company_id)
        else:
            count = db.query(Period).count()
        return {"total_periods": count}
    except Exception as e:
        logger.error(f"Dönem sayısı getirilirken hata: {e}")
        raise HTTPException(status_code=500, detail="Dönem sayısı getirilemedi")
