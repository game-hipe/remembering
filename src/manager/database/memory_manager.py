from sqlalchemy import select

from .base import BaseDataBaseManager, _Memory
from ...core import OutputMemory, BaseResponse, Memeory


class MemoryManager(BaseDataBaseManager):
    """Класс для управления воспоминаниями пользователей"""
    
    async def add_memory(self, memory: _Memory, user_id: int) -> BaseResponse[OutputMemory]:
        async with self.Session() as session:
            async with session.begin():
                data_memory = self._build_memory(memory, user_id)
                
                session.add(data_memory)
                await session.flush()
                
                return BaseResponse(
                    success = True,
                    message = f"Воспоминания типа '{data_memory.type}', был добавлен",
                    item = self._build_memory(data_memory, None)
                )
                
    async def delete_memory(self, memory_id: int) -> BaseResponse[bool]:
        async with self.Session() as session:
            async with session.begin():
                memory = await session.get(Memeory, memory_id)
                if memory:
                    await session.delete(memory)
                    return BaseResponse(
                        success=True, 
                        message="Воспоминания удалено", 
                        item=True
                    )
                return BaseResponse(
                    success=False, 
                    message="Воспоминания не найдено", 
                    item=False
                )
                
    async def get_memory(self, user_id: int) -> BaseResponse[list[OutputMemory]]:
        async with self.Session() as session:
                memories = await session.scalars(
                    select(Memeory).where(Memeory.user_id == user_id)
                )
                
                if memories:
                    return BaseResponse(
                        success=True, 
                        message="Воспоминания найдены", 
                        item=[self._build_memory(memory, None) for memory in memories]
                    )
                return BaseResponse(success=False, message="Воспоминания не найдены", item=[])