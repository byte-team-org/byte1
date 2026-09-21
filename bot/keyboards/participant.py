from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def card_keyboard(lang: str = "ru") -> InlineKeyboardMarkup:
    from bot.middlewares.i18n import t
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=t("btn_copy_card", lang), callback_data="copy_card")]
    ])
