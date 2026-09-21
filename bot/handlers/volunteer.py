import re
from datetime import date, datetime
from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from bot.states.volunteer import VolunteerForm
from bot.keyboards.common import phone_keyboard, remove_keyboard
from bot.keyboards.regions import regions_keyboard
from bot.middlewares.i18n import t
from bot.database import AsyncSessionLocal
from bot.models.volunteer import Volunteer, VolunteerStatus
from bot.services.regions import check_and_reserve_volunteer
from bot.services.notifications import (
    notify_admin_new_volunteer,
    notify_volunteer_approved,
    notify_volunteer_rejected,
)
from sqlalchemy import select

router = Router()

PHONE_RE = re.compile(r"^\+?[0-9]{7,15}$")


# ── Entry point ────────────────────────────────────────────────────────────────

@router.callback_query(F.data == "role:volunteer")
async def start_volunteer(callback: CallbackQuery, state: FSMContext, lang: str):
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(Volunteer).where(Volunteer.telegram_id == callback.from_user.id)
        )
        existing = result.scalar_one_or_none()
    if existing:
        await callback.message.edit_text(t("already_registered", lang))
        await callback.answer()
        return

    await state.set_state(VolunteerForm.photo)
    await callback.message.edit_text(t("upload_photo", lang), parse_mode="HTML")
    await callback.answer()


# ── Photo ──────────────────────────────────────────────────────────────────────

@router.message(VolunteerForm.photo, F.photo)
async def process_photo(message: Message, state: FSMContext, lang: str):
    # Get the highest-quality photo
    photo_file_id = message.photo[-1].file_id
    await state.update_data(photo_file_id=photo_file_id)
    await state.set_state(VolunteerForm.full_name)
    await message.answer(t("enter_fullname", lang), parse_mode="HTML")


@router.message(VolunteerForm.photo)
async def process_photo_wrong(message: Message, state: FSMContext, lang: str):
    await message.answer(t("photo_required", lang), parse_mode="HTML")


# ── Full Name ──────────────────────────────────────────────────────────────────

@router.message(VolunteerForm.full_name, F.text)
async def process_fullname(message: Message, state: FSMContext, lang: str):
    await state.update_data(full_name=message.text.strip())
    await state.set_state(VolunteerForm.phone)
    await message.answer(
        t("share_phone", lang),
        reply_markup=phone_keyboard(lang),
        parse_mode="HTML",
    )


# ── Phone ──────────────────────────────────────────────────────────────────────

@router.message(VolunteerForm.phone, F.contact)
async def process_phone_contact(message: Message, state: FSMContext, lang: str):
    await state.update_data(phone=message.contact.phone_number)
    await state.set_state(VolunteerForm.username)
    await message.answer(t("enter_username", lang), reply_markup=remove_keyboard(), parse_mode="HTML")


@router.message(VolunteerForm.phone, F.text)
async def process_phone_text(message: Message, state: FSMContext, lang: str):
    phone = message.text.strip()
    if not PHONE_RE.match(phone):
        await message.answer(t("invalid_phone", lang))
        return
    await state.update_data(phone=phone)
    await state.set_state(VolunteerForm.username)
    await message.answer(t("enter_username", lang), reply_markup=remove_keyboard(), parse_mode="HTML")


# ── Username ───────────────────────────────────────────────────────────────────

@router.message(VolunteerForm.username, F.text)
async def process_username(message: Message, state: FSMContext, lang: str):
    username = message.text.strip()
    if username.lower() in ("нет", "none", "yo'q", "no", "-"):
        username = None
    elif not username.startswith("@"):
        username = "@" + username
    await state.update_data(username=username)
    await state.set_state(VolunteerForm.birth_date)
    await message.answer(t("enter_birthdate", lang), parse_mode="HTML")


# ── Birth Date ─────────────────────────────────────────────────────────────────

@router.message(VolunteerForm.birth_date, F.text)
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
    await state.set_state(VolunteerForm.region)
    await message.answer(t("choose_region", lang), reply_markup=regions_keyboard(), parse_mode="HTML")


# ── Region ─────────────────────────────────────────────────────────────────────

@router.callback_query(VolunteerForm.region, F.data.startswith("region:"))
async def process_region(callback: CallbackQuery, state: FSMContext, lang: str, bot: Bot):
    region = callback.data.split(":", 1)[1]
    await callback.answer()

    async with AsyncSessionLocal() as session:
        reserved = await check_and_reserve_volunteer(session, region)

    if not reserved:
        await callback.message.edit_text(
            t("region_full", lang, region=region),
            parse_mode="HTML",
        )
        await state.clear()
        return

    data = await state.get_data()
    await state.update_data(region=region)

    async with AsyncSessionLocal() as session:
        volunteer = Volunteer(
            telegram_id=callback.from_user.id,
            language=lang,
            photo_file_id=data["photo_file_id"],
            full_name=data["full_name"],
            phone=data["phone"],
            username=data.get("username"),
            birth_date=datetime.strptime(data["birth_date"], "%d.%m.%Y").date(),
            region=region,
        )
        session.add(volunteer)
        await session.commit()
        await session.refresh(volunteer)
        vol_id = volunteer.id

    await callback.message.edit_text(
        t("application_submitted", lang),
        parse_mode="HTML",
    )
    await state.clear()

    await notify_admin_new_volunteer(
        bot, lang,
        full_name=data["full_name"],
        phone=data["phone"],
        region=region,
        username=str(data.get("username") or "—"),
        birth_date=data["birth_date"],
        volunteer_id=vol_id,
    )


# ── Admin: approve / reject volunteer ─────────────────────────────────────────

@router.callback_query(F.data.startswith("approve_vol:"))
async def admin_approve_volunteer(callback: CallbackQuery, bot: Bot):
    vol_id = int(callback.data.split(":")[1])
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(Volunteer).where(Volunteer.id == vol_id)
        )
        volunteer = result.scalar_one_or_none()
        if not volunteer:
            await callback.answer("Волонтёр не найден", show_alert=True)
            return
        volunteer.status = VolunteerStatus.approved
        await session.commit()
        tg_id = volunteer.telegram_id
        lang = volunteer.language

    await notify_volunteer_approved(bot, tg_id, lang)
    await callback.message.edit_text(
        callback.message.text + "\n\n✅ <b>Одобрено</b>",
        parse_mode="HTML",
    )
    await callback.answer("Одобрено!")


@router.callback_query(F.data.startswith("reject_vol:"))
async def admin_reject_volunteer(callback: CallbackQuery, bot: Bot):
    vol_id = int(callback.data.split(":")[1])
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(Volunteer).where(Volunteer.id == vol_id)
        )
        volunteer = result.scalar_one_or_none()
        if not volunteer:
            await callback.answer("Волонтёр не найден", show_alert=True)
            return
        volunteer.status = VolunteerStatus.rejected
        await session.commit()
        tg_id = volunteer.telegram_id
        lang = volunteer.language

    await notify_volunteer_rejected(bot, tg_id, lang)
    await callback.message.edit_text(
        callback.message.text + "\n\n❌ <b>Отклонено</b>",
        parse_mode="HTML",
    )
    await callback.answer("Отклонено!")
