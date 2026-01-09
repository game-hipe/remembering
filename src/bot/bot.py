import asyncio

from aiogram.fsm.storage.memory import MemoryStorage
from aiogram import Bot, Dispatcher
from aiogram.types import BotCommand
from aiogram.client.default import DefaultBotProperties

from loguru import logger

from ..manager.memories import Memories
from ..core import config
from .routers import setup
from .middleware import get_middleware
from ..service.notification import Notification


async def set_commands(bot: Bot):
    """
    Устанавливает список команд бота, отображаемых в интерфейсе Telegram.

    Формирует и устанавливает меню команд с их описаниями, которое будет
    доступно пользователю при взаимодействии с ботом. Выполняется при запуске бота.

    :param bot: Экземпляр бота из библиотеки aiogram, через который выполняется установка команд
    :type bot: aiogram.Bot
    :return: None
    """
    logger.info("Инициализация команд")
    commands = [
        BotCommand(command="addmemory", description="Добавить напоминание"),
        BotCommand(command="showmemory", description="Показать напоминания"),
        BotCommand(command="start", description="Начать работу с ботом"),
        BotCommand(command="help", description="Помощь"),
        BotCommand(command="cancel", description="Сброс состояние"),
    ]
    await bot.set_my_commands(commands)


async def setup_bot(manager: Memories) -> tuple[Bot, Dispatcher]:
    """
    Настраивает и инициализирует экземпляры бота и диспетчера.

    Создаёт объект Bot с токеном из конфигурации и HTML-разметкой по умолчанию.
    Инициализирует диспетчер с хранилищем состояний в памяти, регистрирует middleware
    для передачи менеджера данных во все обработчики, подключает все маршрутизаторы
    и устанавливает список доступных команд бота.

    :param manager: Экземпляр менеджера для работы с воспоминаниями
    :type manager: Memories
    :return: Кортеж из настроенного объекта Bot и диспетчера Dispatcher
    :rtype: tuple[aiogram.Bot, aiogram.Dispatcher]
    """
    logger.info("Настройка бота")

    bot = Bot(token=config.BOT_TOKEN, default=DefaultBotProperties(parse_mode="HTML"))

    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)
    middleware = get_middleware(manager)

    dp.message.middleware(middleware)
    dp.callback_query.middleware(middleware)

    dp.include_routers(*setup(manager))

    await set_commands(bot)

    return bot, dp


async def run_bot(manager: Memories):
    """
    Запускает бота в режиме polling.

    Выполняет настройку бота и диспетчера через функцию setup_bot,
    логирует успешный запуск и начинает прослушивание обновлений от Telegram.

    :param manager: Экземпляр менеджера для управления воспоминаниями,
                    передаётся в настройку бота для интеграции бизнес-логики
    :type manager: Memories
    :return: None
    """
    logger.info("Запуск бота...")
    bot, dp = await setup_bot(manager)

    logger.success("Бот запущен")
    await asyncio.gather(dp.start_polling(bot), _run_service(manager, bot))


async def _run_service(manager: Memories, bot: Bot) -> None:
    """
    Точка запуска сервисов приложения.

    В текущей реализации запускает сервис уведомлений, отвечающий за
    планирование и отправку оповещений пользователям на основе управлителя воспоминаний.
    При необходимости сюда можно добавить другие фоновые сервисы или задачи.

    :param manager: Экземпляр класса управления воспоминаниями, используемый для получения данных.
    :type manager: Memories
    :param bot: Экземпляр бота из библиотеки aiogram, используемый для отправки сообщений.
    :type bot: Bot
    :return: Ничего не возвращает.
    :rtype: None
    """
    await Notification(manager, bot, interval=config.INTERVAL).start()