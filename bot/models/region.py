from sqlalchemy import Column, Integer, String
from bot.database import Base


REGIONS = ["Нукус", "Навои", "Ташкент", "Қашқадарё", "Фарғона", "Самарқанд"]


class RegionCapacity(Base):
    __tablename__ = "region_capacity"

    id = Column(Integer, primary_key=True, autoincrement=True)
    region_name = Column(String(50), nullable=False, unique=True, index=True)
    max_participants = Column(Integer, nullable=False, default=50)
    current_participants = Column(Integer, nullable=False, default=0)
    max_volunteers = Column(Integer, nullable=False, default=10)
    current_volunteers = Column(Integer, nullable=False, default=0)
