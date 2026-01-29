"""
Calculation Engine - Otomatik hesaplama motoru
"""

from decimal import Decimal
from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)

class CalculationEngine:
    """
    Kuralları satırlara uygulayan hesaplama motoru
    """
    
    @staticmethod
    def apply_percentage_rule(amount: Decimal, percentage: Decimal) -> Decimal:
        """
        Yüzde kuralı uygula
        """
        return amount * (1 + (percentage / 100))
    
    @staticmethod
    def apply_formula_rule(amount: Decimal, formula: str) -> Decimal:
        """
        Formül kuralı uygula
        Örn: "original_amount * 1.1" veya "original_amount + 10000"
        """
        try:
            # Güvenli eval (sadece math işlemleri)
            context = {
                'original_amount': amount,
                'Decimal': Decimal,
            }
            result = eval(formula, {"__builtins__": {}}, context)
            return Decimal(str(result))
        except Exception as e:
            logger.error(f"Formül hatasında: {formula} - {e}")
            raise ValueError(f"Formül hatası: {e}")
    
    @staticmethod
    def apply_threshold_rule(
        amount: Decimal, 
        threshold: Decimal, 
        percentage: Decimal
    ) -> Decimal:
        """
        Eşik kuralı uygula
        Eğer amount > threshold ise percentage uygula
        """
        if amount > threshold:
            return amount * (1 + (percentage / 100))
        return amount
    
    @staticmethod
    def apply_rules_to_line(
        line: Dict[str, Any], 
        rules: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Satıra tüm kuralları uygula
        """
        result = line.copy()
        original_amount = Decimal(str(line.get('original_amount', 0)))
        applied_rules = []
        
        for rule in rules:
            if not rule.get('is_active'):
                continue
            
            try:
                rule_type = rule.get('rule_type')
                
                if rule_type == 'PERCENTAGE':
                    percentage = Decimal(str(rule.get('percentage_value', 0)))
                    result['revised_amount'] = CalculationEngine.apply_percentage_rule(
                        original_amount, percentage
                    )
                    applied_rules.append(f"{rule['rule_name']} ({percentage}%)")
                
                elif rule_type == 'FORMULA':
                    formula = rule.get('action')
                    result['revised_amount'] = CalculationEngine.apply_formula_rule(
                        original_amount, formula
                    )
                    applied_rules.append(f"{rule['rule_name']}")
                
                elif rule_type == 'THRESHOLD':
                    threshold = Decimal(str(rule.get('threshold_amount', 0)))
                    percentage = Decimal(str(rule.get('percentage_value', 0)))
                    result['revised_amount'] = CalculationEngine.apply_threshold_rule(
                        original_amount, threshold, percentage
                    )
                    applied_rules.append(f"{rule['rule_name']} (>={threshold})")
            
            except Exception as e:
                logger.error(f"Kural uygulanırken hata: {rule['rule_name']} - {e}")
                continue
        
        result['applied_rules'] = applied_rules
        return result
    
    @staticmethod
    def apply_rules_to_bulk(
        lines: List[Dict[str, Any]], 
        rules: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Toplu satırlara kuralları uygula
        """
        results = []
        for line in lines:
            try:
                result = CalculationEngine.apply_rules_to_line(line, rules)
                results.append(result)
            except Exception as e:
                logger.error(f"Satır işlenirken hata: {line} - {e}")
                results.append({
                    **line,
                    'error': str(e)
                })
        
        return results
    
    @staticmethod
    def get_calculation_preview(
        amount: Decimal, 
        rules: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Hesaplama önizlemesi
        """
        original = Decimal(str(amount))
        
        # Kuralları uygula
        line = {'original_amount': original}
        processed = CalculationEngine.apply_rules_to_line(line, rules)
        
        revised = Decimal(str(processed.get('revised_amount', original)))
        difference = revised - original
        percentage_change = (difference / original * 100) if original != 0 else Decimal(0)
        
        return {
            'original_amount': float(original),
            'revised_amount': float(revised),
            'difference': float(difference),
            'percentage_change': float(percentage_change),
            'applied_rules': processed.get('applied_rules', [])
        }