"""
Service model definition
"""

from sqlalchemy import Column, Integer, String, Text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from database import Base

class Service(Base):
    """Service model for different food services"""
    __tablename__ = "services"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, index=True)
    description = Column(Text, nullable=True)
    image_url = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationship with menu items
    menu_items = relationship("MenuItem", back_populates="service", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Service(id={self.id}, name={self.name})>"
