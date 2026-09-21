from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from bot.models.region import REGIONS


def regions_keyboard() -> InlineKeyboardMarkup:
    buttons = []
    for region in REGIONS:
        buttons.append([InlineKeyboardButton(text=region, callback_data=f"region:{region}")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)
