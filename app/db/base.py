"""
SQLAlchemy Declarative Base and Common Models
"""

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, DateTime, func
from datetime import datetime

Base = declarative_base()



class BaseModel(Base):
    """
    Base model for all database models
    """
    __abstract__ = True
    
    created_date = Column(
        DateTime,
        default=func.now(),
        nullable=False,
        comment="Oluşturulma tarihi"
    )
    updated_date = Column(
        DateTime,
        default=func.now(),
        onupdate=func.now(),
        nullable=False,
        comment="Son güncellenme tarihi"
    )