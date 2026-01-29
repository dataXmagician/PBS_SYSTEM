"""
Budget Repository - Database CRUD işlemleri
"""

from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.budget import Budget
from app.models.budget_line import BudgetLine
from app.schemas.budget import BudgetCreate, BudgetUpdate, BudgetLineCreate, BudgetLineUpdate
from uuid import UUID
from typing import Optional, List

class BudgetRepository:
    """
    Budget modeli için database işlemleri
    """
    
    @staticmethod
    def create(db: Session, budget_in: BudgetCreate) -> Budget:
        """
        Yeni bütçe oluştur
        """
        db_budget = Budget(
            company_id=budget_in.company_id,
            fiscal_year=budget_in.fiscal_year,
            budget_version=budget_in.budget_version,
            description=budget_in.description,
            currency=budget_in.currency
        )
        db.add(db_budget)
        db.commit()
        db.refresh(db_budget)
        return db_budget
    
    @staticmethod
    def get_by_id(db: Session, budget_id: UUID) -> Optional[Budget]:
        """
        ID'ye göre bütçe getir
        """
        return db.query(Budget).filter(Budget.id == budget_id).first()
    
    @staticmethod
    def get_by_company_and_year(
        db: Session, company_id: UUID, fiscal_year: str
    ) -> Optional[Budget]:
        """
        Şirket ve mali yıla göre bütçe getir
        """
        return db.query(Budget).filter(
            Budget.company_id == company_id,
            Budget.fiscal_year == fiscal_year
        ).order_by(Budget.created_date.desc()).first()
    
    @staticmethod
    def get_by_company(db: Session, company_id: UUID, skip: int = 0, limit: int = 100) -> tuple[List[Budget], int]:
        """
        Şirkete ait bütçeleri listele
        """
        query = db.query(Budget).filter(Budget.company_id == company_id).order_by(Budget.created_date.desc())
        total = query.count()
        budgets = query.offset(skip).limit(limit).all()
        return budgets, total
    
    @staticmethod
    def update(db: Session, budget_id: UUID, budget_in: BudgetUpdate) -> Optional[Budget]:
        """
        Bütçe güncelle
        """
        db_budget = BudgetRepository.get_by_id(db, budget_id)
        if db_budget:
            if budget_in.description is not None:
                db_budget.description = budget_in.description
            if budget_in.status is not None:
                db_budget.status = budget_in.status
            db.commit()
            db.refresh(db_budget)
        return db_budget
    
    @staticmethod
    def delete(db: Session, budget_id: UUID) -> bool:
        """
        Bütçe sil
        """
        db_budget = BudgetRepository.get_by_id(db, budget_id)
        if db_budget:
            db.delete(db_budget)
            db.commit()
            return True
        return False
    
    @staticmethod
    def count_by_company(db: Session, company_id: UUID) -> int:
        """
        Şirkete ait toplam bütçe sayısını getir
        """
        return db.query(func.count(Budget.id)).filter(Budget.company_id == company_id).scalar()

class BudgetLineRepository:
    """
    BudgetLine modeli için database işlemleri
    """
    
    @staticmethod
    def create(db: Session, budget_line_in: BudgetLineCreate, budget_id: UUID) -> BudgetLine:
        """
        Yeni bütçe satırı oluştur
        """
        db_line = BudgetLine(
            budget_id=budget_id,
            period_id=budget_line_in.period_id,
            product_id=budget_line_in.product_id,
            customer_id=budget_line_in.customer_id,
            original_amount=budget_line_in.original_amount,
            revised_amount=budget_line_in.revised_amount,
            actual_amount=budget_line_in.actual_amount,
            forecast_amount=budget_line_in.forecast_amount,
            notes=budget_line_in.notes
        )
        db.add(db_line)
        db.commit()
        db.refresh(db_line)
        return db_line
    
    @staticmethod
    def get_by_id(db: Session, line_id: UUID) -> Optional[BudgetLine]:
        """
        ID'ye göre bütçe satırı getir
        """
        return db.query(BudgetLine).filter(BudgetLine.id == line_id).first()
    
    @staticmethod
    def get_by_budget(db: Session, budget_id: UUID, skip: int = 0, limit: int = 1000) -> tuple[List[BudgetLine], int]:
        """
        Bütçeye ait satırları listele
        """
        query = db.query(BudgetLine).filter(BudgetLine.budget_id == budget_id)
        total = query.count()
        lines = query.offset(skip).limit(limit).all()
        return lines, total
    
    @staticmethod
    def update(db: Session, line_id: UUID, line_in: BudgetLineUpdate) -> Optional[BudgetLine]:
        """
        Bütçe satırı güncelle
        """
        db_line = BudgetLineRepository.get_by_id(db, line_id)
        if db_line:
            if line_in.revised_amount is not None:
                db_line.revised_amount = line_in.revised_amount
            if line_in.actual_amount is not None:
                db_line.actual_amount = line_in.actual_amount
            if line_in.forecast_amount is not None:
                db_line.forecast_amount = line_in.forecast_amount
            if line_in.notes is not None:
                db_line.notes = line_in.notes
            if line_in.status is not None:
                db_line.status = line_in.status
            
            # Varyans hesapla
            db_line.variance = db_line.revised_amount - db_line.actual_amount
            if db_line.revised_amount != 0:
                db_line.variance_percent = (db_line.variance / db_line.revised_amount) * 100
            
            db.commit()
            db.refresh(db_line)
        return db_line
    
    @staticmethod
    def delete(db: Session, line_id: UUID) -> bool:
        """
        Bütçe satırı sil
        """
        db_line = BudgetLineRepository.get_by_id(db, line_id)
        if db_line:
            db.delete(db_line)
            db.commit()
            return True
        return False
    
    @staticmethod
    def bulk_create(db: Session, lines: List[BudgetLineCreate], budget_id: UUID) -> List[BudgetLine]:
        """
        Toplu bütçe satırı oluştur (Excel import için)
        """
        db_lines = [
            BudgetLine(
                budget_id=budget_id,
                period_id=line.period_id,
                product_id=line.product_id,
                customer_id=line.customer_id,
                original_amount=line.original_amount,
                revised_amount=line.revised_amount,
                actual_amount=line.actual_amount,
                forecast_amount=line.forecast_amount,
                notes=line.notes
            )
            for line in lines
        ]
        db.add_all(db_lines)
        db.commit()
        return db_lines
    
    @staticmethod
    def count_by_budget(db: Session, budget_id: UUID) -> int:
        """
        Bütçedeki satır sayısını getir
        """
        return db.query(func.count(BudgetLine.id)).filter(BudgetLine.budget_id == budget_id).scalar()
