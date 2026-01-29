"""
Scenario API Endpoints - Senaryo analizi
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from uuid import UUID
from app.db.session import get_db
from app.dependencies import get_current_user
from app.services.scenario_service import ScenarioService
from app.schemas.user import UserResponse
import logging

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/scenarios",
    tags=["Scenarios"],
    responses={404: {"description": "Not found"}},
)

# POST - Senaryo oluştur ve hesapla
@router.post("/budget/{budget_id}/create")
async def create_scenario(
    budget_id: UUID,
    scenario_name: str = Query(..., description="Senaryo Adı"),
    adjustment_percentage: float = Query(..., description="Ayarlama Yüzdesi (-100 to 100)"),
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Senaryo oluştur ve analiz et
    
    **Parametreler:**
    - adjustment_percentage: -100 ile 100 arasında yüzde
      - 0: Base case
      - 20: %20 artış (Optimistic)
      - -20: %20 azalış (Pessimistic)
    """
    try:
        logger.info(f"{current_user.username} senaryo oluşturuyor: {scenario_name}")
        
        scenario_data = ScenarioService.create_scenario(
            db, budget_id, scenario_name, adjustment_percentage, current_user.username
        )
        
        logger.info(f"Senaryo oluşturuldu: {scenario_name}")
        return JSONResponse(content=scenario_data)
        
    except ValueError as e:
        logger.warning(f"Senaryo oluşturmada hata: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Senaryo oluşturulurken hata: {e}")
        raise HTTPException(status_code=500, detail="Senaryo oluşturulamadı")

# GET - Senaryo karşılaştırması (Base vs Optimistic vs Pessimistic)
@router.get("/budget/{budget_id}/compare")
async def compare_scenarios(
    budget_id: UUID,
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Üç temel senaryo karşılaştır:
    - **Base Case**: 0% (ayarlama yok)
    - **Optimistic**: +20%
    - **Pessimistic**: -20%
    
    **Cevap:**
    - Toplam tutarlar
    - Upside/Downside tutarları
    - Minimum-Maximum aralığı
    """
    try:
        logger.info(f"{current_user.username} senaryoları karşılaştırıyor: {budget_id}")
        
        comparison = ScenarioService.compare_scenarios(db, budget_id)
        
        logger.info(f"Senaryolar karşılaştırıldı")
        return JSONResponse(content=comparison)
        
    except ValueError as e:
        logger.warning(f"Senaryo karşılaştırmasında hata: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Senaryo karşılaştırılırken hata: {e}")
        raise HTTPException(status_code=500, detail="Karşılaştırma yapılamadı")

# GET - Hassasiyet analizi
@router.get("/budget/{budget_id}/sensitivity")
async def analyze_sensitivity(
    budget_id: UUID,
    variable: str = Query("budget", description="Değişken (budget, product, customer)"),
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Hassasiyet analizi - Değişkenlere göre etki analizi
    
    **Çıktı:**
    - -30%, -20%, -10%, 0%, +10%, +20%, +30% değişimlerin etkisi
    - Her değişim için toplam tutar ve impact
    """
    try:
        logger.info(f"{current_user.username} hassasiyet analizi yapıyor: {budget_id}")
        
        sensitivity = ScenarioService.analyze_sensitivity(db, budget_id, variable)
        
        logger.info(f"Hassasiyet analizi tamamlandı")
        return JSONResponse(content=sensitivity)
        
    except ValueError as e:
        logger.warning(f"Hassasiyet analizi hatası: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Hassasiyet analizi sırasında hata: {e}")
        raise HTTPException(status_code=500, detail="Analiz yapılamadı")
