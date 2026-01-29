"""
Period Repository - Database CRUD işlemleri
"""

from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.period import Period
from app.schemas.period import PeriodCreate, PeriodUpdate
from uuid import UUID
from typing import Optional, List

class PeriodRepository:
    """
    Period modeli için database işlemleri
    """
    
    @staticmethod
    def create(db: Session, period_in: PeriodCreate) -> Period:
        """
        Yeni dönem oluştur
        """
        db_period = Period(
            company_id=period_in.company_id,
            fiscal_year=period_in.fiscal_year,
            period=period_in.period,
            period_name=period_in.period_name,
            start_date=period_in.start_date,
            end_date=period_in.end_date
        )
        db.add(db_period)
        db.commit()
        db.refresh(db_period)
        return db_period
    
    @staticmethod
    def get_by_id(db: Session, period_id: UUID) -> Optional[Period]:
        """
        ID'ye göre dönem getir
        """
        return db.query(Period).filter(Period.id == period_id).first()
    
    @staticmethod
    def get_by_company_and_period(
        db: Session, company_id: UUID, fiscal_year: int, period: int
    ) -> Optional[Period]:
        """
        Şirket, mali yıl ve dönem numarasına göre dönem getir
        """
        return db.query(Period).filter(
            Period.company_id == company_id,
            Period.fiscal_year == fiscal_year,
            Period.period == period
        ).first()
    
    @staticmethod
    def get_by_company(db: Session, company_id: UUID, skip: int = 0, limit: int = 100) -> tuple[List[Period], int]:
        """
        Şirkete ait dönemleri listele
        """
        query = db.query(Period).filter(Period.company_id == company_id).order_by(Period.fiscal_year.desc(), Period.period.desc())
        total = query.count()
        periods = query.offset(skip).limit(limit).all()
        return periods, total
    
    @staticmethod
    def get_by_company_and_fiscal_year(
        db: Session, company_id: UUID, fiscal_year: int, skip: int = 0, limit: int = 100
    ) -> tuple[List[Period], int]:
        """
        Şirket ve mali yıla göre dönemleri listele
        """
        query = db.query(Period).filter(
            Period.company_id == company_id,
            Period.fiscal_year == fiscal_year
        ).order_by(Period.period)
        total = query.count()
        periods = query.offset(skip).limit(limit).all()
        return periods, total
    
    @staticmethod
    def update(db: Session, period_id: UUID, period_in: PeriodUpdate) -> Optional[Period]:
        """
        Dönem güncelle
        """
        db_period = PeriodRepository.get_by_id(db, period_id)
        if db_period:
            if period_in.period_name is not None:
                db_period.period_name = period_in.period_name
            if period_in.is_open is not None:
                db_period.is_open = period_in.is_open
            if period_in.is_locked is not None:
                db_period.is_locked = period_in.is_locked
            db.commit()
            db.refresh(db_period)
        return db_period
    
    @staticmethod
    def delete(db: Session, period_id: UUID) -> bool:
        """
        Dönem sil
        """
        db_period = PeriodRepository.get_by_id(db, period_id)
        if db_period:
            db.delete(db_period)
            db.commit()
            return True
        return False
    
    @staticmethod
    def count_by_company(db: Session, company_id: UUID) -> int:
        """
        Şirkete ait toplam dönem sayısını getir
        """
        return db.query(func.count(Period.id)).filter(Period.company_id == company_id).scalar()
