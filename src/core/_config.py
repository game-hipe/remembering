import os
import json

from pathlib import Path
from dataclasses import dataclass

from dotenv import load_dotenv

__all__ = ["config"]

load_dotenv()


@dataclass
class Config:
    BOT_TOKEN: str = os.getenv("BOT_TOKEN")
    DB_URL: str = os.getenv("DB_URL")

    PATH_IMAGE: Path = Path(os.getenv("PATH_IMAGE"))
    PATH_VIDEO: Path = Path(os.getenv("PATH_VIDEO"))
    INTERVAL: int = int(os.getenv("INTERVAL", 300))

    CITATE: Path = Path("src/bot/citates.json")

    def __post_init__(self):
        self.setup()

        if not self.BOT_TOKEN:
            raise ValueError("BOT_TOKEN Не может быть пуст!")

    def setup(self):
        self.PATH_IMAGE.mkdir(parents=True, exist_ok=True)
        self.PATH_VIDEO.mkdir(parents=True, exist_ok=True)

    @property
    def citates(self) -> list[str]:
        try:
            with self.CITATE.open("r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []


config = Config()
