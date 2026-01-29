"""
Budget Service - Business logic
"""

from sqlalchemy.orm import Session
from app.repositories.budget_repository import BudgetRepository, BudgetLineRepository
from app.schemas.budget import (
    BudgetCreate, BudgetUpdate, BudgetResponse, BudgetDetailResponse,
    BudgetLineCreate, BudgetLineUpdate, BudgetLineResponse
)
from uuid import UUID
from typing import Optional, List
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)

class BudgetService:
    """
    Budget için business logic
    """
    
    @staticmethod
    def create_budget(db: Session, budget_in: BudgetCreate) -> BudgetResponse:
        """
        Yeni bütçe oluştur
        """
        existing = BudgetRepository.get_by_company_and_year(
            db, budget_in.company_id, budget_in.fiscal_year
        )
        if existing:
            raise ValueError(f"Bu mali yıl için bütçe zaten mevcut: {budget_in.fiscal_year}")
        
        logger.info(f"Yeni bütçe oluşturuluyor: {budget_in.fiscal_year}")
        budget = BudgetRepository.create(db, budget_in)
        logger.info(f"Bütçe başarıyla oluşturuldu: {budget.id}")
        return BudgetResponse.model_validate(budget)
    
    @staticmethod
    def get_budget(db: Session, budget_id: UUID) -> Optional[BudgetResponse]:
        """
        Bütçe detayını getir
        """
        budget = BudgetRepository.get_by_id(db, budget_id)
        if not budget:
            logger.warning(f"Bütçe bulunamadı: {budget_id}")
            return None
        return BudgetResponse.model_validate(budget)
    
    @staticmethod
    def get_budget_with_lines(db: Session, budget_id: UUID) -> Optional[BudgetDetailResponse]:
        """
        Bütçeyi satırları ile getir
        """
        budget = BudgetRepository.get_by_id(db, budget_id)
        if not budget:
            logger.warning(f"Bütçe bulunamadı: {budget_id}")
            return None
        return BudgetDetailResponse.model_validate(budget)
    
    @staticmethod
    def get_budgets_by_company(
        db: Session, company_id: UUID, skip: int = 0, limit: int = 100
    ) -> dict:
        """
        Şirkete ait bütçeleri listele
        """
        budgets, total = BudgetRepository.get_by_company(db, company_id, skip, limit)
        logger.info(f"Bütçeler listelendi: {len(budgets)} / {total}")
        return {
            "data": [BudgetResponse.model_validate(b) for b in budgets],
            "total": total,
            "skip": skip,
            "limit": limit
        }
    
    @staticmethod
    def update_budget(db: Session, budget_id: UUID, budget_in: BudgetUpdate) -> Optional[BudgetResponse]:
        """
        Bütçe güncelle
        """
        logger.info(f"Bütçe güncelleniyor: {budget_id}")
        budget = BudgetRepository.update(db, budget_id, budget_in)
        if not budget:
            logger.warning(f"Bütçe bulunamadı: {budget_id}")
            return None
        logger.info(f"Bütçe güncellendi: {budget_id}")
        return BudgetResponse.model_validate(budget)
    
    @staticmethod
    def delete_budget(db: Session, budget_id: UUID) -> bool:
        """
        Bütçe sil
        """
        logger.warning(f"Bütçe silinmeye çalışılıyor: {budget_id}")
        result = BudgetRepository.delete(db, budget_id)
        if result:
            logger.info(f"Bütçe silindi: {budget_id}")
        else:
            logger.warning(f"Silinecek bütçe bulunamadı: {budget_id}")
        return result

class BudgetLineService:
    """
    BudgetLine için business logic
    """
    
    @staticmethod
    def add_line(db: Session, budget_id: UUID, line_in: BudgetLineCreate) -> BudgetLineResponse:
        """
        Bütçeye satır ekle
        """
        budget = BudgetRepository.get_by_id(db, budget_id)
        if not budget:
            raise ValueError(f"Bütçe bulunamadı: {budget_id}")
        
        logger.info(f"Bütçeye satır ekleniyor: {budget_id}")
        line = BudgetLineRepository.create(db, line_in, budget_id)
        logger.info(f"Satır başarıyla eklendi: {line.id}")
        return BudgetLineResponse.model_validate(line)
    
    @staticmethod
    def get_line(db: Session, line_id: UUID) -> Optional[BudgetLineResponse]:
        """
        Bütçe satırını getir
        """
        line = BudgetLineRepository.get_by_id(db, line_id)
        if not line:
            logger.warning(f"Satır bulunamadı: {line_id}")
            return None
        return BudgetLineResponse.model_validate(line)
    
    @staticmethod
    def get_lines_by_budget(
        db: Session, budget_id: UUID, skip: int = 0, limit: int = 1000
    ) -> dict:
        """
        Bütçenin satırlarını listele
        """
        lines, total = BudgetLineRepository.get_by_budget(db, budget_id, skip, limit)
        logger.info(f"Satırlar listelendi: {len(lines)} / {total}")
        return {
            "data": [BudgetLineResponse.model_validate(l) for l in lines],
            "total": total,
            "skip": skip,
            "limit": limit
        }
    
    @staticmethod
    def update_line(db: Session, line_id: UUID, line_in: BudgetLineUpdate) -> Optional[BudgetLineResponse]:
        """
        Bütçe satırını güncelle
        """
        logger.info(f"Satır güncelleniyor: {line_id}")
        line = BudgetLineRepository.update(db, line_id, line_in)
        if not line:
            logger.warning(f"Satır bulunamadı: {line_id}")
            return None
        logger.info(f"Satır güncellendi: {line_id}")
        return BudgetLineResponse.model_validate(line)
    
    @staticmethod
    def delete_line(db: Session, line_id: UUID) -> bool:
        """
        Bütçe satırını sil
        """
        logger.warning(f"Satır silinmeye çalışılıyor: {line_id}")
        result = BudgetLineRepository.delete(db, line_id)
        if result:
            logger.info(f"Satır silindi: {line_id}")
        else:
            logger.warning(f"Silinecek satır bulunamadı: {line_id}")
        return result
    
    @staticmethod
    def bulk_add_lines(db: Session, budget_id: UUID, lines: List[BudgetLineCreate]) -> dict:
        """
        Toplu satır ekleme (Excel import için)
        """
        budget = BudgetRepository.get_by_id(db, budget_id)
        if not budget:
            raise ValueError(f"Bütçe bulunamadı: {budget_id}")
        
        logger.info(f"Toplu {len(lines)} satır ekleniyor: {budget_id}")
        created_lines = BudgetLineRepository.bulk_create(db, lines, budget_id)
        logger.info(f"{len(created_lines)} satır başarıyla eklendi")
        return {
            "created": len(created_lines),
            "lines": [BudgetLineResponse.model_validate(l) for l in created_lines]
        }
