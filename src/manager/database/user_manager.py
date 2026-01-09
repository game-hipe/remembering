from typing import AsyncGenerator

from sqlalchemy import select

from ...core import BaseUser, OutputUser, BaseResponse
from ...core import User
from .base import BaseDataBaseManager


class UserManager(BaseDataBaseManager):
    """
    Менеджер для управления пользователями в базе данных.

    Предоставляет методы для добавления, получения, удаления и проверки
    наличия пользователей в системе. Наследует функциональность BaseDataBaseManager
    для работы с сессиями и преобразования объектов моделей.
    """

    async def add_user(self, user: BaseUser) -> BaseResponse[OutputUser]:
        """
        Добавляет нового пользователя в базу данных, если он ещё не существует.

        Проверяет наличие пользователя по chat_id. Если пользователь уже есть,
        возвращает его данные. В противном случае — создаёт новую запись.

        :param user: Объект данных пользователя (BaseUser) с именем, chat_id и интервалом
        :type user: BaseUser
        :return: Объект ответа с результатом операции и данными пользователя
        :rtype: BaseResponse[OutputUser]
        """
        async with self.Session() as session:
            async with session.begin():
                if finded_user := await session.scalar(
                    select(User).where(User.chat_id == user.chat_id)
                ):
                    return BaseResponse(
                        success=True,
                        message="Данный пользователь уже находится в базе данных",
                        item=self._build_user(finded_user),
                    )
                create_user = self._build_user(user)
                session.add(create_user)
                await session.flush()

                return BaseResponse(
                    success=True,
                    message="Пользователь успешно добавлен в базу данных",
                    item=OutputUser(
                        id=create_user.id,
                        name=create_user.name,
                        chat_id=create_user.chat_id,
                        interval=create_user.interval,
                    ),
                )

    async def get_user(self, chat_id: int) -> BaseResponse[OutputUser | None]:
        """
        Получает данные пользователя по его chat_id.

        Выполняет поиск пользователя в базе данных и при наличии
        возвращает его данные в формате OutputUser.

        :param chat_id: Уникальный идентификатор чата в Telegram
        :type chat_id: int
        :return: Объект ответа с результатом и данными пользователя (или None, если не найден)
        :rtype: BaseResponse[OutputUser | None]
        """
        async with self.Session() as session:
            if user := await session.scalar(
                select(User).where(User.chat_id == chat_id)
            ):
                return BaseResponse(
                    success=True,
                    message="Пользователь найден",
                    item=self._build_user(user),
                )
            return BaseResponse(
                success=False, message="Пользователь не найден", item=None
            )

    async def delete_user(self, chat_id: int) -> BaseResponse[bool]:
        """
        Удаляет пользователя из базы данных по его chat_id.

        Выполняет удаление в рамках транзакции. Возвращает статус операции.

        :param chat_id: Уникальный идентификатор чата в Telegram
        :type chat_id: int
        :return: Объект ответа с флагом успеха и булевым значением результата
        :rtype: BaseResponse[bool]
        """
        async with self.Session() as session:
            async with session.begin():
                if user := await session.scalar(
                    select(User).where(User.chat_id == chat_id)
                ):
                    session.delete(user)
                    return BaseResponse(
                        success=True, message="Пользователь удален", item=True
                    )
                return BaseResponse(
                    success=False, message="Пользователь не найден", item=False
                )

    async def get_users(
        self, batch_size: int = 100, start_id: int = 0
    ) -> AsyncGenerator[BaseResponse[list[OutputUser]]]:
        """
        Получает список всех пользователей из базы данных.

        :param batch_size: Размер выборки за один раз (по умолчанию 100)
        :type batch_size: int

        :param start_id: Начальный ID для выборки (по умолчанию 0)
        :type start_id: int

        :return: Объект ответа с результатом и списком пользователей
        :rtype: BaseResponse[list[OutputUser]]

        """
        async with self.Session() as session:
            while True:
                # Выбираем пакет пользователей
                query = (
                    select(User)
                    .where(User.id >= start_id)
                    .order_by(User.id)
                    .limit(batch_size)
                )
                result = await session.execute(query)
                users_list = list(result.scalars().unique())

                if not users_list:
                    # Больше пользователей нет
                    yield BaseResponse(
                        success=True, message="Все пользователи получены", item=[]
                    )
                    break

                # Получаем последний ID для следующего пакета
                last_id = users_list[-1].id
                start_id = last_id + 1
                yield BaseResponse(
                    success=True,
                    message=f"Получено {len(users_list)} пользователей",
                    item=[self._build_user(user) for user in users_list],
                )

    async def _user_in_base(self, chat_id: int) -> bool:
        """
        Проверяет, существует ли пользователь в базе данных.

        Выполняет запрос к БД и возвращает булево значение наличия записи.

        :param chat_id: Уникальный идентификатор чата в Telegram
        :type chat_id: int
        :return: True, если пользователь найден, иначе False
        :rtype: bool
        """
        async with self.Session() as session:
            async with session.begin():
                if await session.scalar(select(User).where(User.chat_id == chat_id)):
                    return True
                return False