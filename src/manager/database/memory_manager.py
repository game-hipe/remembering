from sqlalchemy import select

from .base import BaseDataBaseManager, _Memory
from ...core import OutputMemory, BaseResponse, Memory


class MemoryManager(BaseDataBaseManager):
    """
    Менеджер для работы с воспоминаниями пользователей в базе данных.

    Наследует функциональность BaseDataBaseManager для преобразования объектов
    и предоставляет методы для добавления, удаления и получения воспоминаний.
    Все операции выполняются асинхронно через SQLAlchemy ORM.
    """

    async def add_memory(
        self, memory: _Memory, user_id: int
    ) -> BaseResponse[OutputMemory]:
        """
        Добавляет новое воспоминание в базу данных для указанного пользователя.

        Создаёт ORM-объект воспоминания, сохраняет его в БД и возвращает
        объект вывода с заполненным ID. Использует транзакцию для обеспечения целостности.

        :param memory: Объект воспоминания (TextMemory, PhotoMemory или VideoMemory)
        :type memory: _Memory
        :param user_id: Идентификатор пользователя в базе данных
        :type user_id: int
        :return: Объект ответа с результатом операции и данными о сохранённом воспоминании
        :rtype: BaseResponse[OutputMemory]
        """
        async with self.Session() as session:
            async with session.begin():
                data_memory = self._build_memory(memory, user_id)

                session.add(data_memory)
                await session.flush()

                return BaseResponse(
                    success=True,
                    message=f"Воспоминание типа '{data_memory.type}' было добавлено",
                    item=self._build_memory(data_memory, None),
                )

    async def delete_memory(self, memory_id: int) -> BaseResponse[bool]:
        """
        Удаляет воспоминание по его идентификатору.

        Находит воспоминание в базе данных и удаляет его в рамках транзакции.
        Возвращает статус операции.

        :param memory_id: Идентификатор воспоминания в базе данных
        :type memory_id: int
        :return: Объект ответа с флагом успеха и булевым результатом
        :rtype: BaseResponse[bool]
        """
        async with self.Session() as session:
            async with session.begin():
                memory = await session.get(Memory, memory_id)
                if memory:
                    await session.delete(memory)
                    return BaseResponse(
                        success=True, message="Воспоминание удалено", item=True
                    )
                return BaseResponse(
                    success=False, message="Воспоминание не найдено", item=False
                )

    async def get_memorys(self, user_id: int) -> BaseResponse[list[OutputMemory]]:
        """
        Получает список всех воспоминаний для указанного пользователя.

        Выполняет запрос к базе данных с фильтрацией по user_id и преобразует
        результат в список объектов OutputMemory.

        :param user_id: Идентификатор пользователя в базе данных
        :type user_id: int
        :return: Объект ответа с результатом и списком воспоминаний (возможно пустым)
        :rtype: BaseResponse[list[OutputMemory]]
        """
        async with self.Session() as session:
            memories = await session.scalars(
                select(Memory).where(Memory.user_id == user_id)
            )

            memory_list = [self._build_memory(memory, None) for memory in memories]
            if memory_list:
                return BaseResponse(
                    success=True, message="Воспоминания найдены", item=memory_list
                )
            return BaseResponse(
                success=False, message="Воспоминания не найдены", item=[]
            )

    async def get_memory(self, memory_id: int) -> BaseResponse[OutputMemory | None]:
        """
        Получает данные воспоминания по его идентификатору.

        Выполняет поиск воспоминания в базе данных и возвращает его данные
        в формате OutputMemory.

        :param memory_id: Идентификатор воспоминания в базе данных
        :type memory_id: int
        :return: Объект ответа с результатом и данными воспоминания (или None, если не найдено)
        :rtype: BaseResponse[OutputMemory | None]
        """
        async with self.Session() as session:
            memory = await session.get(Memory, memory_id)
            if memory:
                return BaseResponse(
                    success=True,
                    message="Воспоминание найдено",
                    item=self._build_memory(memory, None),
                )
            return BaseResponse(
                success=False, message="Воспоминание не найдено", item=None
            )
