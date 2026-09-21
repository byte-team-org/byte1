from aiogram import Bot
from bot.config import settings


async def notify_admin_new_participant(bot: Bot, lang: str, full_name: str, phone: str,
                                       region: str, username: str, birth_date: str):
    from bot.middlewares.i18n import t
    text = t("admin_new_participant", "ru",
             full_name=full_name, phone=phone,
             region=region, username=username, birth_date=birth_date)
    try:
        await bot.send_message(settings.ADMIN_CHAT_ID, text, parse_mode="HTML")
    except Exception as e:
        print(f"[NOTIFY] Failed to notify admin: {e}")


async def notify_admin_new_volunteer(bot: Bot, lang: str, full_name: str, phone: str,
                                     region: str, username: str, birth_date: str,
                                     volunteer_id: int):
    from bot.middlewares.i18n import t
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    text = t("admin_new_volunteer", "ru",
             full_name=full_name, phone=phone,
             region=region, username=username, birth_date=birth_date)
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Одобрить", callback_data=f"approve_vol:{volunteer_id}"),
            InlineKeyboardButton(text="❌ Отклонить", callback_data=f"reject_vol:{volunteer_id}"),
        ]
    ])
    try:
        await bot.send_message(settings.ADMIN_CHAT_ID, text, reply_markup=keyboard, parse_mode="HTML")
    except Exception as e:
        print(f"[NOTIFY] Failed to notify admin: {e}")


async def notify_volunteer_approved(bot: Bot, telegram_id: int, lang: str):
    from bot.middlewares.i18n import t
    try:
        await bot.send_message(telegram_id, t("application_approved", lang), parse_mode="HTML")
    except Exception as e:
        print(f"[NOTIFY] Failed to notify volunteer {telegram_id}: {e}")


async def notify_volunteer_rejected(bot: Bot, telegram_id: int, lang: str):
    from bot.middlewares.i18n import t
    try:
        await bot.send_message(telegram_id, t("application_rejected", lang), parse_mode="HTML")
    except Exception as e:
        print(f"[NOTIFY] Failed to notify volunteer {telegram_id}: {e}")
