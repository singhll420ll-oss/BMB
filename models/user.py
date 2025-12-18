"""
User model definition
"""

from sqlalchemy import Column, Integer, String, DateTime, Enum, Text
from sqlalchemy.sql import func
import enum

from database import Base

class UserRole(str, enum.Enum):
    """User role enumeration"""
    CUSTOMER = "customer"
    TEAM_MEMBER = "team_member"
    ADMIN = "admin"

class User(Base):
    """User model for customers, team members, and admins"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(100), unique=True, nullable=False, index=True)
    phone = Column(String(20), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    address = Column(Text, nullable=True)
    role = Column(Enum(UserRole), nullable=False, default=UserRole.CUSTOMER)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships will be defined in schemas if needed
    
    def __repr__(self):
        return f"<User(id={self.id}, username={self.username}, role={self.role})>"
