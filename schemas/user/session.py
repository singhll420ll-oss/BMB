"""
Pydantic schemas for UserSession model
"""

from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class UserSessionResponse(BaseModel):
    """Schema for user session response"""
    id: int
    user_id: int
    user_name: str
    user_role: str
    login_time: datetime
    logout_time: Optional[datetime]
    date: datetime
    duration_seconds: Optional[float]
    
    class Config:
        from_attributes = True
