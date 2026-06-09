from fastapi import FastAPI
from sqlalchemy import func, select

from app.db import SessionLocal
from app.models import Capture, CaptureStatus

app = FastAPI(title="Curiosity OS")


@app.get("/health")
async def health():
    return {"ok": True}


@app.get("/stats")
async def stats():
    result = {}
    async with SessionLocal() as s:
        for st in CaptureStatus:
            cnt = (await s.execute(
                select(func.count(Capture.id)).where(Capture.status == st)
            )).scalar_one()
            result[st.value] = cnt
    return result