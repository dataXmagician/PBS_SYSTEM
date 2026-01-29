"""
Customer Repository - Database CRUD işlemleri
"""

from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.customer import Customer
from app.schemas.customer import CustomerCreate, CustomerUpdate
from uuid import UUID
from typing import Optional, List

class CustomerRepository:
    """
    Customer modeli için database işlemleri
    """
    
    @staticmethod
    def create(db: Session, customer_in: CustomerCreate) -> Customer:
        """
        Yeni müşteri oluştur
        """
        db_customer = Customer(
            company_id=customer_in.company_id,
            sap_customer_number=customer_in.sap_customer_number,
            sap_customer_code=customer_in.sap_customer_code,
            name=customer_in.name,
            customer_group=customer_in.customer_group,
            sales_organization=customer_in.sales_organization,
            distribution_channel=customer_in.distribution_channel,
            division=customer_in.division
        )
        db.add(db_customer)
        db.commit()
        db.refresh(db_customer)
        return db_customer
    
    @staticmethod
    def get_by_id(db: Session, customer_id: UUID) -> Optional[Customer]:
        """
        ID'ye göre müşteri getir
        """
        return db.query(Customer).filter(Customer.id == customer_id).first()
    
    @staticmethod
    def get_by_sap_number(db: Session, company_id: UUID, sap_customer_number: str) -> Optional[Customer]:
        """
        SAP Customer Number'a göre müşteri getir
        """
        return db.query(Customer).filter(
            Customer.company_id == company_id,
            Customer.sap_customer_number == sap_customer_number
        ).first()
    
    @staticmethod
    def get_by_company(db: Session, company_id: UUID, skip: int = 0, limit: int = 100) -> tuple[List[Customer], int]:
        """
        Şirkete ait müşterileri listele
        """
        query = db.query(Customer).filter(Customer.company_id == company_id)
        total = query.count()
        customers = query.offset(skip).limit(limit).all()
        return customers, total
    
    @staticmethod
    def get_active_by_company(db: Session, company_id: UUID, skip: int = 0, limit: int = 100) -> tuple[List[Customer], int]:
        """
        Şirkete ait aktif müşterileri listele
        """
        query = db.query(Customer).filter(
            Customer.company_id == company_id,
            Customer.is_active == True
        )
        total = query.count()
        customers = query.offset(skip).limit(limit).all()
        return customers, total
    
    @staticmethod
    def update(db: Session, customer_id: UUID, customer_in: CustomerUpdate) -> Optional[Customer]:
        """
        Müşteri güncelle
        """
        db_customer = CustomerRepository.get_by_id(db, customer_id)
        if db_customer:
            if customer_in.name is not None:
                db_customer.name = customer_in.name
            if customer_in.customer_group is not None:
                db_customer.customer_group = customer_in.customer_group
            if customer_in.is_active is not None:
                db_customer.is_active = customer_in.is_active
            db.commit()
            db.refresh(db_customer)
        return db_customer
    
    @staticmethod
    def delete(db: Session, customer_id: UUID) -> bool:
        """
        Müşteri sil
        """
        db_customer = CustomerRepository.get_by_id(db, customer_id)
        if db_customer:
            db.delete(db_customer)
            db.commit()
            return True
        return False
    
    @staticmethod
    def count_by_company(db: Session, company_id: UUID) -> int:
        """
        Şirkete ait toplam müşteri sayısını getir
        """
        return db.query(func.count(Customer.id)).filter(Customer.company_id == company_id).scalar()
