from sqlalchemy import Column, Integer, BigInteger, String, Date, DateTime, Enum
from sqlalchemy.sql import func
from bot.database import Base
import enum


class ParticipantStatus(str, enum.Enum):
    pending = "pending"
    approved = "approved"
    rejected = "rejected"


class Participant(Base):
    __tablename__ = "participants"

    id = Column(Integer, primary_key=True, autoincrement=True)
    telegram_id = Column(BigInteger, nullable=False, unique=True, index=True)
    language = Column(String(5), nullable=False, default="ru")
    last_name = Column(String(100), nullable=False)
    first_name = Column(String(100), nullable=False)
    phone = Column(String(30), nullable=False)
    username = Column(String(100), nullable=True)
    birth_date = Column(Date, nullable=False)
    region = Column(String(50), nullable=False)
    card_number_shown = Column(String(20), nullable=True)
    receipt_file_id = Column(String(200), nullable=True)
    status = Column(
        Enum(ParticipantStatus),
        nullable=False,
        default=ParticipantStatus.pending,
    )
    created_at = Column(DateTime(timezone=True), server_default=func.now())
