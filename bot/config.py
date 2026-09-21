from pydantic_settings import BaseSettings
from typing import Dict


class Settings(BaseSettings):
    # Bot
    BOT_TOKEN: str
    ADMIN_CHAT_ID: int

    # Database
    DATABASE_URL: str

    # Card
    CARD_NUMBER: str = "1234567890123456"
    CARD_HOLDER: str = "ISKANDER CF"

    # Admin panel
    SECRET_KEY: str = "change-me"
    ADMIN_USERNAME: str = "admin"
    ADMIN_PASSWORD: str = "admin123"

    # Region limits participants
    NUKUS_LIMIT_P: int = 50
    NAVOI_LIMIT_P: int = 50
    TASHKENT_LIMIT_P: int = 100
    KASHKADARYA_LIMIT_P: int = 50
    FERGANA_LIMIT_P: int = 50
    SAMARKAND_LIMIT_P: int = 50

    # Region limits volunteers
    NUKUS_LIMIT_V: int = 10
    NAVOI_LIMIT_V: int = 10
    TASHKENT_LIMIT_V: int = 20
    KASHKADARYA_LIMIT_V: int = 10
    FERGANA_LIMIT_V: int = 10
    SAMARKAND_LIMIT_V: int = 10

    @property
    def region_limits_participants(self) -> Dict[str, int]:
        return {
            "Нукус": self.NUKUS_LIMIT_P,
            "Навои": self.NAVOI_LIMIT_P,
            "Ташкент": self.TASHKENT_LIMIT_P,
            "Қашқадарё": self.KASHKADARYA_LIMIT_P,
            "Фарғона": self.FERGANA_LIMIT_P,
            "Самарқанд": self.SAMARKAND_LIMIT_P,
        }

    @property
    def region_limits_volunteers(self) -> Dict[str, int]:
        return {
            "Нукус": self.NUKUS_LIMIT_V,
            "Навои": self.NAVOI_LIMIT_V,
            "Ташкент": self.TASHKENT_LIMIT_V,
            "Қашқадарё": self.KASHKADARYA_LIMIT_V,
            "Фарғона": self.FERGANA_LIMIT_V,
            "Самарқанд": self.SAMARKAND_LIMIT_V,
        }

    class Config:
        env_file = ".env"


settings = Settings()
