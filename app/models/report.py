"""
Report Model - Bütçe Raporları
"""

from sqlalchemy import Column, String, DateTime, func, ForeignKey, Text, LargeBinary
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from app.db.base import Base

class Report(Base):
    """
    Oluşturulmuş rapor kaydı
    """
    __tablename__ = "reports"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    budget_id = Column(UUID(as_uuid=True), ForeignKey("budgets.id"), nullable=False, index=True)
    report_type = Column(String(50), nullable=False, comment="Rapor Tipi (SUMMARY, DETAILED, VARIANCE)")
    report_format = Column(String(10), nullable=False, comment="Format (PDF, EXCEL)")
    title = Column(String(200), comment="Rapor Başlığı")
    description = Column(Text, comment="Rapor Açıklaması")
    file_path = Column(String(500), comment="Dosya Yolu")
    file_size = Column(String(50), comment="Dosya Boyutu")
    generated_by = Column(String(100), comment="Oluşturan Kullanıcı")
    created_date = Column(DateTime, default=func.now(), nullable=False)
    
    # Relationships
    budget = relationship("Budget", backref="reports")
    
    def __repr__(self):
        return f"<Report(id={self.id}, type={self.report_type}, format={self.report_format})>"
