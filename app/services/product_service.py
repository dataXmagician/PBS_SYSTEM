"""
Product Service - Business logic
"""

from sqlalchemy.orm import Session
from app.repositories.product_repository import ProductRepository
from app.schemas.product import ProductCreate, ProductUpdate, ProductResponse
from uuid import UUID
from typing import Optional, List
import logging

logger = logging.getLogger(__name__)

class ProductService:
    """
    Product için business logic
    """
    
    @staticmethod
    def create_product(db: Session, product_in: ProductCreate) -> ProductResponse:
        """
        Yeni ürün oluştur
        """
        # Aynı ürün zaten var mı kontrol et
        existing = ProductRepository.get_by_sap_number(
            db, product_in.company_id, product_in.sap_material_number
        )
        if existing:
            raise ValueError(f"Bu SAP Material Number zaten mevcut: {product_in.sap_material_number}")
        
        logger.info(f"Yeni ürün oluşturuluyor: {product_in.name}")
        product = ProductRepository.create(db, product_in)
        logger.info(f"Ürün başarıyla oluşturuldu: {product.id}")
        return ProductResponse.model_validate(product)
    
    @staticmethod
    def get_product(db: Session, product_id: UUID) -> Optional[ProductResponse]:
        """
        Ürün detayını getir
        """
        product = ProductRepository.get_by_id(db, product_id)
        if not product:
            logger.warning(f"Ürün bulunamadı: {product_id}")
            return None
        return ProductResponse.model_validate(product)
    
    @staticmethod
    def get_products_by_company(
        db: Session, company_id: UUID, skip: int = 0, limit: int = 100, active_only: bool = False
    ) -> dict:
        """
        Şirkete ait ürünleri listele
        """
        if active_only:
            products, total = ProductRepository.get_active_by_company(db, company_id, skip, limit)
        else:
            products, total = ProductRepository.get_by_company(db, company_id, skip, limit)
        
        logger.info(f"Ürünler listelendi: {len(products)} / {total}")
        return {
            "data": [ProductResponse.model_validate(p) for p in products],
            "total": total,
            "skip": skip,
            "limit": limit
        }
    
    @staticmethod
    def update_product(db: Session, product_id: UUID, product_in: ProductUpdate) -> Optional[ProductResponse]:
        """
        Ürün güncelle
        """
        logger.info(f"Ürün güncelleniyor: {product_id}")
        product = ProductRepository.update(db, product_id, product_in)
        if not product:
            logger.warning(f"Ürün bulunamadı: {product_id}")
            return None
        logger.info(f"Ürün güncellendi: {product_id}")
        return ProductResponse.model_validate(product)
    
    @staticmethod
    def delete_product(db: Session, product_id: UUID) -> bool:
        """
        Ürün sil
        """
        logger.warning(f"Ürün silinmeye çalışılıyor: {product_id}")
        result = ProductRepository.delete(db, product_id)
        if result:
            logger.info(f"Ürün silindi: {product_id}")
        else:
            logger.warning(f"Silinecek ürün bulunamadı: {product_id}")
        return result
    
    @staticmethod
    def get_product_count_by_company(db: Session, company_id: UUID) -> int:
        """
        Şirkete ait toplam ürün sayısını getir
        """
        count = ProductRepository.count_by_company(db, company_id)
        logger.info(f"Şirkete ait ürün sayısı: {count}")
        return count
