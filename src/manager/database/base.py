from typing import TypeAlias, overload
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, AsyncEngine

from ...core import TextMemory, PhotoMemory, VideoMemory, OutputMemory
from ...core import BaseUser, OutputUser
from ...core import User, Memory
from ...core import config

_Memory: TypeAlias = TextMemory | PhotoMemory | VideoMemory


class BaseDataBaseManager:
    """
    Базовый класс для управления взаимодействием с базой данных.

    Предоставляет общие методы для преобразования объектов модели
    между различными слоями приложения (например, из DTO в ORM и обратно).
    Использует асинхронный движок SQLAlchemy и фабрику сессий для работы с БД.

    :param engine: Асинхронный движок SQLAlchemy для подключения к базе данных
    :type engine: AsyncEngine
    """

    def __init__(self, engine: AsyncEngine):
        self.engine = engine
        self.Session: async_sessionmaker[AsyncSession] = async_sessionmaker(engine)

    @overload
    def _build_user(self, user: BaseUser) -> User:
        """
        Преобразует объект BaseUser (DTO) в ORM-модель User.

        :param user: Объект входных данных пользователя
        :return: Экземпляр ORM-модели User
        """

    @overload
    def _build_user(self, user: User) -> OutputUser:
        """
        Преобразует ORM-модель User в объект вывода OutputUser.

        :param user: Экземпляр ORM-модели User
        :return: Объект OutputUser для возврата в бизнес-логику
        """

    def _build_user(self, user: User | BaseUser) -> User | OutputUser:
        """
        Универсальный метод преобразования пользовательских объектов.

        В зависимости от типа входного объекта выполняет преобразование:
        - BaseUser -> User (для сохранения в БД)
        - User -> OutputUser (для возврата из БД)

        :param user: Входной объект пользователя (BaseUser или User)
        :type user: User | BaseUser
        :return: Преобразованный объект (User или OutputUser)
        :raises TypeError: Если передан неподдерживаемый тип
        """
        if isinstance(user, User):
            return OutputUser(
                name=user.name,
                chat_id=user.chat_id,
                interval=user.interval,
                id=user.id,
                memories=[self._build_memory(x, None) for x in user.memories],
            )
        elif isinstance(user, BaseUser):
            return User(name=user.name, chat_id=user.chat_id, interval=user.interval)
        raise TypeError(f"Неподдерживаемый тип данных {type(user).__name__}")

    @overload
    def _build_memory(self, memory: _Memory, user_id: int) -> Memory:
        """
        Преобразует объект _Memory (DTO) в ORM-модель Memory.

        :param memory: Объект воспоминания из бизнес-логики
        :param user_id: Идентификатор пользователя в БД
        :return: Экземпляр ORM-модели Memory, готовый к сохранению
        """

    @overload
    def _build_memory(self, memory: Memory, user_id: None) -> OutputMemory:
        """
        Преобразует ORM-модель Memory в объект вывода OutputMemory.

        :param memory: Экземпляр ORM-модели Memory из БД
        :param user_id: Должен быть None — параметр для перегрузки типов
        :return: Объект OutputMemory для возврата в бизнес-логику
        """

    def _build_memory(
        self, memory: Memory | _Memory, user_id: int | None = None
    ) -> OutputMemory | Memory:
        """
        Универсальный метод преобразования объектов воспоминаний.

        Выполняет преобразование:
        - _Memory -> Memory (с указанием user_id, для сохранения в БД)
        - Memory -> OutputMemory (при извлечении из БД)

        :param memory: Входной объект воспоминания
        :type memory: Memory | _Memory
        :param user_id: Идентификатор пользователя (только при создании ORM-объекта)
        :type user_id: int | None
        :return: Преобразованный объект воспоминания
        :raises TypeError: Если тип воспоминания не поддерживается
        """
        if isinstance(memory, Memory):
            return OutputMemory(
                id=memory.id,
                title=memory.title,
                content=memory.content,
                type=memory.type,
                user_id=memory.user_id,
                item=memory.item,
                remind_to=memory.sent_at.replace(
                    tzinfo = config.APP_TZ
                ),
            )
        elif isinstance(memory, self.__get_memory_args()):
            return Memory(
                title=memory.title,
                content=memory.content,
                type=memory.type,
                user_id=user_id,
                item=str(memory.item.absolute()) if hasattr(memory, "item") else None,
                sent_at=memory.remind_to
            )
        else:
            raise TypeError(f"Тип воспоминаний {type(memory)} неподдерживается")

    @staticmethod
    def __get_memory_args():
        """
        Возвращает типы, допустимые для поля _Memory (Union-типы из typing).

        Используется для проверки совместимости объектов при построении ORM-модели.

        :return: Кортеж типов, разрешённых для _Memory
        :rtype: tuple
        """
        return _Memory.__args__
