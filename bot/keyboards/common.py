from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton


def language_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🇷🇺 Русский", callback_data="lang:ru"),
            InlineKeyboardButton(text="🇬🇧 English", callback_data="lang:en"),
            InlineKeyboardButton(text="🇺🇿 O'zbek", callback_data="lang:uz"),
        ]
    ])


def role_keyboard(lang: str = "ru") -> InlineKeyboardMarkup:
    from bot.middlewares.i18n import t
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=t("btn_participant", lang), callback_data="role:participant")],
        [InlineKeyboardButton(text=t("btn_volunteer", lang), callback_data="role:volunteer")],
    ])


def phone_keyboard(lang: str = "ru") -> ReplyKeyboardMarkup:
    from bot.middlewares.i18n import t
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=t("btn_share_phone", lang), request_contact=True)]],
        resize_keyboard=True,
        one_time_keyboard=True,
    )


def remove_keyboard():
    from aiogram.types import ReplyKeyboardRemove
    return ReplyKeyboardRemove()
