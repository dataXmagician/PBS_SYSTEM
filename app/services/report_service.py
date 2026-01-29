"""
Report Service - Rapor oluşturma (PDF/Excel)
"""

from sqlalchemy.orm import Session
from app.models.budget import Budget
from app.models.budget_line import BudgetLine
from uuid import UUID
from decimal import Decimal
import json
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class ReportService:
    """
    Rapor oluşturma servisi
    """
    
    @staticmethod
    def generate_summary_report(db: Session, budget_id: UUID) -> dict:
        """
        Özet rapor oluştur
        """
        logger.info(f"Özet rapor oluşturuluyor: {budget_id}")
        
        # Bütçeyi getir
        budget = db.query(Budget).filter(Budget.id == budget_id).first()
        if not budget:
            raise ValueError(f"Bütçe bulunamadı: {budget_id}")
        
        # Bütçe satırlarını getir
        lines = db.query(BudgetLine).filter(BudgetLine.budget_id == budget_id).all()
        
        # Hesaplamalar
        total_original = sum(Decimal(line.original_amount) for line in lines) if lines else Decimal(0)
        total_revised = sum(Decimal(line.revised_amount) for line in lines) if lines else Decimal(0)
        total_actual = sum(Decimal(line.actual_amount) for line in lines) if lines else Decimal(0)
        total_forecast = sum(Decimal(line.forecast_amount) for line in lines) if lines else Decimal(0)
        
        # Varyans
        total_variance = total_revised - total_actual
        variance_percent = (total_variance / total_revised * 100) if total_revised != 0 else Decimal(0)
        
        report_data = {
            "title": f"Bütçe Özet Raporu - {budget.fiscal_year}",
            "budget_id": str(budget_id),
            "fiscal_year": budget.fiscal_year,
            "version": budget.budget_version,
            "generated_at": datetime.utcnow().isoformat(),
            "summary": {
                "total_original": float(total_original),
                "total_revised": float(total_revised),
                "total_actual": float(total_actual),
                "total_forecast": float(total_forecast),
                "total_variance": float(total_variance),
                "variance_percent": float(variance_percent),
                "line_count": len(lines)
            },
            "status": budget.status,
            "currency": budget.currency
        }
        
        logger.info(f"Özet rapor oluşturuldu: {budget_id}")
        return report_data
    
    @staticmethod
    def generate_detailed_report(db: Session, budget_id: UUID) -> dict:
        """
        Detaylı rapor oluştur
        """
        logger.info(f"Detaylı rapor oluşturuluyor: {budget_id}")
        
        # Bütçeyi getir
        budget = db.query(Budget).filter(Budget.id == budget_id).first()
        if not budget:
            raise ValueError(f"Bütçe bulunamadı: {budget_id}")
        
        # Bütçe satırlarını getir
        lines = db.query(BudgetLine).filter(BudgetLine.budget_id == budget_id).all()
        
        # Satırları dönüştür
        line_data = []
        for line in lines:
            variance = Decimal(line.revised_amount) - Decimal(line.actual_amount)
            variance_pct = (variance / Decimal(line.revised_amount) * 100) if Decimal(line.revised_amount) != 0 else Decimal(0)
            
            line_data.append({
                "period_id": str(line.period_id),
                "product_id": str(line.product_id) if line.product_id else None,
                "customer_id": str(line.customer_id) if line.customer_id else None,
                "original": float(line.original_amount),
                "revised": float(line.revised_amount),
                "actual": float(line.actual_amount),
                "forecast": float(line.forecast_amount),
                "variance": float(variance),
                "variance_percent": float(variance_pct)
            })
        
        report_data = {
            "title": f"Bütçe Detaylı Raporu - {budget.fiscal_year}",
            "budget_id": str(budget_id),
            "fiscal_year": budget.fiscal_year,
            "version": budget.budget_version,
            "generated_at": datetime.utcnow().isoformat(),
            "lines": line_data,
            "total_lines": len(line_data),
            "status": budget.status,
            "currency": budget.currency
        }
        
        logger.info(f"Detaylı rapor oluşturuldu: {budget_id}")
        return report_data
    
    @staticmethod
    def generate_variance_report(db: Session, budget_id: UUID) -> dict:
        """
        Varyans raporu oluştur
        """
        logger.info(f"Varyans raporu oluşturuluyor: {budget_id}")
        
        # Bütçeyi getir
        budget = db.query(Budget).filter(Budget.id == budget_id).first()
        if not budget:
            raise ValueError(f"Bütçe bulunamadı: {budget_id}")
        
        # Bütçe satırlarını getir ve varyansa göre filtrele
        lines = db.query(BudgetLine).filter(BudgetLine.budget_id == budget_id).all()
        
        # Varyansı hesapla ve filtrele (10% üzeri)
        variance_lines = []
        for line in lines:
            variance = Decimal(line.revised_amount) - Decimal(line.actual_amount)
            variance_pct = (variance / Decimal(line.revised_amount) * 100) if Decimal(line.revised_amount) != 0 else Decimal(0)
            
            if abs(variance_pct) >= 10:  # %10 ve üzeri varyans
                variance_lines.append({
                    "period_id": str(line.period_id),
                    "product_id": str(line.product_id) if line.product_id else None,
                    "customer_id": str(line.customer_id) if line.customer_id else None,
                    "revised": float(line.revised_amount),
                    "actual": float(line.actual_amount),
                    "variance": float(variance),
                    "variance_percent": float(variance_pct),
                    "status": "UNFAVORABLE" if variance < 0 else "FAVORABLE"
                })
        
        report_data = {
            "title": f"Bütçe Varyans Raporu - {budget.fiscal_year}",
            "budget_id": str(budget_id),
            "fiscal_year": budget.fiscal_year,
            "version": budget.budget_version,
            "generated_at": datetime.utcnow().isoformat(),
            "variance_threshold": 10,  # %10 üzeri
            "variance_lines": variance_lines,
            "variance_count": len(variance_lines),
            "status": budget.status,
            "currency": budget.currency
        }
        
        logger.info(f"Varyans raporu oluşturuldu: {budget_id}, {len(variance_lines)} satır")
        return report_data
