"""
Budget API Endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc
from uuid import UUID
from app.schemas.user import UserResponse
from app.dependencies import get_current_user
from app.db.session import get_db
from app.services.budget_service import BudgetService, BudgetLineService
from app.schemas.budget import (
    BudgetCreate, BudgetUpdate, BudgetResponse, BudgetDetailResponse,
    BudgetLineCreate, BudgetLineUpdate, BudgetLineResponse
)
from app.models.budget import Budget
from typing import List
import logging

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/budgets",
    tags=["Budgets"],
    responses={404: {"description": "Not found"}},
)

# ==================== BUDGET ENDPOINTS ====================

# GET - Bütçeleri listele (company_id opsiyonel)
@router.get("", response_model=dict)
async def list_budgets(
    company_id: UUID = Query(None, description="Şirket ID (opsiyonel)"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Bütçeleri listele
    - company_id verilirse: O şirkete ait bütçeler
    - company_id yoksa: Tüm bütçeler
    """
    try:
        if company_id:
            return BudgetService.get_budgets_by_company(db, company_id, skip, limit)
        else:
            # Tüm bütçeleri getir
            query = db.query(Budget).order_by(desc(Budget.created_date))
            total = query.count()
            budgets = query.offset(skip).limit(limit).all()
            logger.info(f"Bütçeler listelendi: {len(budgets)} / {total}")
            return {
                "data": [BudgetResponse.model_validate(b) for b in budgets],
                "total": total,
                "skip": skip,
                "limit": limit
            }
    except Exception as e:
        logger.error(f"Bütçeleri listelerken hata: {e}")
        raise HTTPException(status_code=500, detail="Bütçeleri listelemek başarısız")

