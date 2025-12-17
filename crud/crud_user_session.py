"""
CRUD operations for UserSession model
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from typing import Optional, List, Tuple
from datetime import datetime, date, timedelta

from models.user_session import UserSession
from models.user import User

class UserSessionCRUD:
    """CRUD operations for UserSession model"""
    
    @staticmethod
    async def create_login(db: AsyncSession, user_id: int) -> UserSession:
        """Create a new login session"""
        db_session = UserSession(
            user_id=user_id,
            login_time=datetime.utcnow(),
            date=date.today()
        )
        db.add(db_session)
        await db.commit()
        await db.refresh(db_session)
        return db_session
    
    @staticmethod
    async def update_logout(db: AsyncSession, session_id: int) -> Optional[UserSession]:
        """Update logout time for a session"""
        from sqlalchemy import update
        
        await db.execute(
            update(UserSession)
            .where(UserSession.id == session_id)
            .values(logout_time=datetime.utcnow())
        )
        await db.commit()
        
        result = await db.execute(
            select(UserSession).where(UserSession.id == session_id)
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_active_sessions(db: AsyncSession) -> List[UserSession]:
        """Get all active sessions (without logout time)"""
        result = await db.execute(
            select(UserSession)
            .where(UserSession.logout_time.is_(None))
            .options(selectinload(UserSession.user))
            .order_by(UserSession.login_time.desc())
        )
        return result.scalars().all()
    
    @staticmethod
    async def get_user_sessions(db: AsyncSession, user_id: int, skip: int = 0, limit: int = 100) -> List[UserSession]:
        """Get all sessions for a user"""
        result = await db.execute(
            select(UserSession)
            .where(UserSession.user_id == user_id)
            .order_by(UserSession.login_time.desc())
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()
    
    @staticmethod
    async def get_today_sessions(db: AsyncSession) -> List[UserSession]:
        """Get today's sessions"""
        result = await db.execute(
            select(UserSession)
            .where(UserSession.date == date.today())
            .options(selectinload(UserSession.user))
            .order_by(UserSession.login_time.desc())
        )
        return result.scalars().all()
    
    @staticmethod
    async def get_session_stats(db: AsyncSession, user_id: Optional[int] = None, days: int = 30) -> dict:
        """Get session statistics"""
        start_date = date.today() - timedelta(days=days)
        
        query = select(
            UserSession.user_id,
            User.name.label("user_name"),
            User.role,
            func.count(UserSession.id).label("session_count"),
            func.avg(
                func.extract('epoch', UserSession.logout_time - UserSession.login_time)
            ).label("avg_duration"),
            func.max(UserSession.login_time).label("last_login")
        ).join(User)
        
        if user_id:
            query = query.where(UserSession.user_id == user_id)
        
        query = query.where(UserSession.date >= start_date)
        query = query.where(UserSession.logout_time.isnot(None))
        query = query.group_by(UserSession.user_id, User.name, User.role)
        query = query.order_by(func.count(UserSession.id).desc())
        
        result = await db.execute(query)
        rows = result.all()
        
        stats = []
        for row in rows:
            stats.append({
                "user_id": row.user_id,
                "user_name": row.user_name,
                "role": row.role,
                "session_count": row.session_count,
                "avg_duration": float(row.avg_duration or 0),
                "last_login": row.last_login
            })
        
        return {"stats": stats, "period_days": days}

# Create instance
user_session = UserSessionCRUD()