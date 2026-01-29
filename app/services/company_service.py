"""
Company Service - Business logic
"""

from sqlalchemy.orm import Session
from app.repositories.company_repository import CompanyRepository
from app.schemas.company import CompanyCreate, CompanyUpdate, CompanyResponse
from app.models.company import Company
from uuid import UUID
from typing import Optional, List
import logging

logger = logging.getLogger(__name__)

class CompanyService:
    """
    Company için business logic
    """
    
    @staticmethod
    def create_company(db: Session, company_in: CompanyCreate) -> CompanyResponse:
        """
        Yeni şirket oluştur
        """
        # SAP kodu zaten var mı kontrol et
        existing = CompanyRepository.get_by_sap_code(db, company_in.sap_company_code)
        if existing:
            raise ValueError(f"SAP Şirket Kodu '{company_in.sap_company_code}' zaten mevcut")
        
        logger.info(f"Yeni şirket oluşturuluyor: {company_in.name} ({company_in.sap_company_code})")
        company = CompanyRepository.create(db, company_in)
        logger.info(f"Şirket başarıyla oluşturuldu: {company.id}")
        return CompanyResponse.model_validate(company)
    
    @staticmethod
    def get_company(db: Session, company_id: UUID) -> Optional[CompanyResponse]:
        """
        Şirket detayını getir
        """
        company = CompanyRepository.get_by_id(db, company_id)
        if not company:
            logger.warning(f"Şirket bulunamadı: {company_id}")
            return None
        return CompanyResponse.model_validate(company)
    
    @staticmethod
    def get_all_companies(db: Session, skip: int = 0, limit: int = 100) -> dict:
        """
        Tüm şirketleri listele
        """
        companies, total = CompanyRepository.get_all(db, skip, limit)
        logger.info(f"Şirketler listelendi: {len(companies)} / {total}")
        return {
            "data": [CompanyResponse.model_validate(c) for c in companies],
            "total": total,
            "skip": skip,
            "limit": limit
        }
    
    @staticmethod
    def get_active_companies(db: Session, skip: int = 0, limit: int = 100) -> dict:
        """
        Aktif şirketleri listele
        """
        companies, total = CompanyRepository.get_active(db, skip, limit)
        logger.info(f"Aktif şirketler listelendi: {len(companies)} / {total}")
        return {
            "data": [CompanyResponse.model_validate(c) for c in companies],
            "total": total
        }
    
    @staticmethod
    def update_company(db: Session, company_id: UUID, company_in: CompanyUpdate) -> Optional[CompanyResponse]:
        """
        Şirket güncelle
        """
        logger.info(f"Şirket güncelleniyor: {company_id}")
        company = CompanyRepository.update(db, company_id, company_in)
        if not company:
            logger.warning(f"Şirket bulunamadı: {company_id}")
            return None
        logger.info(f"Şirket güncellendi: {company_id}")
        return CompanyResponse.model_validate(company)
    
    @staticmethod
    def delete_company(db: Session, company_id: UUID) -> bool:
        """
        Şirket sil
        """
        logger.warning(f"Şirket silinmeye çalışılıyor: {company_id}")
        result = CompanyRepository.delete(db, company_id)
        if result:
            logger.info(f"Şirket silindi: {company_id}")
        else:
            logger.warning(f"Silinecek şirket bulunamadı: {company_id}")
        return result
    
    @staticmethod
    def get_company_count(db: Session) -> int:
        """
        Toplam şirket sayısını getir
        """
        count = CompanyRepository.count(db)
        logger.info(f"Toplam şirket sayısı: {count}")
        return count
