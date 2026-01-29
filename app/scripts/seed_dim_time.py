"""
Tarih boyutunu doldur (2020-2035 arası)
Kullanım: python -m app.scripts.seed_dim_time
"""

from datetime import date, timedelta
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.models.dynamic.dim_time import DimTime

TURKISH_MONTHS = {
    1: ("Ocak", "Oca"),
    2: ("Şubat", "Şub"),
    3: ("Mart", "Mar"),
    4: ("Nisan", "Nis"),
    5: ("Mayıs", "May"),
    6: ("Haziran", "Haz"),
    7: ("Temmuz", "Tem"),
    8: ("Ağustos", "Ağu"),
    9: ("Eylül", "Eyl"),
    10: ("Ekim", "Eki"),
    11: ("Kasım", "Kas"),
    12: ("Aralık", "Ara")
}

TURKISH_DAYS = {
    0: "Pazartesi",
    1: "Salı",
    2: "Çarşamba",
    3: "Perşembe",
    4: "Cuma",
    5: "Cumartesi",
    6: "Pazar"
}


def seed_dim_time(start_year: int = 2020, end_year: int = 2035):
    """Tarih boyutunu doldur"""
    db: Session = SessionLocal()
    
    try:
        # Mevcut kayıtları kontrol et
        existing = db.query(DimTime).count()
        if existing > 0:
            print(f"⚠️  dim_time tablosunda {existing} kayıt var. Atlanıyor...")
            return
        
        start_date = date(start_year, 1, 1)
        end_date = date(end_year, 12, 31)
        
        current = start_date
        records = []
        
        while current <= end_date:
            month_name, month_short = TURKISH_MONTHS[current.month]
            day_name = TURKISH_DAYS[current.weekday()]
            
            # Ay/Çeyrek/Yıl sonu kontrolleri
            next_day = current + timedelta(days=1)
            is_month_end = next_day.month != current.month
            is_quarter_end = is_month_end and current.month in [3, 6, 9, 12]
            is_year_end = current.month == 12 and current.day == 31
            
            record = DimTime(
                date_key=int(current.strftime("%Y%m%d")),
                full_date=current,
                year=current.year,
                quarter=(current.month - 1) // 3 + 1,
                month=current.month,
                month_name=month_name,
                month_name_short=month_short,
                week=current.isocalendar()[1],
                day=current.day,
                day_of_week=current.weekday() + 1,  # 1-7 (Pazartesi=1)
                day_name=day_name,
                day_of_year=current.timetuple().tm_yday,
                is_weekend=current.weekday() >= 5,
                is_month_end=is_month_end,
                is_quarter_end=is_quarter_end,
                is_year_end=is_year_end,
                fiscal_year=current.year,
                fiscal_quarter=(current.month - 1) // 3 + 1,
                fiscal_month=current.month
            )
            records.append(record)
            current += timedelta(days=1)
        
        # Toplu ekleme
        db.bulk_save_objects(records)
        db.commit()
        
        print(f"✅ {len(records)} tarih kaydı eklendi ({start_year}-{end_year})")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Hata: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_dim_time()
