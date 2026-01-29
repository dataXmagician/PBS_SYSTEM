"""
Rule API Endpoints - Hesaplama kuralları
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from uuid import UUID
from app.db.session import get_db
from app.dependencies import get_current_user
from app.schemas.user import UserResponse
from app.schemas.rule import RuleCreate, RuleUpdate, RuleResponse, BulkCalculationRequest
from app.services.calculation_engine import CalculationEngine
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/rules",
    tags=["Rules"],
    responses={404: {"description": "Not found"}},
)

# GET - Şirkete ait kuralları listele
@router.get("/company/{company_id}")
async def list_rules(
    company_id: UUID,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Şirkete ait hesaplama kurallarını listele
    """
    try:
        from app.models.rule import CalculationRule
        
        logger.info(f"{current_user.username} kuralları listeleniyor: {company_id}")
        
        query = db.query(CalculationRule).filter(
            CalculationRule.company_id == company_id
        )
        total = query.count()
        rules = query.offset(skip).limit(limit).all()
        
        return {
            "data": [RuleResponse.model_validate(r) for r in rules],
            "total": total
        }
    except Exception as e:
        logger.error(f"Kuralları listelerken hata: {e}")
        raise HTTPException(status_code=500, detail="Kurallar listelenemiyor")

# POST - Yeni kural oluştur
@router.post("/", response_model=RuleResponse)
async def create_rule(
    rule_data: RuleCreate,
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Yeni hesaplama kuralı oluştur
    """
    try:
        from app.models.rule import CalculationRule
        
        logger.info(f"{current_user.username} kural oluşturuyor: {rule_data.rule_name}")
        
        rule = CalculationRule(
            company_id=rule_data.company_id,
            rule_name=rule_data.rule_name,
            rule_type=rule_data.rule_type,
            description=rule_data.description,
            action=rule_data.action,
            percentage_value=rule_data.percentage_value,
            threshold_amount=rule_data.threshold_amount,
            is_active=rule_data.is_active,
            apply_automatically=rule_data.apply_automatically,
            requires_approval=rule_data.requires_approval,
            created_by=current_user.username
        )
        
        db.add(rule)
        db.commit()
        db.refresh(rule)
        
        logger.info(f"Kural oluşturuldu: {rule.id}")
        return RuleResponse.model_validate(rule)
    
    except Exception as e:
        logger.error(f"Kural oluşturulurken hata: {e}")
        raise HTTPException(status_code=500, detail="Kural oluşturulamadı")

# PUT - Kuralı güncelle
@router.put("/{rule_id}", response_model=RuleResponse)
async def update_rule(
    rule_id: UUID,
    rule_data: RuleUpdate,
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Hesaplama kuralını güncelle
    """
    try:
        from app.models.rule import CalculationRule
        
        logger.info(f"{current_user.username} kuralı güncelliyor: {rule_id}")
        
        rule = db.query(CalculationRule).filter(CalculationRule.id == rule_id).first()
        if not rule:
            raise HTTPException(status_code=404, detail="Kural bulunamadı")
        
        # Güncelle
        if rule_data.rule_name:
            rule.rule_name = rule_data.rule_name
        if rule_data.description is not None:
            rule.description = rule_data.description
        if rule_data.action:
            rule.action = rule_data.action
        if rule_data.percentage_value is not None:
            rule.percentage_value = rule_data.percentage_value
        if rule_data.is_active is not None:
            rule.is_active = rule_data.is_active
        
        db.commit()
        db.refresh(rule)
        
        logger.info(f"Kural güncellendi: {rule_id}")
        return RuleResponse.model_validate(rule)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Kural güncellenirken hata: {e}")
        raise HTTPException(status_code=500, detail="Kural güncellenemedi")

# DELETE - Kuralı sil
@router.delete("/{rule_id}")
async def delete_rule(
    rule_id: UUID,
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Hesaplama kuralını sil
    """
    try:
        from app.models.rule import CalculationRule
        
        logger.info(f"{current_user.username} kuralı siliyor: {rule_id}")
        
        rule = db.query(CalculationRule).filter(CalculationRule.id == rule_id).first()
        if not rule:
            raise HTTPException(status_code=404, detail="Kural bulunamadı")
        
        db.delete(rule)
        db.commit()
        
        logger.info(f"Kural silindi: {rule_id}")
        return {"message": "Kural başarıyla silindi"}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Kural silinirken hata: {e}")
        raise HTTPException(status_code=500, detail="Kural silinemedi")

# POST - Hesaplama önizlemesi
@router.post("/preview/calculate")
async def preview_calculation(
    amount: Decimal = Query(..., description="Orijinal tutar"),
    rule_ids: str = Query("", description="Kural ID'leri (virgülle ayrılmış)"),
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Kuralları uygulamadan önce önizleme yap
    """
    try:
        from app.models.rule import CalculationRule
        
        # Kuralları getir
        rules_list = []
        if rule_ids:
            rule_id_list = [UUID(rid.strip()) for rid in rule_ids.split(',')]
            rules = db.query(CalculationRule).filter(
                CalculationRule.id.in_(rule_id_list),
                CalculationRule.is_active == True
            ).all()
            rules_list = [
                {
                    'rule_name': r.rule_name,
                    'rule_type': r.rule_type,
                    'action': r.action,
                    'percentage_value': r.percentage_value,
                    'threshold_amount': r.threshold_amount,
                    'is_active': r.is_active
                }
                for r in rules
            ]
        
        # Önizleme
        preview = CalculationEngine.get_calculation_preview(amount, rules_list)
        
        logger.info(f"{current_user.username} hesaplama önizlemesi yaptı")
        return preview
    
    except Exception as e:
        logger.error(f"Önizleme hatası: {e}")
        raise HTTPException(status_code=500, detail="Önizleme yapılamadı")

# POST - Toplu hesaplama
@router.post("/bulk/calculate")
async def bulk_calculate(
    request: BulkCalculationRequest,
    company_id: UUID = Query(..., description="Şirket ID"),
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Toplu satırlara kuralları uygula
    """
    try:
        from app.models.rule import CalculationRule
        
        logger.info(f"{current_user.username} toplu hesaplama yapıyor")
        
        # Kuralları getir
        rules_query = db.query(CalculationRule).filter(
            CalculationRule.company_id == company_id,
            CalculationRule.is_active == True
        )
        
        if request.rule_ids:
            rules_query = rules_query.filter(CalculationRule.id.in_(request.rule_ids))
        
        rules = rules_query.all()
        rules_list = [
            {
                'rule_name': r.rule_name,
                'rule_type': r.rule_type,
                'action': r.action,
                'percentage_value': r.percentage_value,
                'threshold_amount': r.threshold_amount,
                'is_active': r.is_active
            }
            for r in rules
        ]
        
        # Kuralları uygula
        if request.apply_rules:
            results = CalculationEngine.apply_rules_to_bulk(request.lines, rules_list)
        else:
            results = request.lines
        
        success_count = len([r for r in results if 'error' not in r])
        error_count = len([r for r in results if 'error' in r])
        
        logger.info(f"Toplu hesaplama tamamlandı: {success_count} başarılı, {error_count} hata")
        
        return {
            "processed_count": len(results),
            "success_count": success_count,
            "error_count": error_count,
            "results": results
        }
    
    except Exception as e:
        logger.error(f"Toplu hesaplama hatası: {e}")
        raise HTTPException(status_code=500, detail="Toplu hesaplama yapılamadı")