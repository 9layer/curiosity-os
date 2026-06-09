from datetime import datetime, timezone

from sqlalchemy import func, select

from app.db import SessionLocal
from app.llm.client import complete_json
from app.llm.prompts import ENRICH_SYSTEM
from app.models import Capture, CaptureStatus, DEFAULT_PROJECTS, Project


async def ensure_seed_projects():
    async with SessionLocal() as s:
        count = (await s.execute(select(func.count(Project.id)))).scalar_one()
        if count == 0:
            s.add_all([Project(name=n) for n in DEFAULT_PROJECTS])
            await s.commit()


async def create_capture(raw_text: str) -> int:
    async with SessionLocal() as s:
        c = Capture(raw_text=raw_text, status=CaptureStatus.inbox)
        s.add(c)
        await s.commit()
        await s.refresh(c)
        return c.id


async def enrich_capture(capture_id: int):
    async with SessionLocal() as s:
        projects = (await s.execute(select(Project))).scalars().all()
        names = [p.name for p in projects]
        c = await s.get(Capture, capture_id)
        if c is None:
            return None
        data = await complete_json(
            ENRICH_SYSTEM.replace("{projects}", ", ".join(names)), c.raw_text
        )
        c.entities = data.get("entities") or []
        c.topic = data.get("topic")
        c.is_question = bool(data.get("is_question", False))
        sp = data.get("suggested_project")
        c.suggested_project = sp
        if sp:
            match = next((p for p in projects if p.name.lower() == str(sp).lower()), None)
            if match:
                c.project_id = match.id
        await s.commit()
        await s.refresh(c)
        return c


async def set_status(capture_id: int, status: CaptureStatus):
    async with SessionLocal() as s:
        c = await s.get(Capture, capture_id)
        if c:
            c.status = status
            c.decided_at = datetime.now(timezone.utc)
            await s.commit()


async def list_inbox(limit: int = 20):
    async with SessionLocal() as s:
        rows = (await s.execute(
            select(Capture)
            .where(Capture.status == CaptureStatus.inbox)
            .order_by(Capture.created_at.desc())
            .limit(limit)
        )).scalars().all()
        return rows