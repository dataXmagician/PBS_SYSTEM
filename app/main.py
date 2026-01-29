"""
Kurumsal Bütçe Sistemi - FastAPI Main Application
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.openapi.utils import get_openapi
import logging
from app.config import settings
from app.api.v1 import rules
# API Routes
from app.api.v1 import companies, products, customers, periods, budgets, forecasts, reports,scenarios
from app.api import auth
from app.api.v1 import reports
from app.api.v1 import scenarios

# Logger setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPI app initialization
app = FastAPI(
    title=settings.API_TITLE,
    description=settings.API_DESCRIPTION,
    version=settings.API_VERSION,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json"
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/api/v1")
app.include_router(companies.router, prefix="/api/v1")
app.include_router(products.router, prefix="/api/v1")
app.include_router(customers.router, prefix="/api/v1")
app.include_router(periods.router, prefix="/api/v1")
app.include_router(budgets.router, prefix="/api/v1")
app.include_router(forecasts.router, prefix="/api/v1")
app.include_router(reports.router, prefix="/api/v1")
app.include_router(scenarios.router, prefix="/api/v1")
app.include_router(rules.router, prefix="/api/v1")

# Health Check Endpoint
@app.get("/health", tags=["Health"])
async def health_check():
    """
    Uygulamanın durumunu kontrol et
    """
    return {
        "status": "healthy",
        "service": "Budget System API",
        "version": settings.API_VERSION
    }

# Root Endpoint
@app.get("/", tags=["Root"])
async def root():
    """
    Root endpoint - API bilgileri
    """
    return {
        "message": "Kurumsal Bütçe Sistemi API'ye Hoşgeldiniz",
        "version": settings.API_VERSION,
        "docs": "/api/docs",
        "health": "/health",
        "auth": {
            "register": "/api/v1/auth/register",
            "login": "/api/v1/auth/login",
            "me": "/api/v1/auth/me"
        }
    }

# Error Handlers
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """
    Global exception handler
    """
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": "Bir hata oluştu. Lütfen daha sonra tekrar deneyin."
            }
        }
    )

@app.get("/api/v1/", tags=["API Info"])
async def api_info():
    """
    API v1 bilgileri
    """
    return {
        "version": "v1",
        "endpoints": {
            "health": "/health",
            "auth": {
                "register": "/api/v1/auth/register",
                "login": "/api/v1/auth/login",
                "me": "/api/v1/auth/me",
                "verify": "/api/v1/auth/verify-token"
            },
            "companies": "/api/v1/companies",
            "products": "/api/v1/products",
            "customers": "/api/v1/customers",
            "periods": "/api/v1/periods",
            "budgets": "/api/v1/budgets",
            "docs": "/api/docs"
        }
    }

# Custom OpenAPI schema with security
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title=settings.API_TITLE,
        version=settings.API_VERSION,
        description=settings.API_DESCRIPTION,
        routes=app.routes,
    )
    
    # Add security schemes
    openapi_schema["components"]["securitySchemes"] = {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
            "description": "JWT Token (Login'den aldığın access_token)"
        }
    }
    
    # Mark protected endpoints
    protected_paths = [
        "/api/v1/companies",
        "/api/v1/products",
        "/api/v1/customers",
        "/api/v1/periods",
        "/api/v1/budgets",
    ]
    
    for path, methods in openapi_schema.get("paths", {}).items():
        # Skip auth endpoints
        if "/auth/" in path:
            continue
        
        # Add security to protected endpoints
        for method, details in methods.items():
            if method in ["get", "post", "put", "delete"]:
                if "security" not in details:
                    details["security"] = [{"BearerAuth": []}]
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi

# Startup Event
@app.on_event("startup")
async def startup_event():
    """
    Uygulama başlatıldığında
    """
    logger.info("🚀 Budget System API başlatılıyor...")
    logger.info(f"📊 Database: {settings.DATABASE_URL}")
    logger.info(f"🔄 Redis: {settings.REDIS_URL}")

# Shutdown Event
@app.on_event("shutdown")
async def shutdown_event():
    """
    Uygulama kapatıldığında
    """
    logger.info("🛑 Budget System API kapatılıyor...")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )