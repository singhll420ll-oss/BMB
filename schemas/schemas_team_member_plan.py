"""
Pydantic schemas for TeamMemberPlan model
"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class TeamMemberPlanCreate(BaseModel):
    """Schema for creating a team member plan"""
    team_member_id: int
    description: str = Field(..., min_length=1)
    image_url: Optional[str] = None

class TeamMemberPlanResponse(BaseModel):
    """Schema for team member plan response"""
    id: int
    admin_id: int
    admin_name: str
    team_member_id: int
    team_member_name: str
    description: str
    image_url: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True