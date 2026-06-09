from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select

from app.db import SessionLocal
from app.models import Capture, CaptureStatus, Project


async def weekly_summary() -> str:
    since = datetime.now(timezone.utc) - timedelta(days=7)
    async with SessionLocal() as s:
        total = (await s.execute(
            select(func.count(Capture.id)).where(Capture.created_at >= since)
        )).scalar_one()
        rows = (await s.execute(
            select(Project.name, func.count(Capture.id))
            .join(Capture, Capture.project_id == Project.id)
            .where(Capture.created_at >= since)
            .group_by(Project.name)
            .order_by(func.count(Capture.id).desc())
        )).all()
        inbox = (await s.execute(
            select(func.count(Capture.id)).where(Capture.status == CaptureStatus.inbox)
        )).scalar_one()
    lines = [f"За неделю добавлено {total} вопросов."]
    if rows:
        lines.append("")
        lines.append("Основные темы:")
        for name, cnt in rows:
            lines.append(f"• {name} ({cnt})")
    lines.append("")
    lines.append(f"В Inbox сейчас: {inbox}.")
    lines.append("Решите судьбу каждой записи: /inbox")
    return "\n".join(lines)


async def overdue_inbox(ttl_days: int):
    cutoff = datetime.now(timezone.utc) - timedelta(days=ttl_days)
    async with SessionLocal() as s:
        rows = (await s.execute(
            select(Capture).where(
                Capture.status == CaptureStatus.inbox, Capture.created_at < cutoff
            )
        )).scalars().all()
        return rows