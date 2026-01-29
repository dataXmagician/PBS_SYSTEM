"""
Customer Service - Business logic
"""

from sqlalchemy.orm import Session
from app.repositories.customer_repository import CustomerRepository
from app.schemas.customer import CustomerCreate, CustomerUpdate, CustomerResponse
from uuid import UUID
from typing import Optional
import logging

logger = logging.getLogger(__name__)

class CustomerService:
    """
    Customer için business logic
    """
    
    @staticmethod
    def create_customer(db: Session, customer_in: CustomerCreate) -> CustomerResponse:
        """
        Yeni müşteri oluştur
        """
        existing = CustomerRepository.get_by_sap_number(
            db, customer_in.company_id, customer_in.sap_customer_number
        )
        if existing:
            raise ValueError(f"Bu SAP Customer Number zaten mevcut: {customer_in.sap_customer_number}")
        
        logger.info(f"Yeni müşteri oluşturuluyor: {customer_in.name}")
        customer = CustomerRepository.create(db, customer_in)
        logger.info(f"Müşteri başarıyla oluşturuldu: {customer.id}")
        return CustomerResponse.model_validate(customer)
    
    @staticmethod
    def get_customer(db: Session, customer_id: UUID) -> Optional[CustomerResponse]:
        """
        Müşteri detayını getir
        """
        customer = CustomerRepository.get_by_id(db, customer_id)
        if not customer:
            logger.warning(f"Müşteri bulunamadı: {customer_id}")
            return None
        return CustomerResponse.model_validate(customer)
    
    @staticmethod
    def get_customers_by_company(
        db: Session, company_id: UUID, skip: int = 0, limit: int = 100, active_only: bool = False
    ) -> dict:
        """
        Şirkete ait müşterileri listele
        """
        if active_only:
            customers, total = CustomerRepository.get_active_by_company(db, company_id, skip, limit)
        else:
            customers, total = CustomerRepository.get_by_company(db, company_id, skip, limit)
        
        logger.info(f"Müşteriler listelendi: {len(customers)} / {total}")
        return {
            "data": [CustomerResponse.model_validate(c) for c in customers],
            "total": total,
            "skip": skip,
            "limit": limit
        }
    
    @staticmethod
    def update_customer(db: Session, customer_id: UUID, customer_in: CustomerUpdate) -> Optional[CustomerResponse]:
        """
        Müşteri güncelle
        """
        logger.info(f"Müşteri güncelleniyor: {customer_id}")
        customer = CustomerRepository.update(db, customer_id, customer_in)
        if not customer:
            logger.warning(f"Müşteri bulunamadı: {customer_id}")
            return None
        logger.info(f"Müşteri güncellendi: {customer_id}")
        return CustomerResponse.model_validate(customer)
    
    @staticmethod
    def delete_customer(db: Session, customer_id: UUID) -> bool:
        """
        Müşteri sil
        """
        logger.warning(f"Müşteri silinmeye çalışılıyor: {customer_id}")
        result = CustomerRepository.delete(db, customer_id)
        if result:
            logger.info(f"Müşteri silindi: {customer_id}")
        else:
            logger.warning(f"Silinecek müşteri bulunamadı: {customer_id}")
        return result
    
    @staticmethod
    def get_customer_count_by_company(db: Session, company_id: UUID) -> int:
        """
        Şirkete ait toplam müşteri sayısını getir
        """
        count = CustomerRepository.count_by_company(db, company_id)
        logger.info(f"Şirkete ait müşteri sayısı: {count}")
        return count
