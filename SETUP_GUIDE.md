# 🚀 Kurumsal Bütçe Sistemi - Kurulum ve Çalıştırma Rehberi

## 📋 Adım Adım Kurulum (Windows)

### **ADIM 1: Dosyaları İndirdiğin Klasöre Koy**

Şu dosyaları `budget-system` klasörüne kopyala:
```
budget-system/
├── docker-compose.yml
├── .env
├── requirements.txt
├── main.py
├── config.py
├── base.py
└── session.py
```

### **ADIM 2: Klasör Yapısını Oluştur**

PowerShell'de şu komutları çalıştır:

```powershell
cd budget-system

# Klasörleri oluştur
mkdir app
mkdir app\db
mkdir app\api
mkdir app\api\v1
mkdir tests
```

### **ADIM 3: Dosyaları Doğru Yerlere Koy**

```
budget-system/
├── docker-compose.yml          ← Kök klasör
├── .env                         ← Kök klasör
├── requirements.txt             ← Kök klasör
├── main.py                      ← app/ klasörüne taşı
├── config.py                    ← app/ klasörüne taşı
├── base.py                      ← app/db/ klasörüne taşı
└── session.py                   ← app/db/ klasörüne taşı
```

PowerShell'de:
```powershell
# app/ klasörüne __init__.py ekle
New-Item app\__init__.py
New-Item app\db\__init__.py
New-Item app\api\__init__.py
New-Item app\api\v1\__init__.py
```

### **ADIM 4: Python Virtual Environment Kur**

```powershell
# Virtual environment oluştur
python -m venv venv

# Aktivate et
venv\Scripts\activate

# Paketleri kur
pip install -r requirements.txt
```

### **ADIM 5: Docker'ı Başlat**

```powershell
# PostgreSQL ve Redis'i Docker'da çalıştır
docker-compose up -d
```

**Kontrol Et:**
- PostgreSQL: http://localhost:5432
- Redis: localhost:6379
- pgAdmin: http://localhost:5050
  - Email: admin@budgetsystem.local
  - Password: admin123

### **ADIM 6: FastAPI Uygulamasını Çalıştır**

```powershell
# Venv aktivasyon kontrol et (başında (venv) olmalı)
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Başarılı ise şunu göreceksin:**
```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Application startup complete
```

### **ADIM 7: Test Et**

Tarayıcıda aç:

1. **Health Check**: http://localhost:8000/health
   - Cevap: `{"status": "healthy", ...}`

2. **API Docs**: http://localhost:8000/api/docs
   - Swagger UI ile API'yi test edebilirsin

3. **pgAdmin**: http://localhost:5050
   - PostgreSQL veritabanını yönet

---

## 🐳 Docker Komutları

```powershell
# Servisleri başlat
docker-compose up -d

# Servislerin durumunu kontrol et
docker-compose ps

# Logs'ları görmek için
docker-compose logs -f postgres   # PostgreSQL logs
docker-compose logs -f redis      # Redis logs

# Servisleri durdur
docker-compose down

# Veriyi sil ve baştan başla
docker-compose down -v
```

---

## 📊 PostgreSQL Bağlantısı

**pgAdmin arayüzü ile:**
1. http://localhost:5050 aç
2. Login: admin@budgetsystem.local / admin123
3. "Add New Server" tıkla
4. Bilgiler:
   - Host: postgres
   - Port: 5432
   - Username: budgetuser
   - Password: budgetpass123
   - Database: budget_system

**Terminal ile (psql):**
```powershell
# Docker container'a gir
docker exec -it budget_postgres psql -U budgetuser -d budget_system

# İçinde çalıştır:
\dt                    # Tabloları listele
\l                     # Veritabanlarını listele
SELECT version();      # PostgreSQL versiyon
```

---

## ⚠️ Sık Karşılaşılan Sorunlar

### ❌ "Connection refused"
**Çözüm**: Docker servisleri başlatılmış mı?
```powershell
docker-compose ps
# Hepsi "Up" durumunda olmalı
```

### ❌ "Port already in use"
**Çözüm**: Başka bir uygulama kullanıyor
```powershell
# Portu değiştir docker-compose.yml'de
# 5432:5432 → 5433:5432 gibi
```

### ❌ "Module not found"
**Çözüm**: Virtual environment aktif değil
```powershell
venv\Scripts\activate
# Başında (venv) olmalı
```

### ❌ "Pydantic validation error"
**Çözüm**: .env dosyasında tüm değişkenler var mı?
```powershell
# .env dosyasını kontrol et
cat .env
```

---

## 🎯 Sonraki Adımlar

Tüm sistem çalışıyorsa:

1. **Database Migrasyonları**: Alembic ile schema oluştur
2. **Company Management API**: İlk endpoint'i yazalım
3. **Master Data API**: Products, Customers, Periods
4. **Authentication**: JWT login sistemi
5. **Budget CRUD**: Bütçe yönetim API'leri

---

## 📝 Kullanışlı Komutlar

```powershell
# Venv'yi aktivate et
venv\Scripts\activate

# Paket ekle
pip install package_name

# Paket listesini güncelle
pip freeze > requirements.txt

# FastAPI'yi başlat (otomatik reload)
uvicorn app.main:app --reload

# FastAPI'yi başlat (belirli port)
uvicorn app.main:app --port 8001 --reload

# Docker logs'unu izle
docker-compose logs -f

# Docker'ı tamamen temizle
docker-compose down -v

# Test çalıştır
pytest

# Kod formatı düzenle
black app/

# Linting kontrol
flake8 app/
```

---

## ✅ Başarılı Kurulum Kontrol Listesi

- [ ] Docker yüklü ve çalışıyor
- [ ] PowerShell'de `docker --version` başarılı
- [ ] Proje klasörü oluşturuldu
- [ ] Dosyalar doğru yerlerde
- [ ] Virtual environment oluşturuldu
- [ ] `pip install -r requirements.txt` başarılı
- [ ] `docker-compose up -d` başarılı
- [ ] `docker-compose ps` tüm servisleri "Up" gösteriyor
- [ ] `uvicorn app.main:app --reload` başarılı
- [ ] http://localhost:8000/health başarılı cevap veriyor
- [ ] http://localhost:8000/api/docs Swagger UI açılıyor
- [ ] http://localhost:5050 pgAdmin açılıyor

**Hepsi başarılı? 🎉 Artık geliştirmeye başlayabiliriz!**

