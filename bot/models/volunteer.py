from sqlalchemy import Column, Integer, BigInteger, String, Date, DateTime, Enum
from sqlalchemy.sql import func
from bot.database import Base
import enum


class VolunteerStatus(str, enum.Enum):
    pending = "pending"
    approved = "approved"
    rejected = "rejected"


class Volunteer(Base):
    __tablename__ = "volunteers"

    id = Column(Integer, primary_key=True, autoincrement=True)
    telegram_id = Column(BigInteger, nullable=False, unique=True, index=True)
    language = Column(String(5), nullable=False, default="ru")
    photo_file_id = Column(String(200), nullable=False)
    full_name = Column(String(200), nullable=False)
    phone = Column(String(30), nullable=False)
    username = Column(String(100), nullable=True)
    birth_date = Column(Date, nullable=False)
    region = Column(String(50), nullable=False)
    status = Column(
        Enum(VolunteerStatus),
        nullable=False,
        default=VolunteerStatus.pending,
    )
    created_at = Column(DateTime(timezone=True), server_default=func.now())
