"""
CRUD operations for TeamMemberPlan model
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from sqlalchemy.orm import selectinload
from typing import Optional, List

from models.team_member_plan import TeamMemberPlan
from schemas.team_member_plan import TeamMemberPlanCreate

class TeamMemberPlanCRUD:
    """CRUD operations for TeamMemberPlan model"""
    
    @staticmethod
    async def create(db: AsyncSession, admin_id: int, plan_data: TeamMemberPlanCreate) -> TeamMemberPlan:
        """Create a new team member plan"""
        db_plan = TeamMemberPlan(
            admin_id=admin_id,
            team_member_id=plan_data.team_member_id,
            description=plan_data.description,
            image_url=plan_data.image_url
        )
        db.add(db_plan)
        await db.commit()
        await db.refresh(db_plan)
        return db_plan
    
    @staticmethod
    async def get_by_id(db: AsyncSession, plan_id: int) -> Optional[TeamMemberPlan]:
        """Get plan by ID"""
        result = await db.execute(
            select(TeamMemberPlan)
            .where(TeamMemberPlan.id == plan_id)
            .options(
                selectinload(TeamMemberPlan.admin),
                selectinload(TeamMemberPlan.team_member)
            )
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_by_team_member(db: AsyncSession, team_member_id: int, skip: int = 0, limit: int = 50) -> List[TeamMemberPlan]:
        """Get plans for a team member"""
        result = await db.execute(
            select(TeamMemberPlan)
            .where(TeamMemberPlan.team_member_id == team_member_id)
            .options(selectinload(TeamMemberPlan.admin))
            .order_by(TeamMemberPlan.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()
    
    @staticmethod
    async def get_all(db: AsyncSession, skip: int = 0, limit: int = 100) -> List[TeamMemberPlan]:
        """Get all plans"""
        result = await db.execute(
            select(TeamMemberPlan)
            .options(
                selectinload(TeamMemberPlan.admin),
                selectinload(TeamMemberPlan.team_member)
            )
            .order_by(TeamMemberPlan.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()
    
    @staticmethod
    async def delete(db: AsyncSession, plan_id: int) -> bool:
        """Delete a plan"""
        result = await db.execute(
            delete(TeamMemberPlan).where(TeamMemberPlan.id == plan_id)
        )
        await db.commit()
        return result.rowcount > 0

# Create instance
team_member_plan = TeamMemberPlanCRUD()
