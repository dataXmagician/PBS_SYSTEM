"""
AuditLog Model - Denetim (audit) kayıtları

Alanlar: id, user_id, action, target_table, created_at
"""

from sqlalchemy import Column, String, DateTime, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID
import uuid
from app.db.base import Base


class AuditLog(Base):
    """Denetim kaydı - sistemdeki önemli aksiyonları loglamak için"""
    __tablename__ = "audit_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True, index=True, comment="İşlemi yapan kullanıcı ID")
    action = Column(String(200), nullable=False, comment="Gerçekleştirilen eylem (ör: create_budget)")
    target_table = Column(String(100), nullable=False, comment="Hedef tablo/varlık adı")
    created_at = Column(DateTime, default=func.now(), nullable=False, comment="Kayıt zamanı")

    def __repr__(self):
        return f"<AuditLog(id={self.id}, user_id={self.user_id}, action={self.action})>"
