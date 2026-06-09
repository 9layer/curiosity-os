import asyncio

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from aiogram import Bot

from app.config import settings
from app.services import review as rev

bot = Bot(token=settings.TELEGRAM_BOT_TOKEN)


async def send_weekly_review():
    text = await rev.weekly_summary()
    await bot.send_message(settings.ALLOWED_TELEGRAM_USER_ID, "🗓 Еженедельный обзор\n\n" + text)


async def nudge_overdue():
    rows = await rev.overdue_inbox(settings.INBOX_TTL_DAYS)
    if rows:
        await bot.send_message(
            settings.ALLOWED_TELEGRAM_USER_ID,
            f"⚠️ {len(rows)} записей висят в Inbox дольше {settings.INBOX_TTL_DAYS} дней. Пора решить: /inbox",
        )


def parse_cron(expr: str) -> CronTrigger:
    minute, hour, dom, month, dow = expr.split()
    return CronTrigger(minute=minute, hour=hour, day=dom, month=month, day_of_week=dow)


async def main():
    sched = AsyncIOScheduler(timezone="Europe/Warsaw")
    sched.add_job(send_weekly_review, parse_cron(settings.WEEKLY_REVIEW_CRON))
    sched.add_job(nudge_overdue, CronTrigger(hour=9, minute=0))
    sched.start()
    while True:
        await asyncio.sleep(3600)


if __name__ == "__main__":
    asyncio.run(main())