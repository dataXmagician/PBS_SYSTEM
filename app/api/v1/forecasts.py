"""
Forecast API Endpoints - Tahmin hesaplama ve yönetimi
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from uuid import UUID
from app.db.session import get_db
from app.dependencies import get_current_user
from app.services.forecast_service import ForecastService
from app.schemas.forecast import ForecastRequest, ForecastResult, ForecastResponse
from app.schemas.user import UserResponse
import logging

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/forecasts",
    tags=["Forecasts"],
    responses={404: {"description": "Not found"}},
)

# POST - Tahmin hesapla
@router.post("/calculate", response_model=ForecastResult)
async def calculate_forecast(
    forecast_req: ForecastRequest,
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Bütçe tahmini hesapla
    
    **Parametreler:**
    - budget_id: Bütçe ID
    - period_id: Tahmin yapılacak dönem ID
    - product_id: Ürün ID (opsiyonel)
    - customer_id: Müşteri ID (opsiyonel)
    - method: Tahmin yöntemi (MOVING_AVERAGE)
    - lookback_periods: Kaç ay geri bakılacak (1-12, default: 3)
    """
    try:
        logger.info(f"{current_user.username} tahmin hesaplıyor: {forecast_req.budget_id}")
        
        # Tahmin hesapla
        forecast_result = ForecastService.calculate_moving_average_forecast(
            db=db,
            budget_id=forecast_req.budget_id,
            target_period_id=forecast_req.period_id,
            product_id=forecast_req.product_id,
            customer_id=forecast_req.customer_id,
            lookback_periods=forecast_req.lookback_periods
        )
        
        logger.info(f"Tahmin hesaplandı: {forecast_result.forecast_amount}")
        return forecast_result
        
    except ValueError as e:
        logger.warning(f"Tahmin validasyon hatası: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Tahmin hesaplanırken hata: {e}")
        raise HTTPException(status_code=500, detail="Tahmin hesaplanamadı")

# POST - Tahmin hesapla ve kaydet
@router.post("/calculate-and-save", response_model=dict)
async def calculate_and_save_forecast(
    forecast_req: ForecastRequest,
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Bütçe tahmini hesapla ve veritabanına kaydet
    
    **Parametreler:**
    - budget_id: Bütçe ID
    - period_id: Tahmin yapılacak dönem ID
    - product_id: Ürün ID (opsiyonel)
    - customer_id: Müşteri ID (opsiyonel)
    - method: Tahmin yöntemi (MOVING_AVERAGE)
    - lookback_periods: Kaç ay geri bakılacak (1-12, default: 3)
    """
    try:
        logger.info(f"{current_user.username} tahmin hesaplayıp kaydediyor: {forecast_req.budget_id}")
        
        # Tahmin hesapla
        forecast_result = ForecastService.calculate_moving_average_forecast(
            db=db,
            budget_id=forecast_req.budget_id,
            target_period_id=forecast_req.period_id,
            product_id=forecast_req.product_id,
            customer_id=forecast_req.customer_id,
            lookback_periods=forecast_req.lookback_periods
        )
        
        # Tahmini kaydet
        result = ForecastService.save_forecast(
            db=db,
            budget_id=forecast_req.budget_id,
            target_period_id=forecast_req.period_id,
            forecast_result=forecast_result,
            product_id=forecast_req.product_id,
            customer_id=forecast_req.customer_id,
            method=forecast_req.method,
            username=current_user.username
        )
        
        logger.info(f"Tahmin kaydedildi: {result['id']}")
        return {
            **result,
            "forecast_amount": float(forecast_result.forecast_amount),
            "trend_percentage": float(forecast_result.trend_percentage),
            "confidence_score": float(forecast_result.confidence_score),
            "interpretation": forecast_result.interpretation
        }
        
    except ValueError as e:
        logger.warning(f"Tahmin validasyon hatası: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Tahmin kaydedilirken hata: {e}")
        raise HTTPException(status_code=500, detail="Tahmin kaydedilemedi")

# GET - Tahmin detayı
@router.get("/{forecast_id}", response_model=ForecastResponse)
async def get_forecast(
    forecast_id: UUID,
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Tahmin detayını getir (JWT Token gerekli)
    """
    try:
        from app.models.forecast import Forecast
        
        logger.info(f"{current_user.username} tahmin detayını görüntülüyor: {forecast_id}")
        
        forecast = db.query(Forecast).filter(Forecast.id == forecast_id).first()
        if not forecast:
            raise HTTPException(status_code=404, detail=f"Tahmin bulunamadı: {forecast_id}")
        
        return ForecastResponse.model_validate(forecast)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Tahmin detayı getirilirken hata: {e}")
        raise HTTPException(status_code=500, detail="Tahmin detayı getirilemedi")

# GET - Bütçeye ait tahminleri listele
@router.get("/budget/{budget_id}", response_model=dict)
async def list_forecasts_by_budget(
    budget_id: UUID,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Bütçeye ait tahminleri listele (JWT Token gerekli)
    """
    try:
        from app.models.forecast import Forecast
        
        logger.info(f"{current_user.username} tahminleri listeleniyor: {budget_id}")
        
        query = db.query(Forecast).filter(Forecast.budget_id == budget_id)
        total = query.count()
        forecasts = query.offset(skip).limit(limit).all()
        
        return {
            "data": [ForecastResponse.model_validate(f) for f in forecasts],
            "total": total,
            "skip": skip,
            "limit": limit
        }
        
    except Exception as e:
        logger.error(f"Tahminleri listelerken hata: {e}")
        raise HTTPException(status_code=500, detail="Tahminleri listelemek başarısız")
