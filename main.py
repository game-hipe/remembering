import asyncio

from sqlalchemy.ext.asyncio import create_async_engine
from src.manager.memories import Memories

from src.core.entites.models import Base
from src.bot.bot import run_bot
from src.core import config

from loguru import logger


async def main():
    engine = create_async_engine(config.DB_URL)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    api = Memories(engine)

    try:
        await run_bot(api)
    except Exception:
        raise
    finally:
        await engine.dispose()


if __name__ == "__main__":
    try:
        asyncio.run(main())

    except KeyboardInterrupt:
        logger.info("Программа остановлена пользователем")

    except Exception as e:
        logger.critical(f"ОШИБКА: {e}")

    finally:
        logger.info("Выход из программы...")
