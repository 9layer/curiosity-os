from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def decision_kb(capture_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🔍 Изучить", callback_data=f"st:explore:{capture_id}"),
            InlineKeyboardButton(text="📅 Отложить", callback_data=f"st:scheduled:{capture_id}"),
        ],
        [
            InlineKeyboardButton(text="💤 Когда-нибудь", callback_data=f"st:someday:{capture_id}"),
            InlineKeyboardButton(text="🗄 Архив", callback_data=f"st:archived:{capture_id}"),
        ],
        [InlineKeyboardButton(text="🗑 Удалить", callback_data=f"st:deleted:{capture_id}")],
    ])


def explore_kb(capture_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="▶️ Продолжить", callback_data=f"ex:more:{capture_id}"),
        InlineKeyboardButton(text="↩️ К проекту", callback_data=f"ex:back:{capture_id}"),
    ]])