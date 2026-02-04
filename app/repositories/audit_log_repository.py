"""
Audit Log Repository - Database CRUD operations for audit logs
"""

from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.models.audit_log import AuditLog
from uuid import UUID
from typing import Optional, List, Tuple


class AuditLogRepository:
    """Audit log database operations"""

    @staticmethod
    def create(
        db: Session,
        user_id: Optional[UUID],
        action: str,
        target_table: str
    ) -> AuditLog:
        """Create a new audit log record"""
        audit_log = AuditLog(
            user_id=user_id,
            action=action,
            target_table=target_table
        )
        db.add(audit_log)
        db.commit()
        db.refresh(audit_log)
        return audit_log

    @staticmethod
    def get_by_id(db: Session, log_id: UUID) -> Optional[AuditLog]:
        """Get audit log by ID"""
        return db.query(AuditLog).filter(AuditLog.id == log_id).first()

    @staticmethod
    def get_all(
        db: Session,
        skip: int = 0,
        limit: int = 1000
    ) -> Tuple[List[AuditLog], int]:
        """Get all audit logs with pagination"""
        query = db.query(AuditLog).order_by(desc(AuditLog.created_at))
        total = query.count()
        logs = query.offset(skip).limit(limit).all()
        return logs, total

    @staticmethod
    def get_by_user(
        db: Session,
        user_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> Tuple[List[AuditLog], int]:
        """Get audit logs for a specific user"""
        query = db.query(AuditLog).filter(
            AuditLog.user_id == user_id
        ).order_by(desc(AuditLog.created_at))
        total = query.count()
        logs = query.offset(skip).limit(limit).all()
        return logs, total

    @staticmethod
    def get_by_table(
        db: Session,
        table_name: str,
        skip: int = 0,
        limit: int = 100
    ) -> Tuple[List[AuditLog], int]:
        """Get audit logs for a specific table"""
        query = db.query(AuditLog).filter(
            AuditLog.target_table == table_name
        ).order_by(desc(AuditLog.created_at))
        total = query.count()
        logs = query.offset(skip).limit(limit).all()
        return logs, total

    @staticmethod
    def get_by_action(
        db: Session,
        action: str,
        skip: int = 0,
        limit: int = 100
    ) -> Tuple[List[AuditLog], int]:
        """Get audit logs for a specific action"""
        query = db.query(AuditLog).filter(
            AuditLog.action == action
        ).order_by(desc(AuditLog.created_at))
        total = query.count()
        logs = query.offset(skip).limit(limit).all()
        return logs, total

    @staticmethod
    def count_all(db: Session) -> int:
        """Count total audit logs"""
        return db.query(AuditLog).count()

    @staticmethod
    def delete_old(db: Session, days: int = 90) -> int:
        """Delete audit logs older than specified days"""
        from datetime import datetime, timedelta
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        count = db.query(AuditLog).filter(
            AuditLog.created_at < cutoff_date
        ).delete()
        db.commit()
        return count
