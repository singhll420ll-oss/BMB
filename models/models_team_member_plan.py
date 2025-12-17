"""
Team Member Plan model definition
"""

from sqlalchemy import Column, Integer, Text, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from database import Base

class TeamMemberPlan(Base):
    """Team member plan model for daily plans/instructions"""
    __tablename__ = "team_member_plans"
    
    id = Column(Integer, primary_key=True, index=True)
    admin_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    team_member_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    description = Column(Text, nullable=False)
    image_url = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    admin = relationship("User", foreign_keys=[admin_id])
    team_member = relationship("User", foreign_keys=[team_member_id])
    
    def __repr__(self):
        return f"<TeamMemberPlan(id={self.id}, team_member_id={self.team_member_id})>"