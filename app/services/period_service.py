"""
Period Service - Business logic
"""

from sqlalchemy.orm import Session
from app.repositories.period_repository import PeriodRepository
from app.schemas.period import PeriodCreate, PeriodUpdate, PeriodResponse
from uuid import UUID
from typing import Optional
import logging

logger = logging.getLogger(__name__)

class PeriodService:
    """
    Period için business logic
    """
    
    @staticmethod
    def create_period(db: Session, period_in: PeriodCreate) -> PeriodResponse:
        """
        Yeni dönem oluştur
        """
        existing = PeriodRepository.get_by_company_and_period(
            db, period_in.company_id, period_in.fiscal_year, period_in.period
        )
        if existing:
            raise ValueError(
                f"Bu dönem zaten mevcut: {period_in.fiscal_year} - Period {period_in.period}"
            )
        
        logger.info(f"Yeni dönem oluşturuluyor: {period_in.fiscal_year} - {period_in.period}")
        period = PeriodRepository.create(db, period_in)
        logger.info(f"Dönem başarıyla oluşturuldu: {period.id}")
        return PeriodResponse.model_validate(period)
    
    @staticmethod
    def get_period(db: Session, period_id: UUID) -> Optional[PeriodResponse]:
        """
        Dönem detayını getir
        """
        period = PeriodRepository.get_by_id(db, period_id)
        if not period:
            logger.warning(f"Dönem bulunamadı: {period_id}")
            return None
        return PeriodResponse.model_validate(period)
    
    @staticmethod
    def get_periods_by_company(
        db: Session, company_id: UUID, skip: int = 0, limit: int = 100
    ) -> dict:
        """
        Şirkete ait dönemleri listele
        """
        periods, total = PeriodRepository.get_by_company(db, company_id, skip, limit)
        logger.info(f"Dönemler listelendi: {len(periods)} / {total}")
        return {
            "data": [PeriodResponse.model_validate(p) for p in periods],
            "total": total,
            "skip": skip,
            "limit": limit
        }
    
    @staticmethod
    def get_periods_by_fiscal_year(
        db: Session, company_id: UUID, fiscal_year: int, skip: int = 0, limit: int = 100
    ) -> dict:
        """
        Mali yıla göre dönemleri listele
        """
        periods, total = PeriodRepository.get_by_company_and_fiscal_year(
            db, company_id, fiscal_year, skip, limit
        )
        logger.info(f"Dönemler listelendi: {len(periods)} / {total}")
        return {
            "data": [PeriodResponse.model_validate(p) for p in periods],
            "total": total,
            "fiscal_year": fiscal_year
        }
    
    @staticmethod
    def update_period(db: Session, period_id: UUID, period_in: PeriodUpdate) -> Optional[PeriodResponse]:
        """
        Dönem güncelle
        """
        logger.info(f"Dönem güncelleniyor: {period_id}")
        period = PeriodRepository.update(db, period_id, period_in)
        if not period:
            logger.warning(f"Dönem bulunamadı: {period_id}")
            return None
        logger.info(f"Dönem güncellendi: {period_id}")
        return PeriodResponse.model_validate(period)
    
    @staticmethod
    def delete_period(db: Session, period_id: UUID) -> bool:
        """
        Dönem sil
        """
        logger.warning(f"Dönem silinmeye çalışılıyor: {period_id}")
        result = PeriodRepository.delete(db, period_id)
        if result:
            logger.info(f"Dönem silindi: {period_id}")
        else:
            logger.warning(f"Silinecek dönem bulunamadı: {period_id}")
        return result
    
    @staticmethod
    def get_period_count_by_company(db: Session, company_id: UUID) -> int:
        """
        Şirkete ait toplam dönem sayısını getir
        """
        count = PeriodRepository.count_by_company(db, company_id)
        logger.info(f"Şirkete ait dönem sayısı: {count}")
        return count
