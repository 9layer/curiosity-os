from datetime import datetime, timezone

from sqlalchemy import func, select, update

from app.db import SessionLocal
from app.models import Capture, FocusSession


async def set_focus(project, source, goal):
    async with SessionLocal() as s:
        await s.execute(
            update(FocusSession)
            .where(FocusSession.active.is_(True))
            .values(active=False, ended_at=datetime.now(timezone.utc))
        )
        fs = FocusSession(project=project, source=source, goal=goal, active=True)
        s.add(fs)
        await s.commit()
        await s.refresh(fs)
        return fs


async def get_active_focus():
    async with SessionLocal() as s:
        fs = (await s.execute(
            select(FocusSession)
            .where(FocusSession.active.is_(True))
            .order_by(FocusSession.started_at.desc())
        )).scalars().first()
        if fs is None:
            return None, 0
        count = (await s.execute(
            select(func.count(Capture.id)).where(Capture.created_at >= fs.started_at)
        )).scalar_one()
        return fs, count