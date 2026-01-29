"""
Company Repository - Database CRUD işlemleri
"""

from sqlalchemy.orm import Session
from sqlalchemy import select, func
from app.models.company import Company
from app.schemas.company import CompanyCreate, CompanyUpdate
from uuid import UUID
from typing import Optional, List

class CompanyRepository:
    """
    Company modeli için database işlemleri
    """
    
    @staticmethod
    def create(db: Session, company_in: CompanyCreate) -> Company:
        """
        Yeni şirket oluştur
        """
        db_company = Company(
            sap_company_code=company_in.sap_company_code,
            name=company_in.name,
            budget_detail_level=company_in.budget_detail_level
        )
        db.add(db_company)
        db.commit()
        db.refresh(db_company)
        return db_company
    
    @staticmethod
    def get_by_id(db: Session, company_id: UUID) -> Optional[Company]:
        """
        ID'ye göre şirket getir
        """
        return db.query(Company).filter(Company.id == company_id).first()
    
    @staticmethod
    def get_by_sap_code(db: Session, sap_company_code: str) -> Optional[Company]:
        """
        SAP şirket koduna göre şirket getir
        """
        return db.query(Company).filter(Company.sap_company_code == sap_company_code).first()
    
    @staticmethod
    def get_all(db: Session, skip: int = 0, limit: int = 100) -> tuple[List[Company], int]:
        """
        Tüm şirketleri listele (pagination ile)
        """
        query = db.query(Company)
        total = query.count()
        companies = query.offset(skip).limit(limit).all()
        return companies, total
    
    @staticmethod
    def get_active(db: Session, skip: int = 0, limit: int = 100) -> tuple[List[Company], int]:
        """
        Aktif şirketleri listele
        """
        query = db.query(Company).filter(Company.is_active == True)
        total = query.count()
        companies = query.offset(skip).limit(limit).all()
        return companies, total
    
    @staticmethod
    def update(db: Session, company_id: UUID, company_in: CompanyUpdate) -> Optional[Company]:
        """
        Şirket güncelle
        """
        db_company = CompanyRepository.get_by_id(db, company_id)
        if db_company:
            if company_in.name is not None:
                db_company.name = company_in.name
            if company_in.budget_detail_level is not None:
                db_company.budget_detail_level = company_in.budget_detail_level
            if company_in.is_active is not None:
                db_company.is_active = company_in.is_active
            db.commit()
            db.refresh(db_company)
        return db_company
    
    @staticmethod
    def delete(db: Session, company_id: UUID) -> bool:
        """
        Şirket sil
        """
        db_company = CompanyRepository.get_by_id(db, company_id)
        if db_company:
            db.delete(db_company)
            db.commit()
            return True
        return False
    
    @staticmethod
    def count(db: Session) -> int:
        """
        Toplam şirket sayısını getir
        """
        return db.query(func.count(Company.id)).scalar()
