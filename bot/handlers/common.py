from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from bot.keyboards.common import language_keyboard, role_keyboard
from bot.middlewares.i18n import t

router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "👋 Добро пожаловать!\n\nВыберите язык / Choose language / Tilni tanlang:",
        reply_markup=language_keyboard(),
    )


@router.message(Command("cancel"))
async def cmd_cancel(message: Message, state: FSMContext, lang: str = "ru"):
    await state.clear()
    await message.answer(t("cancelled", lang))


@router.callback_query(F.data.startswith("lang:"))
async def choose_language(callback: CallbackQuery, state: FSMContext):
    lang = callback.data.split(":")[1]
    await state.update_data(language=lang)
    await callback.message.edit_text(
        t("welcome", lang),
        reply_markup=role_keyboard(lang),
    )
    await callback.answer()
