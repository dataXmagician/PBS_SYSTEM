"""
Audit Log API Endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from uuid import UUID

from app.db.session import get_db
from app.dependencies import get_current_user
from app.schemas.user import UserResponse
from app.services.audit_log_service import AuditLogService
import logging

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/audit-logs",
    tags=["Audit Logs"],
    responses={404: {"description": "Not found"}},
)


# GET - List all audit logs
@router.get("", response_model=dict)
async def list_audit_logs(
    skip: int = Query(0, ge=0),
    limit: int = Query(1000, ge=1, le=5000),
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
):
    """
    List all audit logs with pagination
    """
    try:
        return AuditLogService.get_all_audit_logs(db, skip, limit)
    except Exception as e:
        logger.error(f"Error listing audit logs: {e}")
        raise HTTPException(status_code=500, detail="Denetim kayıtları listelemek başarısız")


# GET - Get audit log by ID
@router.get("/{log_id}", response_model=dict)
async def get_audit_log(
    log_id: UUID,
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
):
    """
    Get a specific audit log by ID
    """
    try:
        log = AuditLogService.get_audit_log(db, log_id)
        if not log:
            raise HTTPException(status_code=404, detail=f"Denetim kaydı bulunamadı: {log_id}")
        return log
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting audit log: {e}")
        raise HTTPException(status_code=500, detail="Denetim kaydı getirilemedi")


# POST - Create test audit logs (for development)
@router.post("/test/create-samples", response_model=dict)
async def create_sample_audit_logs(
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
):
    """
    Create sample audit logs for testing (development only)
    """
    try:
        from app.models.audit_log import AuditLog
        import uuid
        from datetime import datetime, timedelta
        
        # Clear existing records
        db.query(AuditLog).delete()
        db.commit()
        
        # Create sample audit logs
        sample_logs = [
            AuditLog(
                user_id=current_user.id,
                action="create_budget",
                target_table="budgets",
            ),
            AuditLog(
                user_id=current_user.id,
                action="update_budget",
                target_table="budgets",
            ),
            AuditLog(
                user_id=current_user.id,
                action="delete_forecast",
                target_table="forecasts",
            ),
            AuditLog(
                user_id=None,
                action="login_user",
                target_table="users",
            ),
            AuditLog(
                user_id=current_user.id,
                action="create_scenario",
                target_table="scenarios",
            ),
        ]
        
        db.add_all(sample_logs)
        db.commit()
        
        return {
            "success": True,
            "message": f"{len(sample_logs)} örnek denetim kaydı oluşturuldu",
            "count": len(sample_logs),
        }
    except Exception as e:
        logger.error(f"Error creating sample audit logs: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Örnek denetim kayıtları oluşturulamadı")


# GET - Get audit logs by user
@router.get("/user/{user_id}", response_model=dict)
async def get_user_audit_logs(
    user_id: UUID,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
):
    """
    Get audit logs for a specific user
    """
    try:
        return AuditLogService.get_user_audit_logs(db, user_id, skip, limit)
    except Exception as e:
        logger.error(f"Error getting user audit logs: {e}")
        raise HTTPException(status_code=500, detail="Kullanıcı denetim kayıtları getirilemedi")


# GET - Get audit logs by table
@router.get("/table/{table_name}", response_model=dict)
async def get_table_audit_logs(
    table_name: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
):
    """
    Get audit logs for a specific table
    """
    try:
        return AuditLogService.get_table_audit_logs(db, table_name, skip, limit)
    except Exception as e:
        logger.error(f"Error getting table audit logs: {e}")
        raise HTTPException(status_code=500, detail="Tablo denetim kayıtları getirilemedi")
