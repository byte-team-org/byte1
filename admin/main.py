from fastapi import FastAPI, Request, Depends, HTTPException, status, Form
from fastapi.responses import HTMLResponse, RedirectResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import Optional
import csv
import io
import os

from bot.database import AsyncSessionLocal, init_db
from bot.models.participant import Participant, ParticipantStatus
from bot.models.volunteer import Volunteer, VolunteerStatus
from bot.models.region import RegionCapacity
from bot.config import settings

app = FastAPI(title="Byte Admin Panel")

TEMPLATES_DIR = os.path.join(os.path.dirname(__file__), "templates")
templates = Jinja2Templates(directory=TEMPLATES_DIR)

# Simple session tracking (in-memory for simplicity)
_sessions: set[str] = set()


def get_session_token(request: Request) -> Optional[str]:
    return request.cookies.get("admin_session")


def require_auth(request: Request):
    token = get_session_token(request)
    if not token or token not in _sessions:
        raise HTTPException(status_code=302, headers={"Location": "/admin/login"})
    return token


async def get_db():
    async with AsyncSessionLocal() as session:
        yield session


# ── Auth ───────────────────────────────────────────────────────────────────────

@app.get("/admin/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request, "error": None})


@app.post("/admin/login")
async def login(request: Request, username: str = Form(...), password: str = Form(...)):
    if username == settings.ADMIN_USERNAME and password == settings.ADMIN_PASSWORD:
        import secrets
        token = secrets.token_hex(32)
        _sessions.add(token)
        response = RedirectResponse(url="/admin/dashboard", status_code=302)
        response.set_cookie("admin_session", token, httponly=True)
        return response
    return templates.TemplateResponse("login.html", {"request": request, "error": "Неверные данные"})


@app.get("/admin/logout")
async def logout(request: Request):
    token = get_session_token(request)
    if token:
        _sessions.discard(token)
    response = RedirectResponse(url="/admin/login", status_code=302)
    response.delete_cookie("admin_session")
    return response


# ── Dashboard ──────────────────────────────────────────────────────────────────

@app.get("/admin/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request, db: AsyncSession = Depends(get_db), auth=Depends(require_auth)):
    regions_result = await db.execute(select(RegionCapacity))
    regions = regions_result.scalars().all()

    p_count = await db.execute(select(func.count()).select_from(Participant))
    v_count = await db.execute(select(func.count()).select_from(Volunteer))

    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "regions": regions,
        "total_participants": p_count.scalar(),
        "total_volunteers": v_count.scalar(),
    })


# ── Participants ───────────────────────────────────────────────────────────────

@app.get("/admin/participants", response_class=HTMLResponse)
async def participants_list(
    request: Request,
    region: Optional[str] = None,
    status: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    auth=Depends(require_auth),
):
    query = select(Participant).order_by(Participant.created_at.desc())
    if region:
        query = query.where(Participant.region == region)
    if status:
        query = query.where(Participant.status == status)
    result = await db.execute(query)
    participants = result.scalars().all()

    from bot.models.region import REGIONS
    return templates.TemplateResponse("participants.html", {
        "request": request,
        "participants": participants,
        "regions": REGIONS,
        "selected_region": region,
        "selected_status": status,
    })


@app.get("/admin/participants/export")
async def export_participants(db: AsyncSession = Depends(get_db), auth=Depends(require_auth)):
    result = await db.execute(select(Participant).order_by(Participant.created_at.desc()))
    participants = result.scalars().all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["ID", "Telegram ID", "Язык", "Фамилия", "Имя", "Телефон", "Username",
                     "Дата рождения", "Регион", "Статус", "Дата регистрации"])
    for p in participants:
        writer.writerow([
            p.id, p.telegram_id, p.language, p.last_name, p.first_name,
            p.phone, p.username or "—", p.birth_date, p.region, p.status.value,
            p.created_at.strftime("%d.%m.%Y %H:%M") if p.created_at else "—",
        ])
    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=participants.csv"},
    )


# ── Volunteers ─────────────────────────────────────────────────────────────────

@app.get("/admin/volunteers", response_class=HTMLResponse)
async def volunteers_list(
    request: Request,
    region: Optional[str] = None,
    status: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    auth=Depends(require_auth),
):
    query = select(Volunteer).order_by(Volunteer.created_at.desc())
    if region:
        query = query.where(Volunteer.region == region)
    if status:
        query = query.where(Volunteer.status == status)
    result = await db.execute(query)
    volunteers = result.scalars().all()

    from bot.models.region import REGIONS
    return templates.TemplateResponse("volunteers.html", {
        "request": request,
        "volunteers": volunteers,
        "regions": REGIONS,
        "selected_region": region,
        "selected_status": status,
    })


@app.get("/admin/volunteers/export")
async def export_volunteers(db: AsyncSession = Depends(get_db), auth=Depends(require_auth)):
    result = await db.execute(select(Volunteer).order_by(Volunteer.created_at.desc()))
    volunteers = result.scalars().all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["ID", "Telegram ID", "Язык", "ФИО", "Телефон", "Username",
                     "Дата рождения", "Регион", "Статус", "Дата регистрации"])
    for v in volunteers:
        writer.writerow([
            v.id, v.telegram_id, v.language, v.full_name,
            v.phone, v.username or "—", v.birth_date, v.region, v.status.value,
            v.created_at.strftime("%d.%m.%Y %H:%M") if v.created_at else "—",
        ])
    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=volunteers.csv"},
    )


@app.on_event("startup")
async def startup():
    await init_db()


@app.get("/")
async def root():
    return RedirectResponse(url="/admin/dashboard")
