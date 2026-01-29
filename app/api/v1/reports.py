"""
Report API Endpoints - Rapor oluşturma
"""

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from uuid import UUID
from app.db.session import get_db
from app.dependencies import get_current_user
from app.services.report_service import ReportService
from app.schemas.user import UserResponse
import logging

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/reports",
    tags=["Reports"],
    responses={404: {"description": "Not found"}},
)

# POST - Özet rapor oluştur
@router.post("/budget/{budget_id}/summary")
async def generate_summary_report(
    budget_id: UUID,
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Bütçe için özet rapor oluştur (JSON)
    
    **Rapor İçeriği:**
    - Orijinal vs Revize vs Gerçek vs Tahmin tutarları
    - Toplam varyans ve yüzdesi
    - Satır sayısı
    """
    try:
        logger.info(f"{current_user.username} özet rapor oluşturuyor: {budget_id}")
        
        report_data = ReportService.generate_summary_report(db, budget_id)
        
        logger.info(f"Özet rapor oluşturuldu: {budget_id}")
        return JSONResponse(content=report_data)
        
    except ValueError as e:
        logger.warning(f"Rapor oluşturmada validasyon hatası: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Özet rapor oluşturulurken hata: {e}")
        raise HTTPException(status_code=500, detail="Rapor oluşturulamadı")

# POST - Detaylı rapor oluştur
@router.post("/budget/{budget_id}/detailed")
async def generate_detailed_report(
    budget_id: UUID,
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Bütçe için detaylı rapor oluştur (JSON)
    
    **Rapor İçeriği:**
    - Tüm bütçe satırlarının detayları
    - Her satır için orijinal, revize, gerçek, tahmin
    - Her satır için varyans hesaplaması
    """
    try:
        logger.info(f"{current_user.username} detaylı rapor oluşturuyor: {budget_id}")
        
        report_data = ReportService.generate_detailed_report(db, budget_id)
        
        logger.info(f"Detaylı rapor oluşturuldu: {budget_id}")
        return JSONResponse(content=report_data)
        
    except ValueError as e:
        logger.warning(f"Rapor oluşturmada validasyon hatası: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Detaylı rapor oluşturulurken hata: {e}")
        raise HTTPException(status_code=500, detail="Rapor oluşturulamadı")

# POST - Varyans raporu oluştur
@router.post("/budget/{budget_id}/variance")
async def generate_variance_report(
    budget_id: UUID,
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Bütçe için varyans raporu oluştur (JSON)
    
    **Rapor İçeriği:**
    - Yalnızca %10 ve üzeri varyansa sahip satırlar
    - Favorable (artı) vs Unfavorable (eksi) varyans
    - Varyans yüzdesi ve tutarları
    """
    try:
        logger.info(f"{current_user.username} varyans raporu oluşturuyor: {budget_id}")
        
        report_data = ReportService.generate_variance_report(db, budget_id)
        
        logger.info(f"Varyans raporu oluşturuldu: {budget_id}")
        return JSONResponse(content=report_data)
        
    except ValueError as e:
        logger.warning(f"Rapor oluşturmada validasyon hatası: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Varyans raporu oluşturulurken hata: {e}")
        raise HTTPException(status_code=500, detail="Rapor oluşturulamadı")