# GET - Bütçe detayı
@router.get("/{budget_id}", response_model=BudgetResponse)
async def get_budget(
    budget_id: UUID,
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Bütçe detayını getir
    """
    try:
        budget = BudgetService.get_budget(db, budget_id)
        if not budget:
            raise HTTPException(status_code=404, detail=f"Bütçe bulunamadı: {budget_id}")
        return budget
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Bütçe detayı getirilirken hata: {e}")
        raise HTTPException(status_code=500, detail="Bütçe detayı getirilemedi")

# GET - Bütçe (satırları ile)
@router.get("/{budget_id}/with-lines", response_model=BudgetDetailResponse)
async def get_budget_with_lines(
    budget_id: UUID,
    db: Session = Depends(get_db),
current_user: UserResponse = Depends(get_current_user)
):
    """
    Bütçeyi satırları ile getir
    """
    try:
        budget = BudgetService.get_budget_with_lines(db, budget_id)
        if not budget:
            raise HTTPException(status_code=404, detail=f"Bütçe bulunamadı: {budget_id}")
        return budget
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Bütçe detayı getirilirken hata: {e}")
        raise HTTPException(status_code=500, detail="Bütçe detayı getirilemedi")

# POST - Yeni bütçe oluştur
@router.post("", response_model=BudgetResponse, status_code=201)
async def create_budget(
    budget_in: BudgetCreate,
    db: Session = Depends(get_db),
current_user: UserResponse = Depends(get_current_user)
):
    """
    Yeni bütçe oluştur
    """
    try:
        return BudgetService.create_budget(db, budget_in)
    except ValueError as e:
        logger.warning(f"Bütçe oluşturmada validasyon hatası: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Bütçe oluşturulurken hata: {e}")
        raise HTTPException(status_code=500, detail="Bütçe oluşturulamadı")

# PUT - Bütçe güncelle
@router.put("/{budget_id}", response_model=BudgetResponse)
async def update_budget(
    budget_id: UUID,
    budget_in: BudgetUpdate,
    db: Session = Depends(get_db),
current_user: UserResponse = Depends(get_current_user)
):
    """
    Bütçe güncelle
    """
    try:
        budget = BudgetService.update_budget(db, budget_id, budget_in)
        if not budget:
            raise HTTPException(status_code=404, detail=f"Bütçe bulunamadı: {budget_id}")
        return budget
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Bütçe güncellenirken hata: {e}")
        raise HTTPException(status_code=500, detail="Bütçe güncellenemedi")

# DELETE - Bütçe sil
@router.delete("/{budget_id}", status_code=204)
async def delete_budget(
    budget_id: UUID,
    db: Session = Depends(get_db),
current_user: UserResponse = Depends(get_current_user)
):
    """
    Bütçe sil
    """
    try:
        success = BudgetService.delete_budget(db, budget_id)
        if not success:
            raise HTTPException(status_code=404, detail=f"Bütçe bulunamadı: {budget_id}")
        return None
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Bütçe silinirken hata: {e}")
        raise HTTPException(status_code=500, detail="Bütçe silinemedi")

# ==================== BUDGET LINE ENDPOINTS ====================

# GET - Bütçenin satırlarını listele
@router.get("/{budget_id}/lines", response_model=dict)
async def list_budget_lines(
    budget_id: UUID,
    skip: int = Query(0, ge=0),
    limit: int = Query(1000, ge=1, le=10000),
    db: Session = Depends(get_db),
current_user: UserResponse = Depends(get_current_user)
):
    """
    Bütçenin satırlarını listele
    """
    try:
        return BudgetLineService.get_lines_by_budget(db, budget_id, skip, limit)
    except Exception as e:
        logger.error(f"Satırları listelerken hata: {e}")
        raise HTTPException(status_code=500, detail="Satırları listelemek başarısız")

# GET - Bütçe satırı detayı
@router.get("/lines/{line_id}", response_model=BudgetLineResponse)
async def get_budget_line(
    line_id: UUID,
    db: Session = Depends(get_db),
current_user: UserResponse = Depends(get_current_user)
):
    """
    Bütçe satırını getir
    """
    try:
        line = BudgetLineService.get_line(db, line_id)
        if not line:
            raise HTTPException(status_code=404, detail=f"Satır bulunamadı: {line_id}")
        return line
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Satır getirilirken hata: {e}")
        raise HTTPException(status_code=500, detail="Satır getirilemedi")

# POST - Bütçeye satır ekle
@router.post("/{budget_id}/lines", response_model=BudgetLineResponse, status_code=201)
async def add_budget_line(
    budget_id: UUID,
    line_in: BudgetLineCreate,
    db: Session = Depends(get_db),
current_user: UserResponse = Depends(get_current_user)
):
    """
    Bütçeye satır ekle
    """
    try:
        return BudgetLineService.add_line(db, budget_id, line_in)
    except ValueError as e:
        logger.warning(f"Satır eklenmede validasyon hatası: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Satır eklenirken hata: {e}")
        raise HTTPException(status_code=500, detail="Satır eklenemedi")

# POST - Toplu satır ekleme (Excel import)
@router.post("/{budget_id}/lines/bulk", response_model=dict, status_code=201)
async def bulk_add_budget_lines(
    budget_id: UUID,
    lines: List[BudgetLineCreate],
    db: Session = Depends(get_db),
current_user: UserResponse = Depends(get_current_user)
):
    """
    Toplu bütçe satırı ekleme (Excel import için)
    """
    try:
        return BudgetLineService.bulk_add_lines(db, budget_id, lines)
    except ValueError as e:
        logger.warning(f"Toplu ekleme validasyon hatası: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Toplu ekleme sırasında hata: {e}")
        raise HTTPException(status_code=500, detail="Toplu ekleme başarısız")

# PUT - Bütçe satırı güncelle
@router.put("/lines/{line_id}", response_model=BudgetLineResponse)
async def update_budget_line(
    line_id: UUID,
    line_in: BudgetLineUpdate,
    db: Session = Depends(get_db),
current_user: UserResponse = Depends(get_current_user)
):
    """
    Bütçe satırını güncelle
    """
    try:
        line = BudgetLineService.update_line(db, line_id, line_in)
        if not line:
            raise HTTPException(status_code=404, detail=f"Satır bulunamadı: {line_id}")
        return line
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Satır güncellenirken hata: {e}")
        raise HTTPException(status_code=500, detail="Satır güncellenemedi")

# DELETE - Bütçe satırı sil
@router.delete("/lines/{line_id}", status_code=204)
async def delete_budget_line(
    line_id: UUID,
    db: Session = Depends(get_db),
current_user: UserResponse = Depends(get_current_user)
):
    """
    Bütçe satırını sil
    """
    try:
        success = BudgetLineService.delete_line(db, line_id)
        if not success:
            raise HTTPException(status_code=404, detail=f"Satır bulunamadı: {line_id}")
        return None
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Satır silinirken hata: {e}")
        raise HTTPException(status_code=500, detail="Satır silinemedi")
