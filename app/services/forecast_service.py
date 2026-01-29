"""
Forecast Service - Tahmin hesaplama ve istatistik
"""

from sqlalchemy.orm import Session
from app.models.budget_line import BudgetLine
from app.models.period import Period
from app.schemas.forecast import ForecastRequest, ForecastResult
from uuid import UUID
from decimal import Decimal
from typing import List, Tuple
import json
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class ForecastService:
    """
    Tahmin hesaplama servisi
    """
    
    @staticmethod
    def calculate_moving_average_forecast(
        db: Session,
        budget_id: UUID,
        target_period_id: UUID,
        product_id: UUID = None,
        customer_id: UUID = None,
        lookback_periods: int = 3
    ) -> ForecastResult:
        """
        Moving Average tahmin yöntemi
        """
        logger.info(f"Moving Average tahmini hesaplanıyor: budget={budget_id}, lookback={lookback_periods}")
        
        # Hedef dönemi getir
        target_period = db.query(Period).filter(Period.id == target_period_id).first()
        if not target_period:
            raise ValueError(f"Dönem bulunamadı: {target_period_id}")
        
        # Geçmiş dönemleri getir
        past_periods = db.query(Period).filter(
            Period.fiscal_year == target_period.fiscal_year - 1,
            Period.period <= target_period.period
        ).order_by(Period.period.desc()).limit(lookback_periods).all()
        
        # Eğer geçmiş yıl veri yoksa, aynı yılda geri ara
        if not past_periods or len(past_periods) < lookback_periods:
            past_periods = db.query(Period).filter(
                Period.fiscal_year == target_period.fiscal_year,
                Period.period < target_period.period
            ).order_by(Period.period.desc()).limit(lookback_periods).all()
        
        if not past_periods:
            logger.warning(f"Geçmiş veri bulunamadı: {budget_id}")
            raise ValueError("Tahmin için yeterli geçmiş veri bulunamadı")
        
        # Geçmiş döneme ait bütçe satırlarını getir
        data_points = []
        total = Decimal(0)
        
        for period in reversed(past_periods):
            query = db.query(BudgetLine).filter(
                BudgetLine.budget_id == budget_id,
                BudgetLine.period_id == period.id
            )
            
            if product_id:
                query = query.filter(BudgetLine.product_id == product_id)
            if customer_id:
                query = query.filter(BudgetLine.customer_id == customer_id)
            
            lines = query.all()
            amount = sum(line.revised_amount for line in lines) if lines else Decimal(0)
            total += amount
            data_points.append({
                "period": f"{period.fiscal_year}-{period.period:02d}",
                "amount": float(amount)
            })
        
        # Ortalama hesapla
        count = len(data_points)
        if count == 0:
            raise ValueError("Hesaplama için veri bulunamadı")
        
        base_amount = total / count
        
        # Trend hesapla (son 2 veri noktası)
        trend_percentage = Decimal(0)
        if count >= 2:
            oldest = Decimal(str(data_points[0]["amount"]))
            newest = Decimal(str(data_points[-1]["amount"]))
            if oldest != 0:
                trend_percentage = ((newest - oldest) / oldest) * 100
        
        # Tahmin = Ortalama + Trend
        forecast_amount = base_amount * (1 + (trend_percentage / 100))
        
        # Güven puanı (veri sayısına göre)
        # Daha fazla veri = daha yüksek güven
        confidence_score = Decimal(min(count / 12, 1.0))  # Max 1.0
        
        # Confidence interval (%80) - yaklaşık ±0.842 * std
        # Basit versyon: ±20% of forecast
        margin = forecast_amount * Decimal("0.2")
        lower_bound = forecast_amount - margin
        upper_bound = forecast_amount + margin
        
        # Yorumu oluştur
        if trend_percentage > 5:
            interpretation = f"Artış eğilimi: {trend_percentage:.1f}%"
        elif trend_percentage < -5:
            interpretation = f"Azalış eğilimi: {trend_percentage:.1f}%"
        else:
            interpretation = "Sabit trend"
        
        logger.info(f"Tahmin hesaplandı: {forecast_amount}, güven: {confidence_score}")
        
        return ForecastResult(
            forecast_amount=forecast_amount,
            trend_percentage=trend_percentage,
            confidence_score=confidence_score,
            lower_bound=lower_bound,
            upper_bound=upper_bound,
            base_amount=base_amount,
            data_points=data_points,
            interpretation=interpretation
        )
    
    @staticmethod
    def save_forecast(
        db: Session,
        budget_id: UUID,
        target_period_id: UUID,
        forecast_result: ForecastResult,
        product_id: UUID = None,
        customer_id: UUID = None,
        method: str = "MOVING_AVERAGE",
        username: str = None
    ) -> dict:
        """
        Tahmini veritabanına kaydet
        """
        from app.models.forecast import Forecast
        
        logger.info(f"Tahmin kaydediliyor: {budget_id}")
        
        forecast = Forecast(
            budget_id=budget_id,
            period_id=target_period_id,
            product_id=product_id,
            customer_id=customer_id,
            forecast_method=method,
            base_amount=forecast_result.base_amount,
            forecast_amount=forecast_result.forecast_amount,
            trend_percentage=forecast_result.trend_percentage,
            confidence_score=forecast_result.confidence_score,
            lower_bound=forecast_result.lower_bound,
            upper_bound=forecast_result.upper_bound,
            data_points_used=json.dumps(forecast_result.data_points),
            notes=forecast_result.interpretation,
            created_by=username
        )
        
        db.add(forecast)
        db.commit()
        db.refresh(forecast)
        
        logger.info(f"Tahmin kaydedildi: {forecast.id}")
        
        return {
            "id": str(forecast.id),
            "forecast_amount": float(forecast.forecast_amount),
            "confidence_score": float(forecast.confidence_score),
            "message": "Tahmin başarıyla kaydedildi"
        }
