import re
from datetime import date, datetime
from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from bot.states.participant import ParticipantForm
from bot.keyboards.common import phone_keyboard, remove_keyboard
from bot.keyboards.regions import regions_keyboard
from bot.keyboards.participant import card_keyboard
from bot.middlewares.i18n import t
from bot.database import AsyncSessionLocal
from bot.models.participant import Participant
from bot.services.regions import check_and_reserve_participant
from bot.services.notifications import notify_admin_new_participant
from bot.config import settings
from sqlalchemy import select

router = Router()

PHONE_RE = re.compile(r"^\+?[0-9]{7,15}$")


# ── Entry point ────────────────────────────────────────────────────────────────

@router.callback_query(F.data == "role:participant")
async def start_participant(callback: CallbackQuery, state: FSMContext, lang: str):
    # Check if already registered
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(Participant).where(Participant.telegram_id == callback.from_user.id)
        )
        existing = result.scalar_one_or_none()
    if existing:
        await callback.message.edit_text(t("already_registered", lang))
        await callback.answer()
        return

    await state.set_state(ParticipantForm.last_name)
    await callback.message.edit_text(t("enter_lastname", lang), parse_mode="HTML")
    await callback.answer()


# ── Last Name ──────────────────────────────────────────────────────────────────

@router.message(ParticipantForm.last_name, F.text)
async def process_last_name(message: Message, state: FSMContext, lang: str):
    await state.update_data(last_name=message.text.strip())
    await state.set_state(ParticipantForm.first_name)
    await message.answer(t("enter_firstname", lang), parse_mode="HTML")


# ── First Name ─────────────────────────────────────────────────────────────────

@router.message(ParticipantForm.first_name, F.text)
async def process_first_name(message: Message, state: FSMContext, lang: str):
    await state.update_data(first_name=message.text.strip())
    await state.set_state(ParticipantForm.phone)
    await message.answer(
        t("share_phone", lang),
        reply_markup=phone_keyboard(lang),
        parse_mode="HTML",
    )


# ── Phone ──────────────────────────────────────────────────────────────────────

@router.message(ParticipantForm.phone, F.contact)
async def process_phone_contact(message: Message, state: FSMContext, lang: str):
    phone = message.contact.phone_number
    await state.update_data(phone=phone)
    await state.set_state(ParticipantForm.username)
    await message.answer(t("enter_username", lang), reply_markup=remove_keyboard(), parse_mode="HTML")


@router.message(ParticipantForm.phone, F.text)
async def process_phone_text(message: Message, state: FSMContext, lang: str):
    phone = message.text.strip()
    if not PHONE_RE.match(phone):
        await message.answer(t("invalid_phone", lang))
        return
    await state.update_data(phone=phone)
    await state.set_state(ParticipantForm.username)
    await message.answer(t("enter_username", lang), reply_markup=remove_keyboard(), parse_mode="HTML")


# ── Username ───────────────────────────────────────────────────────────────────

@router.message(ParticipantForm.username, F.text)
async def process_username(message: Message, state: FSMContext, lang: str):
    username = message.text.strip()
    if username.lower() in ("нет", "none", "yo'q", "no", "-"):
        username = None
    elif not username.startswith("@"):
        username = "@" + username
    await state.update_data(username=username)
    await state.set_state(ParticipantForm.birth_date)
    await message.answer(t("enter_birthdate", lang), parse_mode="HTML")


# ── Birth Date ─────────────────────────────────────────────────────────────────

@router.message(ParticipantForm.birth_date, F.text)
async def process_birth_date(message: Message, state: FSMContext, lang: str):
    raw = message.text.strip()
    try:
        birth = datetime.strptime(raw, "%d.%m.%Y").date()
    except ValueError:
        await message.answer(t("invalid_date", lang), parse_mode="HTML")
        return
    today = date.today()
    age = today.year - birth.year - ((today.month, today.day) < (birth.month, birth.day))
    if age < 16:
        await message.answer(t("too_young", lang))
        return
    await state.update_data(birth_date=raw)
    await state.set_state(ParticipantForm.region)
    await message.answer(t("choose_region", lang), reply_markup=regions_keyboard(), parse_mode="HTML")


# ── Region ─────────────────────────────────────────────────────────────────────

@router.callback_query(ParticipantForm.region, F.data.startswith("region:"))
async def process_region(callback: CallbackQuery, state: FSMContext, lang: str):
    region = callback.data.split(":", 1)[1]
    await callback.answer()

    async with AsyncSessionLocal() as session:
        reserved = await check_and_reserve_participant(session, region)

    if not reserved:
        await callback.message.edit_text(
            t("region_full", lang, region=region),
            parse_mode="HTML",
        )
        await state.clear()
        return

    await state.update_data(region=region)
    await state.set_state(ParticipantForm.payment)

    card = settings.CARD_NUMBER
    holder = settings.CARD_HOLDER
    await callback.message.edit_text(
        t("card_info", lang, card_number=card, card_holder=holder),
        reply_markup=card_keyboard(lang),
        parse_mode="HTML",
    )


@router.callback_query(F.data == "copy_card")
async def copy_card(callback: CallbackQuery, state: FSMContext, lang: str):
    card = settings.CARD_NUMBER
    await callback.answer()
    await callback.message.answer(
        t("card_number_copy", lang, card_number=card),
        parse_mode="HTML",
    )


# ── Receipt ────────────────────────────────────────────────────────────────────

@router.message(ParticipantForm.payment, F.document)
async def process_receipt_file(message: Message, state: FSMContext, lang: str, bot: Bot):
    file_id = message.document.file_id
    data = await state.get_data()

    async with AsyncSessionLocal() as session:
        participant = Participant(
            telegram_id=message.from_user.id,
            language=lang,
            last_name=data["last_name"],
            first_name=data["first_name"],
            phone=data["phone"],
            username=data.get("username"),
            birth_date=datetime.strptime(data["birth_date"], "%d.%m.%Y").date(),
            region=data["region"],
            card_number_shown=settings.CARD_NUMBER,
            receipt_file_id=file_id,
        )
        session.add(participant)
        await session.commit()

    full_name = f"{data['last_name']} {data['first_name']}"
    await message.answer(
        t("registration_complete", lang, full_name=full_name, region=data["region"]),
        parse_mode="HTML",
    )
    await state.clear()

    await notify_admin_new_participant(
        bot, lang,
        full_name=full_name,
        phone=data["phone"],
        region=data["region"],
        username=str(data.get("username") or "—"),
        birth_date=data["birth_date"],
    )


@router.message(ParticipantForm.payment)
async def process_receipt_wrong(message: Message, state: FSMContext, lang: str):
    """User sent photo or text instead of document."""
    await message.answer(t("receipt_not_file", lang), parse_mode="HTML")
