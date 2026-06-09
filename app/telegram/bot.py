import asyncio

from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command, CommandObject
from aiogram.types import CallbackQuery, Message

from app.config import settings
from app.db import SessionLocal
from app.llm.client import complete
from app.llm.prompts import EXPLORE_SYSTEM
from app.models import Capture, CaptureStatus
from app.services import capture as cap
from app.services import focus as foc
from app.services import review as rev
from app.telegram.keyboards import decision_kb, explore_kb

bot = Bot(token=settings.TELEGRAM_BOT_TOKEN)
dp = Dispatcher()
ALLOWED = settings.ALLOWED_TELEGRAM_USER_ID


def allowed(uid: int) -> bool:
    return uid == ALLOWED


@dp.message(Command("start"))
async def start(m: Message):
    if not allowed(m.from_user.id):
        return
    await m.answer(
        "Я секретарь твоего любопытства.\n\n"
        "• Пришли любую мысль — я зафиксирую и не буду отвлекать ответом.\n"
        "• /focus Проект | Источник | Цель — отметить текущее занятие.\n"
        "• /back — вернуть тебя к занятию.\n"
        "• /inbox — разобрать накопленное.\n"
        "• /review — обзор за неделю.\n"
        "• /explore <id> — кратко исследовать запись."
    )


@dp.message(Command("focus"))
async def focus_cmd(m: Message, command: CommandObject):
    if not allowed(m.from_user.id):
        return
    parts = (command.args or "").split("|")
    project = parts[0].strip() if parts and parts[0].strip() else None
    source = parts[1].strip() if len(parts) > 1 else None
    goal = parts[2].strip() if len(parts) > 2 else None
    await foc.set_focus(project, source, goal)
    await m.answer("Зафиксировал занятие. Пиши /back, когда отвлечёшься.")


@dp.message(Command("back"))
async def back_cmd(m: Message):
    if not allowed(m.from_user.id):
        return
    fs, count = await foc.get_active_focus()
    if fs is None:
        await m.answer("Пока не знаю, чем ты занимался. Отметь через /focus.")
        return
    text = ["До отвлечения ты занимался:"]
    if fs.project:
        text.append(f"Проект: {fs.project}.")
    if fs.source:
        text.append(f"Источник: {fs.source}.")
    if fs.goal:
        text.append(f"Последняя цель: {fs.goal}.")
    text.append(f"За это время возникло {count} вопросов — они сохранены.")
    await m.answer("\n".join(text))


@dp.message(Command("inbox"))
async def inbox_cmd(m: Message):
    if not allowed(m.from_user.id):
        return
    rows = await cap.list_inbox()
    if not rows:
        await m.answer("Inbox пуст. Так держать 👌")
        return
    await m.answer(f"В Inbox {len(rows)} записей. Реши судьбу каждой:")
    for c in rows:
        meta = []
        if c.topic:
            meta.append(c.topic)
        if c.suggested_project:
            meta.append(f"→ {c.suggested_project}")
        suffix = ("\n" + " ".join(meta)) if meta else ""
        await m.answer(f"#{c.id}: {c.raw_text}{suffix}", reply_markup=decision_kb(c.id))

@dp.message(Command("list"))
async def list_cmd(m: Message, command: CommandObject):
    if not allowed(m.from_user.id):
        return
    valid = [s.value for s in CaptureStatus]
    arg = (command.args or "").strip().lower()
    if arg not in valid:
        await m.answer("Укажи статус: /list <" + " | ".join(valid) + ">")
        return
    rows = await cap.list_by_status(CaptureStatus(arg))
    if not rows:
        await m.answer(f"В «{arg}» пусто.")
        return
    await m.answer(f"«{arg}» — {len(rows)} записей:")
    for c in rows:
        meta = []
        if c.topic:
            meta.append(c.topic)
        if c.suggested_project:
            meta.append(f"→ {c.suggested_project}")
        suffix = ("\n" + " ".join(meta)) if meta else ""
        await m.answer(f"#{c.id}: {c.raw_text}{suffix}", reply_markup=decision_kb(c.id))

@dp.message(Command("review"))
async def review_cmd(m: Message):
    if not allowed(m.from_user.id):
        return
    await m.answer(await rev.weekly_summary())


@dp.message(Command("explore"))
async def explore_cmd(m: Message, command: CommandObject):
    if not allowed(m.from_user.id):
        return
    if not command.args:
        await m.answer("Укажи id: /explore 12")
        return
    try:
        cid = int(command.args.strip())
    except ValueError:
        await m.answer("id должен быть числом.")
        return
    await do_explore(m.chat.id, cid)


async def do_explore(chat_id: int, capture_id: int):
    async with SessionLocal() as s:
        c = await s.get(Capture, capture_id)
    if c is None:
        await bot.send_message(chat_id, "Не нашёл такую запись.")
        return
    await cap.set_status(capture_id, CaptureStatus.explore)
    answer = await complete(EXPLORE_SYSTEM, c.raw_text, max_tokens=350)
    await bot.send_message(
        chat_id,
        f"{answer}\n\n⏳ Таймбокс {settings.EXPLORE_TIMEBOX_MIN} мин. Продолжить или вернуться?",
        reply_markup=explore_kb(capture_id),
    )


@dp.callback_query(F.data.startswith("st:"))
async def on_status(cq: CallbackQuery):
    if not allowed(cq.from_user.id):
        return
    _, status, cid = cq.data.split(":")
    await cap.set_status(int(cid), CaptureStatus(status))
    await cq.answer("Готово")
    await cq.message.edit_text(f"{cq.message.text}\n\n✅ Статус: {status}")


@dp.callback_query(F.data.startswith("ex:"))
async def on_explore(cq: CallbackQuery):
    if not allowed(cq.from_user.id):
        return
    _, action, cid = cq.data.split(":")
    if action == "more":
        await cq.answer()
        await do_explore(cq.message.chat.id, int(cid))
    else:
        await cap.set_status(int(cid), CaptureStatus.scheduled)
        await cq.answer("Возвращаемся")
        fs, _ = await foc.get_active_focus()
        if fs and fs.project:
            await cq.message.answer(f"Возвращайся к: {fs.project}. Цель: {fs.goal or '—'}.")
        else:
            await cq.message.answer("Хорошо, вернись к основному занятию 🙂")


@dp.message(F.text & ~F.text.startswith("/"))
async def capture_msg(m: Message):
    if not allowed(m.from_user.id):
        return
    cid = await cap.create_capture(m.text)
    sent = await m.answer("✅ Сохранил. Не отвлекаю — позже разберёшь в /inbox.")
    asyncio.create_task(enrich_and_update(cid, sent))


async def enrich_and_update(cid: int, sent: Message):
    try:
        c = await cap.enrich_capture(cid)
        if c is None:
            return
        bits = ["✅ Сохранил."]
        if c.topic:
            bits.append(f"Тема: {c.topic}.")
        if c.suggested_project:
            bits.append(f"Проект: {c.suggested_project}.")
        elif c.project_id is None:
            bits.append("Проект не ясен → Inbox.")
        bits.append("Позже разберёшь в /inbox.")
        await sent.edit_text(" ".join(bits))
    except Exception:
        pass


async def main():
    for _ in range(30):
        try:
            await cap.ensure_seed_projects()
            break
        except Exception:
            await asyncio.sleep(2)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())