"""
Companies API Endpoints - JWT Korumalı
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from uuid import UUID
from app.db.session import get_db
from app.models.company import Company
from app.dependencies import get_current_user
from app.services.company_service import CompanyService
from app.schemas.company import CompanyCreate, CompanyUpdate, CompanyResponse
from app.schemas.user import UserResponse
import logging

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/companies",
    tags=["Companies"],
    responses={404: {"description": "Not found"}},
)

# GET - Şirketleri listele (korumalı)
@router.get("", response_model=dict)
async def list_companies(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Şirketleri listele (JWT Token gerekli)
    
    Header: Authorization: Bearer <token>
    """
    try:
        logger.info(f"Şirketler listeleniyor: {current_user.username}")
        query = db.query(Company).order_by(Company.created_date.desc())
        total = query.count()
        companies = query.offset(skip).limit(limit).all()
        return {
            "data": [CompanyResponse.model_validate(c) for c in companies],
            "total": total,
            "skip": skip,
            "limit": limit
        }
    except Exception as e:
        logger.error(f"Şirketleri listelerken hata: {e}")
        raise HTTPException(status_code=500, detail="Şirketleri listelemek başarısız")

# GET - Şirket detayı (korumalı)
@router.get("/{company_id}", response_model=CompanyResponse)
async def get_company(
    company_id: UUID,
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Şirket detayını getir (JWT Token gerekli)
    
    Header: Authorization: Bearer <token>
    """
    try:
        logger.info(f"{current_user.username} şirket detayını görüntülüyor: {company_id}")
        company = CompanyService.get_company(db, company_id)
        if not company:
            raise HTTPException(status_code=404, detail=f"Şirket bulunamadı: {company_id}")
        return company
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Şirket detayı getirilirken hata: {e}")
        raise HTTPException(status_code=500, detail="Şirket detayı getirilemedi")

# POST - Yeni şirket oluştur (korumalı)
@router.post("", response_model=CompanyResponse, status_code=201)
async def create_company(
    company_in: CompanyCreate,
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Yeni şirket oluştur (JWT Token gerekli)
    
    Header: Authorization: Bearer <token>
    """
    try:
        logger.info(f"{current_user.username} yeni şirket oluşturuyor: {company_in.name}")
        return CompanyService.create_company(db, company_in)
    except ValueError as e:
        logger.warning(f"Şirket oluşturmada validasyon hatası: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Şirket oluşturulurken hata: {e}")
        raise HTTPException(status_code=500, detail="Şirket oluşturulamadı")

# PUT - Şirket güncelle (korumalı)
@router.put("/{company_id}", response_model=CompanyResponse)
async def update_company(
    company_id: UUID,
    company_in: CompanyUpdate,
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Şirket güncelle (JWT Token gerekli)
    
    Header: Authorization: Bearer <token>
    """
    try:
        logger.info(f"{current_user.username} şirketi güncelliyor: {company_id}")
        company = CompanyService.update_company(db, company_id, company_in)
        if not company:
            raise HTTPException(status_code=404, detail=f"Şirket bulunamadı: {company_id}")
        return company
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Şirket güncellenirken hata: {e}")
        raise HTTPException(status_code=500, detail="Şirket güncellenemedi")

# DELETE - Şirket sil (korumalı)
@router.delete("/{company_id}", status_code=204)
async def delete_company(
    company_id: UUID,
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Şirket sil (JWT Token gerekli)
    
    Header: Authorization: Bearer <token>
    """
    try:
        logger.info(f"{current_user.username} şirketi siliyor: {company_id}")
        success = CompanyService.delete_company(db, company_id)
        if not success:
            raise HTTPException(status_code=404, detail=f"Şirket bulunamadı: {company_id}")
        return None
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Şirket silinirken hata: {e}")
        raise HTTPException(status_code=500, detail="Şirket silinemedi")

# GET - Şirket sayısı (korumalı)
@router.get("/stats/count", response_model=dict)
async def get_company_count(
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Toplam şirket sayısını getir (JWT Token gerekli)
    
    Header: Authorization: Bearer <token>
    """
    try:
        logger.info(f"{current_user.username} şirket sayısını sorguluyor")
        count = CompanyService.count(db)
        return {"total_companies": count}
    except Exception as e:
        logger.error(f"Şirket sayısı getirilirken hata: {e}")
        raise HTTPException(status_code=500, detail="Şirket sayısı getirilemedi")
