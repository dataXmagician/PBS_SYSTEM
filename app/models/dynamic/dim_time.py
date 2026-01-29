"""
Dim Time Model - Tarih Boyutu

Sistem tarafından yönetilen tarih boyutu.
Bütçe/Forecast girişlerinde kullanılır.
"""

from sqlalchemy import Column, Integer, String, Date, Boolean
from app.db.base import BaseModel


class DimTime(BaseModel):
    """
    Tarih boyutu.
    
    Örnek:
        - date_key: 20250101
        - full_date: 2025-01-01
        - year: 2025
        - month: 1
        - month_name: "Ocak"
    """
    __tablename__ = "dim_time"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Tarih anahtarı (YYYYMMDD formatında)
    date_key = Column(Integer, unique=True, nullable=False, index=True)
    
    # Tam tarih
    full_date = Column(Date, unique=True, nullable=False)
    
    # Yıl
    year = Column(Integer, nullable=False, index=True)
    
    # Çeyrek (1-4)
    quarter = Column(Integer, nullable=False)
    
    # Ay (1-12)
    month = Column(Integer, nullable=False, index=True)
    
    # Ay adı
    month_name = Column(String(20), nullable=False)
    month_name_short = Column(String(3), nullable=False)  # Oca, Şub...
    
    # Hafta numarası (1-53)
    week = Column(Integer, nullable=False)
    
    # Gün (1-31)
    day = Column(Integer, nullable=False)
    
    # Haftanın günü (1-7, Pazartesi=1)
    day_of_week = Column(Integer, nullable=False)
    day_name = Column(String(20), nullable=False)
    
    # Yılın günü (1-366)
    day_of_year = Column(Integer, nullable=False)
    
    # Hafta sonu mu?
    is_weekend = Column(Boolean, default=False)
    
    # Ay sonu mu?
    is_month_end = Column(Boolean, default=False)
    
    # Çeyrek sonu mu?
    is_quarter_end = Column(Boolean, default=False)
    
    # Yıl sonu mu?
    is_year_end = Column(Boolean, default=False)
    
    # Fiskal yıl (şirketlere göre değişebilir)
    fiscal_year = Column(Integer, nullable=True)
    fiscal_quarter = Column(Integer, nullable=True)
    fiscal_month = Column(Integer, nullable=True)
    
    def __repr__(self):
        return f"<DimTime(date='{self.full_date}')>"
