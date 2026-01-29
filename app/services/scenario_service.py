"""
Scenario Service - Senaryo analizi hesaplama
"""

from sqlalchemy.orm import Session
from app.models.budget import Budget
from app.models.budget_line import BudgetLine
from uuid import UUID
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)

class ScenarioService:
    """
    Senaryo analizi servisi
    """
    
    @staticmethod
    def create_scenario(
        db: Session,
        budget_id: UUID,
        scenario_name: str,
        adjustment_percentage: float,
        username: str
    ) -> dict:
        """
        Senaryo oluştur ve hesapla
        """
        logger.info(f"Senaryo oluşturuluyor: {budget_id}, {scenario_name}, {adjustment_percentage}%")
        
        # Bütçeyi getir
        budget = db.query(Budget).filter(Budget.id == budget_id).first()
        if not budget:
            raise ValueError(f"Bütçe bulunamadı: {budget_id}")
        
        # Bütçe satırlarını getir
        lines = db.query(BudgetLine).filter(BudgetLine.budget_id == budget_id).all()
        
        # Orijinal toplam
        original_total = sum(Decimal(line.revised_amount) for line in lines) if lines else Decimal(0)
        
        # Yeni senaryo tutarı
        adjustment = Decimal(str(adjustment_percentage))
        scenario_total = original_total * (1 + (adjustment / 100))
        impact = scenario_total - original_total
        impact_pct = (adjustment) if original_total != 0 else Decimal(0)
        
        scenario_data = {
            "scenario_name": scenario_name,
            "scenario_type": "CUSTOM",
            "adjustment_percentage": float(adjustment),
            "original_total": float(original_total),
            "scenario_total": float(scenario_total),
            "impact": float(impact),
            "impact_percentage": float(impact_pct),
            "line_count": len(lines),
            "description": f"{scenario_name}: %{adjustment} ayarlama"
        }
        
        # Senaryo satırlarını oluştur
        scenario_lines = []
        for line in lines:
            adjusted_amount = Decimal(line.revised_amount) * (1 + (adjustment / 100))
            scenario_lines.append({
                "period_id": str(line.period_id),
                "original": float(line.revised_amount),
                "adjusted": float(adjusted_amount),
                "difference": float(adjusted_amount - Decimal(line.revised_amount))
            })
        
        scenario_data["lines"] = scenario_lines
        
        logger.info(f"Senaryo oluşturuldu: {scenario_name}, etki: {impact}")
        return scenario_data
    
    @staticmethod
    def compare_scenarios(db: Session, budget_id: UUID) -> dict:
        """
        Base, Optimistic, Pessimistic senaryoları karşılaştır
        """
        logger.info(f"Senaryolar karşılaştırılıyor: {budget_id}")
        
        # Base senaryo (0%)
        base = ScenarioService.create_scenario(db, budget_id, "Base Case", 0, "system")
        
        # Optimistic (20% artış)
        optimistic = ScenarioService.create_scenario(db, budget_id, "Optimistic", 20, "system")
        
        # Pessimistic (20% azalış)
        pessimistic = ScenarioService.create_scenario(db, budget_id, "Pessimistic", -20, "system")
        
        comparison = {
            "budget_id": str(budget_id),
            "comparison": {
                "base": {
                    "name": "Base Case",
                    "total": base["scenario_total"],
                    "adjustment": 0
                },
                "optimistic": {
                    "name": "Optimistic (+20%)",
                    "total": optimistic["scenario_total"],
                    "adjustment": 20,
                    "upside": optimistic["impact"]
                },
                "pessimistic": {
                    "name": "Pessimistic (-20%)",
                    "total": pessimistic["scenario_total"],
                    "adjustment": -20,
                    "downside": pessimistic["impact"]
                }
            },
            "range": {
                "minimum": pessimistic["scenario_total"],
                "base": base["scenario_total"],
                "maximum": optimistic["scenario_total"],
                "spread": optimistic["impact"] - pessimistic["impact"]
            }
        }
        
        logger.info(f"Senaryolar karşılaştırıldı, spread: {comparison['range']['spread']}")
        return comparison
    
    @staticmethod
    def analyze_sensitivity(db: Session, budget_id: UUID, variable: str) -> dict:
        """
        Hassasiyet analizi (değişkenlere göre etki)
        """
        logger.info(f"Hassasiyet analizi: {budget_id}, variable: {variable}")
        
        # %10, %20, %30 değişimlerin etkisini göster
        changes = [-30, -20, -10, 0, 10, 20, 30]
        results = []
        
        for change in changes:
            scenario = ScenarioService.create_scenario(db, budget_id, f"{change}% Change", change, "system")
            results.append({
                "change_percent": change,
                "total_amount": scenario["scenario_total"],
                "impact": scenario["impact"]
            })
        
        sensitivity = {
            "budget_id": str(budget_id),
            "variable": variable,
            "analysis": results
        }
        
        logger.info(f"Hassasiyet analizi tamamlandı")
        return sensitivity
