from aiogram.fsm.storage.memory import MemoryStorage
from aiogram import Bot, Dispatcher
from aiogram.types import BotCommand
from aiogram.client.default import DefaultBotProperties

from loguru import logger

from ..manager.memories import Memories
from ..core import config
from .routers import setup
from .middleware import get_middleware

async def set_commands(bot: Bot):
    logger.info("Инициализация команд")
    command = [
        BotCommand(command = "addmemory", description = "Добавить напоминание"),
        BotCommand(command = "showmemory", description = "Показать напоминания"),
        BotCommand(command = "deletememory", description = "Удалить напоминание"),
        BotCommand(command = "help", description = "Помощь"),
        BotCommand(command = "start", description = "Начать работу с ботом")
    ]
    await bot.set_my_commands(command)
    
async def setup_bot(manager: Memories) -> tuple[Bot, Dispatcher]:
    logger.info("Настройка бота")
    
    bot = Bot(token = config.BOT_TOKEN, default = DefaultBotProperties(parse_mode = "HTML"))
    
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)
    middleware = get_middleware(manager)
        
    dp.message.middleware(middleware)
    dp.callback_query.middleware(middleware)
    
    dp.include_routers(*setup(manager))
    
    await set_commands(bot)
    
    return bot, dp

async def run_bot(manager: Memories):
    logger.info("Запуск бота...")
    bot, dp = await setup_bot(manager)
    
    logger.success("Бот запущен")
    await dp.start_polling(bot)