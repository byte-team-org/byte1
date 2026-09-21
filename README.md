# ⚡ Byte — Event Registration Telegram Bot

Telegram bot for event registration with two flows: **Participant** and **Volunteer/Ambassador**.  
Built with **aiogram 3**, **PostgreSQL**, **FastAPI** admin panel.

## 🚀 Quick Start

### 1. Clone & configure
```bash
cp .env.example .env
# Edit .env — add BOT_TOKEN, ADMIN_CHAT_ID, DATABASE_URL
```

### 2. Run with Docker (recommended)
```bash
docker-compose up --build
```

Admin panel → http://localhost:8000/admin/dashboard  
Login: `admin` / `admin123` (change in .env)

### 3. Run locally (development)

```bash
# Install dependencies
pip install -r requirements.txt

# Start PostgreSQL (or use docker-compose for only DB)
docker-compose up postgres -d

# Run bot
python -m bot.main

# Run admin panel (separate terminal)
uvicorn admin.main:app --reload --port 8000
```

## 📁 Structure

```
bot/
├── handlers/       FSM handlers (participant, volunteer, common)
├── states/         FSM state groups
├── models/         SQLAlchemy models
├── keyboards/      Inline & reply keyboards
├── middlewares/    i18n middleware
├── services/       Business logic (regions, notifications)
└── locales/        ru.json, en.json, uz.json

admin/
├── main.py         FastAPI app
└── templates/      Jinja2 HTML templates
```

## ✨ Features

- **3 languages**: Russian, English, Uzbek
- **Atomic region capacity** — no race conditions, DB-level locking
- **Phone validation** — contact share or manual +998XXXXXXXXX
- **Date validation** — real date, minimum age 16 years
- **File receipt** — only accepts document (not photo)
- **Copy card number** — inline button for easy copy
- **Admin panel** — filter, search, export CSV
- **Docker** — one command deploy
- **Admin approve/reject** volunteers via Telegram buttons

## 🗺️ Regions & Limits

Configured in `.env`:
| Region | Participants | Volunteers |
|--------|-------------|------------|
| Нукус | 50 | 10 |
| Навои | 50 | 10 |
| Ташкент | 100 | 20 |
| Қашқадарё | 50 | 10 |
| Фарғона | 50 | 10 |
| Самарқанд | 50 | 10 |
