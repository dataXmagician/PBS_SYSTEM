"""
Customer API Endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc
from uuid import UUID
from app.dependencies import get_current_user
from app.schemas.user import UserResponse  # ← EKLE
from app.db.session import get_db
from app.services.customer_service import CustomerService
from app.schemas.customer import CustomerCreate, CustomerUpdate, CustomerResponse
from app.models.customer import Customer
import logging

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/customers",
    tags=["Customers"],
    responses={404: {"description": "Not found"}},
)

# GET - Müşterileri listele (company_id opsiyonel)
@router.get("", response_model=dict)
async def list_customers(
    company_id: UUID = Query(None, description="Şirket ID (opsiyonel)"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    active_only: bool = Query(False),
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Müşterileri listele
    - company_id verilirse: O şirkete ait müşteriler
    - company_id yoksa: Tüm müşteriler
    """
    try:
        if company_id:
            return CustomerService.get_customers_by_company(db, company_id, skip, limit, active_only)
        else:
            # Tüm müşterileri getir
            query = db.query(Customer).order_by(desc(Customer.created_date))
            if active_only:
                query = query.filter(Customer.is_active == True)
            total = query.count()
            customers = query.offset(skip).limit(limit).all()
            logger.info(f"Müşteriler listelendi: {len(customers)} / {total}")
            return {
                "data": [CustomerResponse.model_validate(c) for c in customers],
                "total": total,
                "skip": skip,
                "limit": limit
            }
    except Exception as e:
        logger.error(f"Müşterileri listelerken hata: {e}")
        raise HTTPException(status_code=500, detail="Müşterileri listelemek başarısız")

# GET - Müşteri detayı
@router.get("/{customer_id}", response_model=CustomerResponse)
async def get_customer(
    customer_id: UUID,
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Müşteri detayını getir
    """
    try:
        customer = CustomerService.get_customer(db, customer_id)
        if not customer:
            raise HTTPException(status_code=404, detail=f"Müşteri bulunamadı: {customer_id}")
        return customer
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Müşteri detayı getirilirken hata: {e}")
        raise HTTPException(status_code=500, detail="Müşteri detayı getirilemedi")

# POST - Yeni müşteri oluştur
@router.post("", response_model=CustomerResponse, status_code=201)
async def create_customer(
    customer_in: CustomerCreate,
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Yeni müşteri oluştur
    """
    try:
        return CustomerService.create_customer(db, customer_in)
    except ValueError as e:
        logger.warning(f"Müşteri oluşturmada validasyon hatası: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Müşteri oluşturulurken hata: {e}")
        raise HTTPException(status_code=500, detail="Müşteri oluşturulamadı")

# PUT - Müşteri güncelle
@router.put("/{customer_id}", response_model=CustomerResponse)
async def update_customer(
    customer_id: UUID,
    customer_in: CustomerUpdate,
    db: Session = Depends(get_db)
,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Müşteri güncelle
    """
    try:
        customer = CustomerService.update_customer(db, customer_id, customer_in)
        if not customer:
            raise HTTPException(status_code=404, detail=f"Müşteri bulunamadı: {customer_id}")
        return customer
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Müşteri güncellenirken hata: {e}")
        raise HTTPException(status_code=500, detail="Müşteri güncellenemedi")

# DELETE - Müşteri sil
@router.delete("/{customer_id}", status_code=204)
async def delete_customer(
    customer_id: UUID,
    db: Session = Depends(get_db)
,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Müşteri sil
    """
    try:
        success = CustomerService.delete_customer(db, customer_id)
        if not success:
            raise HTTPException(status_code=404, detail=f"Müşteri bulunamadı: {customer_id}")
        return None
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Müşteri silinirken hata: {e}")
        raise HTTPException(status_code=500, detail="Müşteri silinemedi")

# GET - Müşteri sayısı
@router.get("/stats/count", response_model=dict)
async def get_customer_count(
    company_id: UUID = Query(None, description="Şirket ID (opsiyonel)"),
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Müşteri sayısını getir
    - company_id verilirse: O şirkete ait müşteri sayısı
    - company_id yoksa: Toplam müşteri sayısı
    """
    try:
        if company_id:
            count = CustomerService.get_customer_count_by_company(db, company_id)
        else:
            count = db.query(Customer).count()
        return {"total_customers": count}
    except Exception as e:
        logger.error(f"Müşteri sayısı getirilirken hata: {e}")
        raise HTTPException(status_code=500, detail="Müşteri sayısı getirilemedi")
