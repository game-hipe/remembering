from sqlalchemy.ext.asyncio import AsyncEngine
from loguru import logger

from .database import UserManager, MemoryManager, _Memory
from ..core import BaseUser, BaseResponse, OutputUser, OutputMemory


class Memories:
    """
    Основной класс бизнес-логики приложения для управления пользователями и их воспоминаниями.

    Инкапсулирует взаимодействие с менеджерами пользователей и воспоминаний,
    обеспечивая высокоуровневые операции: добавление пользователя, добавление воспоминаний,
    получение списка воспоминаний. Работает с асинхронным движком базы данных.

    :param engine: Асинхронный движок SQLAlchemy для подключения к базе данных
    :type engine: AsyncEngine
    """

    def __init__(self, engine: AsyncEngine):
        self.engine = engine
        self.user_manager = UserManager(engine)
        self.memory_manager = MemoryManager(engine)

    async def add_user(
        self, chat_id: int, name: str, interval: int = 300
    ) -> BaseResponse[OutputUser | None]:
        """
        Добавляет нового пользователя в систему, если он ещё не существует.

        Выполняет логирование попытки, создаёт объект пользователя и передаёт его
        в UserManager. При успехе возвращает данные о пользователе.

        :param chat_id: Уникальный идентификатор чата в Telegram
        :type chat_id: int
        :param name: Имя пользователя
        :type name: str
        :param interval: Интервал в секундах для напоминаний (по умолчанию 300)
        :type interval: int, optional
        :return: Объект ответа с результатом операции и данными пользователя (или None при ошибке)
        :rtype: BaseResponse[OutputUser | None]
        """
        logger.info(
            "Попытка добавить пользователя (chat_id={}, name={}, interval={})".format(
                chat_id, name, interval
            )
        )
        try:
            result = await self.user_manager.add_user(
                BaseUser(name=name, chat_id=chat_id, interval=interval)
            )
            if result.success:
                logger.success(
                    f"Успешно удалось добавить пользователя (user_id={result.item.id}, message={result.message})"
                )
            return result
        except Exception as e:
            return BaseResponse(
                success=False,
                message=f"Ошибка во время добавления пользователя {e}",
                item=None,
            )

    async def add_memory(
        self, chat_id: int, memory: _Memory
    ) -> BaseResponse[OutputMemory | None]:
        """
        Добавляет новое воспоминание для пользователя по его chat_id.

        Сначала ищет пользователя в системе, затем передаёт воспоминание в MemoryManager.
        Логирует ход выполнения операции.

        :param chat_id: Уникальный идентификатор чата в Telegram
        :type chat_id: int
        :param memory: Объект воспоминания (текстового, фото или видео типа)
        :type memory: _Memory
        :return: Объект ответа с результатом операции и данными о воспоминании (или None при ошибке)
        :rtype: BaseResponse[OutputMemory | None]
        """
        logger.info(
            "Попытка добавить память (chat_id={}, memory-title={})".format(
                chat_id, memory.title
            )
        )
        try:
            if user := await self.user_manager.get_user(chat_id):
                if not user.success:
                    logger.warning(
                        "Пользователь не найден (chat_id={})".format(chat_id)
                        if user.success
                        else f"Ошибка во время добавления памяти (message={user.message})"
                    )
                    return BaseResponse(success=False, message=user.message, item=None)
                result = await self.memory_manager.add_memory(memory, user.item.id)
                logger.success(
                    f"Успешно удалось добавить память (user_id={user.item.id}, message={result.message})"
                )
                return result
        except Exception as e:
            logger.error(f"Ошибка во время добавления памяти (error = {e})")
            return BaseResponse(
                success=False,
                message=f"Ошибка во время добавления памяти {e}",
                item=None,
            )

    async def get_memories(
        self, chat_id: int
    ) -> BaseResponse[list[OutputMemory] | None]:
        """
        Получает список всех воспоминаний для пользователя по его chat_id.

        Сначала проверяет существование пользователя, затем запрашивает
        все его воспоминания через MemoryManager.

        :param chat_id: Уникальный идентификатор чата в Telegram
        :type chat_id: int
        :return: Объект ответа с результатом и списком воспоминаний (или None при ошибке)
        :rtype: BaseResponse[list[OutputMemory] | None]
        """
        logger.info("Попытка получить память (chat_id={})".format(chat_id))
        try:
            if user := await self.user_manager.get_user(chat_id):
                if not user.success:
                    logger.warning(
                        "Пользователь не найден (chat_id={})".format(chat_id)
                        if user.success
                        else f"Ошибка во время получение памяти (message={user.message})"
                    )
                    return BaseResponse(success=False, message=user.message, item=None)
                result = await self.memory_manager.get_memory(user.item.id)
                logger.success(
                    f"Успешно удалось получить память (user_id={user.item.id}, message={result.message})"
                )
                return result
        except Exception as e:
            logger.error(f"Ошибка во время добавления памяти (error = {e})")
            return BaseResponse(
                success=False,
                message=f"Ошибка во время добавления памяти {e}",
                item=None,
            )
