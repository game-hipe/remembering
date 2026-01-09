from typing import AsyncGenerator
from datetime import timedelta

from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker
from loguru import logger

from .tools import except_handler
from .database import UserManager, MemoryManager, _Memory
from ..core import BaseUser, BaseResponse, OutputUser, OutputMemory, Memory


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

        self.Session = async_sessionmaker(engine)

    # @except_handler
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
        result = await self.user_manager.add_user(
            BaseUser(name=name, chat_id=chat_id, interval=interval)
        )
        if result.success:
            logger.success(
                f"Успешно удалось добавить пользователя (user_id={result.item.id}, message={result.message})"
            )
        return result

    @except_handler
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

    @except_handler
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
        user = await self.user_manager.get_user(chat_id)
        if not user.success:
            logger.warning(
                "Пользователь не найден (chat_id={})".format(chat_id)
                if user.success
                else f"Ошибка во время получение памяти (message={user.message})"
            )
            return BaseResponse(success=False, message=user.message, item=None)
        result = await self.memory_manager.get_memorys(user.item.id)
        logger.success(
            f"Успешно удалось получить память (user_id={user.item.id}, message={result.message})"
        )
        return result

    @except_handler
    async def get_memory(self, memory_id: int) -> BaseResponse[OutputMemory | None]:
        """
        Получает воспоминание по его ID.

        :param memory_id: Уникальный идентификатор воспоминания
        :type memory_id: int

        :return: Объект ответа с результатом операции и данными о воспоминании (или None при ошибке или если воспоминание не найдено)
        :rtype: BaseResponse[OutputMemory | None]
        """
        logger.info("Попытка получить память (memory_id={})".format(memory_id))
        memory = await self.memory_manager.get_memory(memory_id)
        if not memory.success:
            logger.warning(
                "Память не найдена (memory_id={})".format(memory_id)
                if memory.success
                else f"Ошибка во время получение памяти (message={memory.message})"
            )
            return BaseResponse(success=False, message=memory.message, item=None)
        logger.success(
            "Успешно удалось получить память (memory_id={})".format(memory_id)
        )
        return memory

    @except_handler
    async def delete_memory(self, memory_id: int) -> BaseResponse[bool]:
        """
        Удаляет воспоминание по его ID.

        :param memory_id: Уникальный идентификатор воспоминания
        :type memory_id: int

        :return: Объект ответа с результатом операции и булевым значением (True при успешном удалении)
        :rtype: BaseResponse[bool]
        """
        logger.info("Попытка удалить память (memory_id={})".format(memory_id))
        memory = await self.memory_manager.delete_memory(memory_id)
        if not memory.success:
            logger.warning(
                "Память не найдена (memory_id={})".format(memory_id)
                if memory.success
                else f"Ошибка во время удаления памяти (message={memory.message})"
            )
            return BaseResponse(success=False, message=memory.message, item=False)
        logger.success(
            "Успешно удалось удалить память (memory_id={})".format(memory_id)
        )
        return memory

    @except_handler
    async def get_user(self, chat_id: int) -> BaseResponse[OutputUser]:
        """
        Получает пользователя по его chat_id.

        :param chat_id: Уникальный идентификатор чата в Telegram
        :type chat_id: int

        :retutrn: Объект ответа с результатом операции и данными о пользователе
        :rtype: BaseResponse[OutputUser]
        """
        logger.info("Попытка получить пользователя (chat_id={})".format(chat_id))
        user = await self.user_manager.get_user(chat_id)
        if not user.success:
            logger.warning("Пользователь не найден (chat_id={})".format(chat_id))
            return BaseResponse(success=False, message=user.message, item=None)
        logger.success(
            "Успешно удалось получить пользователя (chat_id={})".format(chat_id)
        )
        return user

    async def get_users(
        self, batch_size: int = 100
    ) -> AsyncGenerator[BaseResponse[list[OutputUser]]]:
        """
        Получает список всех пользователей.

        :param batch_size: Размер пакета для запроса пользователей (по умолчанию 100)
        :type batch_size: int

        :return: Объект ответа с результатом операции и списком пользователей
        :rtype: BaseResponse[list[OutputUser]]
        """
        logger.info("Попытка получить всех пользователей")
        try:
            async for users in self.user_manager.get_users(batch_size):
                if not users.item:
                    logger.info(users.message)
                    yield users
                    continue

                logger.info(
                    "Успешно удалось получить пользователей (count={})".format(
                        len(users.item)
                    )
                )

                yield users

        except Exception as e:
            logger.error(
                f"Ошибка во время получения всех пользователей (message={str(e)})"
            )
            yield BaseResponse(success=False, message=str(e), item=[])

    @except_handler
    async def add_time_to_memory(
        self, memory_id: int, seconds: int
    ) -> BaseResponse[bool]:
        """
        Добавляет указанное количество секунд к времени воспоминания.

        :param memory_id: Уникальный идентификатор воспоминания
        :type memory_id: int

        :param seconds: Количество секунд для добавления
        :type seconds: int

        :return: Объект ответа с результатом операции.
        :rtype: BaseResponse[bool]
        """
        logger.info(
            "Попытка добавить время к памяти (memory_id={}, seconds={})".format(
                memory_id, seconds
            )
        )
        async with self.Session() as session:
            async with session.begin():
                memory = await session.get(Memory, memory_id)
                if memory is None:
                    logger.warning("Память не найдена (memory_id={})".format(memory_id))
                    return BaseResponse(
                        success=True,
                        message=f"Память не найдена (memory_id={memory_id})",
                        item=False,
                    )

                memory.sent_at = memory.sent_at + timedelta(seconds=seconds)
                logger.success(
                    "Успешно добавлено время к памяти (memory_id={}, seconds={})".format(
                        memory_id, seconds
                    )
                )
                return BaseResponse(
                    success=True, message="Время успешно добавлено", item=True
                )
