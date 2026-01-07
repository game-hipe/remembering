from sqlalchemy.ext.asyncio import AsyncEngine
from loguru import logger

from .database import UserManager, MemoryManager, _Memory
from ..core import BaseUser, BaseResponse, OutputUser, OutputMemory

class Memories:
    def __init__(self, engine: AsyncEngine):
        self.engine = engine
        self.user_manager = UserManager(engine)
        self.memory_manager = MemoryManager(engine)
        
    async def add_user(self, chat_id: int, name: str, interval: int = 300) -> BaseResponse[OutputUser | None]:
        """Добавляет нового пользователя

        Args:
            chat_id (int): chat-id в ТГ
            name (str): Имя пользователя
            interval (int, optional): Через, сколько секунд будут напоминание. Базовое значение 300.

        Returns:
            BaseResponse[OutputUser | None]: Возращает результат в специальном формате, вмесие с информацией об пользователе
        """
        logger.info("Попытка добавить пользователя (chat_id={}, name={}, interval={})".format(
            chat_id,
            name,
            interval
        ))
        try:
            result = await self.user_manager.add_user(
                BaseUser(
                    name = name,
                    chat_id = chat_id,
                    interval = interval
                )
            )
            if result.success:
                logger.success(f"Успешно удалось добавить пользователя (user_id={result.item.id}, message={result.message})")
                
            return result
                
        except Exception as e:
            return BaseResponse(
                success = False,
                message = f"Ошибка во время добавления пользователя {e}",
                item = None
            )
            
    async def add_memory(self, chat_id: int, memory: _Memory) -> BaseResponse[OutputMemory | None]:
        """Добавитт напоминание

        Args:
            chat_id (int): ID тг чата
            memory (_Memory): Воспоминание

        Returns:
            BaseResponse[OutputMemory | None]: Возвращает результат в специальном формате, вмесие с информацией о памяти
        """
        logger.info("Попытка добавить память (chat_id={}, memory-title={})".format(
            chat_id,
            memory.title
        ))
        try:
            if user := await self.user_manager.get_user(chat_id):
                if not user.success:
                    logger.warning(
                        "Пользователь не найден (chat_id={})".format(chat_id) if user.success else f"Ошибка во время добавления памяти (message={user.message})"
                    )
                    return BaseResponse(
                        success = False,
                        message = user.message,
                        item = None
                    )
                result = await self.memory_manager.add_memory(memory, user.item.id)
                logger.success(f"Успешно удалось добавить память (user_id={user.item.id}, message={result.message})")
                return result
                    
        except Exception as e:
            logger.error(f"Ошибка во время добавления памяти (error = {e})")
            return BaseResponse(
                success = False,
                message = f"Ошибка во время добавления памяти {e}",
                item = None
            )
            
    async def get_memories(self, chat_id: int) -> BaseResponse[list[OutputMemory] | None]:
        """Получить всю память 1 пользователя

        Args:
            chat_id (int): ID тг чата

        Returns:
            BaseResponse[list[OutputMemory] | None]: Возвращает результат в специальном формате, вмесие с информацией о всех напоминаниях.
        """
        logger.info("Попытка получить память (chat_id={})".format(chat_id))
        try:
            if user := await self.user_manager.get_user(chat_id):
                if not user.success:
                    logger.warning(
                        "Пользователь не найден (chat_id={})".format(chat_id) if user.success else f"Ошибка во время получение памяти (message={user.message})"
                    )
                    return BaseResponse(
                        success = False,
                        message = user.message,
                        item = None
                    )
                    
                result = await self.memory_manager.get_memory(user.item.id)
                logger.success(f"Успешно удалось добавить память (user_id={user.item.id}, message={result.message})")
                return result
            
        except Exception as e:
            logger.error(f"Ошибка во время добавления памяти (error = {e})")
            return BaseResponse(
                success = False,
                message = f"Ошибка во время добавления памяти {e}",
                item = None
            )