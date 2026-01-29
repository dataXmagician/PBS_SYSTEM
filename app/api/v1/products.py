"""
Product API Endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc
from uuid import UUID
from app.schemas.user import UserResponse 
from app.dependencies import get_current_user
from app.db.session import get_db
from app.services.product_service import ProductService
from app.schemas.product import ProductCreate, ProductUpdate, ProductResponse
from app.models.product import Product
import logging

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/products",
    tags=["Products"],
    responses={404: {"description": "Not found"}},
)

# GET - Ürünleri listele (company_id opsiyonel)
@router.get("", response_model=dict)
async def list_products(
    company_id: UUID = Query(None, description="Şirket ID (opsiyonel)"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    active_only: bool = Query(False),
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Ürünleri listele
    - company_id verilirse: O şirkete ait ürünler
    - company_id yoksa: Tüm ürünler
    """
    try:
        if company_id:
            return ProductService.get_products_by_company(db, company_id, skip, limit, active_only)
        else:
            # Tüm ürünleri getir
            query = db.query(Product).order_by(desc(Product.created_date))
            if active_only:
                query = query.filter(Product.is_active == True)
            total = query.count()
            products = query.offset(skip).limit(limit).all()
            logger.info(f"Ürünler listelendi: {len(products)} / {total}")
            return {
                "data": [ProductResponse.model_validate(p) for p in products],
                "total": total,
                "skip": skip,
                "limit": limit
            }
    except Exception as e:
        logger.error(f"Ürünleri listelerken hata: {e}")
        raise HTTPException(status_code=500, detail="Ürünleri listelemek başarısız")

# GET - Ürün detayı
@router.get("/{product_id}", response_model=ProductResponse)
async def get_product(
    product_id: UUID,
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Ürün detayını getir
    """
    try:
        product = ProductService.get_product(db, product_id)
        if not product:
            raise HTTPException(status_code=404, detail=f"Ürün bulunamadı: {product_id}")
        return product
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ürün detayı getirilirken hata: {e}")
        raise HTTPException(status_code=500, detail="Ürün detayı getirilemedi")

# POST - Yeni ürün oluştur
@router.post("", response_model=ProductResponse, status_code=201)
async def create_product(
    product_in: ProductCreate,
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Yeni ürün oluştur
    """
    try:
        return ProductService.create_product(db, product_in)
    except ValueError as e:
        logger.warning(f"Ürün oluşturmada validasyon hatası: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Ürün oluşturulurken hata: {e}")
        raise HTTPException(status_code=500, detail="Ürün oluşturulamadı")

# PUT - Ürün güncelle
@router.put("/{product_id}", response_model=ProductResponse)
async def update_product(
    product_id: UUID,
    product_in: ProductUpdate,
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Ürün güncelle
    """
    try:
        product = ProductService.update_product(db, product_id, product_in)
        if not product:
            raise HTTPException(status_code=404, detail=f"Ürün bulunamadı: {product_id}")
        return product
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ürün güncellenirken hata: {e}")
        raise HTTPException(status_code=500, detail="Ürün güncellenemedi")

# DELETE - Ürün sil
@router.delete("/{product_id}", status_code=204)
async def delete_product(
    product_id: UUID,
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Ürün sil
    """
    try:
        success = ProductService.delete_product(db, product_id)
        if not success:
            raise HTTPException(status_code=404, detail=f"Ürün bulunamadı: {product_id}")
        return None
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ürün silinirken hata: {e}")
        raise HTTPException(status_code=500, detail="Ürün silinemedi")

# GET - Ürün sayısı
@router.get("/stats/count", response_model=dict)
async def get_product_count(
    company_id: UUID = Query(None, description="Şirket ID (opsiyonel)"),
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Ürün sayısını getir
    - company_id verilirse: O şirkete ait ürün sayısı
    - company_id yoksa: Toplam ürün sayısı
    """
    try:
        if company_id:
            count = ProductService.get_product_count_by_company(db, company_id)
        else:
            count = db.query(Product).count()
        return {"total_products": count}
    except Exception as e:
        logger.error(f"Ürün sayısı getirilirken hata: {e}")
        raise HTTPException(status_code=500, detail="Ürün sayısı getirilemedi")
