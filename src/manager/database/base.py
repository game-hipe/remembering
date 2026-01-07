from typing import TypeAlias, overload
from sqlalchemy.ext.asyncio import (
    AsyncSession, 
    async_sessionmaker, 
    AsyncEngine
)

from ...core import TextMemory, PhotoMemory, VideoMemory, OutputMemory
from ...core import BaseUser, OutputUser
from ...core import User, Memeory

_Memory: TypeAlias = TextMemory | PhotoMemory | VideoMemory

class BaseDataBaseManager:
    def __init__(
        self,
        engine: AsyncEngine
    ):
        self.engine = engine
        self.Session: async_sessionmaker[AsyncSession] = async_sessionmaker(
            engine
        )
                
    @overload
    def _build_user(self, user: BaseUser) -> User: ...
    @overload
    def _build_user(self, user: User) -> OutputUser: ...
    
    def _build_user(self, user: User | OutputUser) -> User | OutputUser:
        if isinstance(user, User):
            return OutputUser(
                name = user.name,
                chat_id = user.chat_id,
                interval = user.interval,
                id = user.id
            )
        elif isinstance(user, BaseUser):
            return User(
                name = user.name,
                chat_id = user.chat_id,
                interval = user.interval
            )
        raise TypeError(
            f"Неподдерживаемый тип данных {type(user).__name__}"
        )
        
    @overload
    def _build_memory(self, memory: _Memory, user_id: int) -> Memeory: ...
    @overload
    def _build_memory(self, memory: Memeory, user_id: None) -> OutputMemory: ...
    
    def _build_memory(self, memory: Memeory | _Memory, user_id: int | None = None) -> OutputMemory | Memeory:
        if isinstance(memory, Memeory):
            return OutputMemory(
                id = memory.id,
                title = memory.title,
                content = memory.content,
                type = memory.type,
                user_id = memory.user_id,
                item = memory.item
            )
        elif isinstance(memory, self.__get_memory_args()):
            return Memeory(
                title = memory.title,
                content = memory.content,
                type = memory.type,
                user_id = user_id,
                item = str(memory.item.absolute()) if hasattr(memory, 'item') else None
            )
        else:
            raise TypeError(f"Тип воспоминаний {type(memory)} неподдерживается")
    
    @staticmethod
    def __get_memory_args():
        return _Memory.__args__