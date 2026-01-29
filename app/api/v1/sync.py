from fastapi import APIRouter
from app.services.sap_connector import SAPConnector

router = APIRouter(prefix="/sync", tags=["Sync"])

@router.post("/sap/companies")
async def sync_companies():
    sap = SAPConnector()
    companies = sap.get_companies()
    # DB'ye ekle...
    return {"imported_count": len(companies)}