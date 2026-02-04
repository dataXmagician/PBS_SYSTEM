"""
Audit Log Service - Business logic for audit logs
"""

from sqlalchemy.orm import Session
from app.repositories.audit_log_repository import AuditLogRepository
from app.models.audit_log import AuditLog
from uuid import UUID
from typing import Optional, List
import logging

logger = logging.getLogger(__name__)


class AuditLogService:
    """Audit log business logic"""

    @staticmethod
    def log_action(
        db: Session,
        user_id: Optional[UUID],
        action: str,
        target_table: str
    ) -> AuditLog:
        """Log a system action"""
        try:
            log = AuditLogRepository.create(
                db,
                user_id=user_id,
                action=action,
                target_table=target_table
            )
            logger.info(f"Audit log created: {action} on {target_table}")
            return log
        except Exception as e:
            logger.error(f"Failed to create audit log: {e}")
            raise

    @staticmethod
    def get_audit_log(db: Session, log_id: UUID) -> Optional[dict]:
        """Get a single audit log"""
        log = AuditLogRepository.get_by_id(db, log_id)
        if not log:
            return None
        return {
            "id": str(log.id),
            "user_id": str(log.user_id) if log.user_id else None,
            "action": log.action,
            "target_table": log.target_table,
            "created_at": log.created_at.isoformat() if log.created_at else None,
        }

    @staticmethod
    def get_all_audit_logs(db: Session, skip: int = 0, limit: int = 1000) -> dict:
        """Get all audit logs"""
        logs, total = AuditLogRepository.get_all(db, skip, limit)
        return {
            "data": [
                {
                    "id": str(log.id),
                    "user_id": str(log.user_id) if log.user_id else None,
                    "action": log.action,
                    "target_table": log.target_table,
                    "created_at": log.created_at.isoformat() if log.created_at else None,
                }
                for log in logs
            ],
            "total": total,
            "skip": skip,
            "limit": limit,
        }

    @staticmethod
    def get_user_audit_logs(
        db: Session,
        user_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> dict:
        """Get audit logs for a user"""
        logs, total = AuditLogRepository.get_by_user(db, user_id, skip, limit)
        return {
            "data": [
                {
                    "id": str(log.id),
                    "user_id": str(log.user_id) if log.user_id else None,
                    "action": log.action,
                    "target_table": log.target_table,
                    "created_at": log.created_at.isoformat() if log.created_at else None,
                }
                for log in logs
            ],
            "total": total,
            "skip": skip,
            "limit": limit,
        }

    @staticmethod
    def get_table_audit_logs(
        db: Session,
        table_name: str,
        skip: int = 0,
        limit: int = 100
    ) -> dict:
        """Get audit logs for a specific table"""
        logs, total = AuditLogRepository.get_by_table(db, table_name, skip, limit)
        return {
            "data": [
                {
                    "id": str(log.id),
                    "user_id": str(log.user_id) if log.user_id else None,
                    "action": log.action,
                    "target_table": log.target_table,
                    "created_at": log.created_at.isoformat() if log.created_at else None,
                }
                for log in logs
            ],
            "total": total,
            "skip": skip,
            "limit": limit,
        }
