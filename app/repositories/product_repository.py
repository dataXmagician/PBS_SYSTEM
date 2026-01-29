"""
Product Repository - Database CRUD işlemleri
"""

from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.product import Product
from app.schemas.product import ProductCreate, ProductUpdate
from uuid import UUID
from typing import Optional, List

class ProductRepository:
    """
    Product modeli için database işlemleri
    """
    
    @staticmethod
    def create(db: Session, product_in: ProductCreate) -> Product:
        """
        Yeni ürün oluştur
        """
        db_product = Product(
            company_id=product_in.company_id,
            sap_material_number=product_in.sap_material_number,
            sap_material_code=product_in.sap_material_code,
            name=product_in.name,
            description=product_in.description,
            category=product_in.category,
            unit_of_measure=product_in.unit_of_measure
        )
        db.add(db_product)
        db.commit()
        db.refresh(db_product)
        return db_product
    
    @staticmethod
    def get_by_id(db: Session, product_id: UUID) -> Optional[Product]:
        """
        ID'ye göre ürün getir
        """
        return db.query(Product).filter(Product.id == product_id).first()
    
    @staticmethod
    def get_by_sap_number(db: Session, company_id: UUID, sap_material_number: str) -> Optional[Product]:
        """
        SAP Material Number'a göre ürün getir
        """
        return db.query(Product).filter(
            Product.company_id == company_id,
            Product.sap_material_number == sap_material_number
        ).first()
    
    @staticmethod
    def get_by_company(db: Session, company_id: UUID, skip: int = 0, limit: int = 100) -> tuple[List[Product], int]:
        """
        Şirkete ait ürünleri listele
        """
        query = db.query(Product).filter(Product.company_id == company_id)
        total = query.count()
        products = query.offset(skip).limit(limit).all()
        return products, total
    
    @staticmethod
    def get_active_by_company(db: Session, company_id: UUID, skip: int = 0, limit: int = 100) -> tuple[List[Product], int]:
        """
        Şirkete ait aktif ürünleri listele
        """
        query = db.query(Product).filter(
            Product.company_id == company_id,
            Product.is_active == True
        )
        total = query.count()
        products = query.offset(skip).limit(limit).all()
        return products, total
    
    @staticmethod
    def update(db: Session, product_id: UUID, product_in: ProductUpdate) -> Optional[Product]:
        """
        Ürün güncelle
        """
        db_product = ProductRepository.get_by_id(db, product_id)
        if db_product:
            if product_in.name is not None:
                db_product.name = product_in.name
            if product_in.description is not None:
                db_product.description = product_in.description
            if product_in.category is not None:
                db_product.category = product_in.category
            if product_in.unit_of_measure is not None:
                db_product.unit_of_measure = product_in.unit_of_measure
            if product_in.is_active is not None:
                db_product.is_active = product_in.is_active
            db.commit()
            db.refresh(db_product)
        return db_product
    
    @staticmethod
    def delete(db: Session, product_id: UUID) -> bool:
        """
        Ürün sil
        """
        db_product = ProductRepository.get_by_id(db, product_id)
        if db_product:
            db.delete(db_product)
            db.commit()
            return True
        return False
    
    @staticmethod
    def count_by_company(db: Session, company_id: UUID) -> int:
        """
        Şirkete ait toplam ürün sayısını getir
        """
        return db.query(func.count(Product.id)).filter(Product.company_id == company_id).scalar()
