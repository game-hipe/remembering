from sqlalchemy import select

from ...core import BaseUser, OutputUser, BaseResponse
from ...core import User
from .base import BaseDataBaseManager


class UserManager(BaseDataBaseManager):
    """Класс для управление пользователями"""
    
    async def add_user(self, user: BaseUser) -> BaseResponse[OutputUser]:
        async with self.Session() as session:
            async with session.begin():
                
                if finded_user := await session.scalar(select(User).where(User.chat_id == user.chat_id)):
                    return BaseResponse(
                        success = True,
                        message = "Данный пользователь уже находится в базе данных",
                        item = self._build_user(finded_user)
                    )
                    
                user = self._build_user(user)
                session.add(user)
                await session.flush()
                
                return BaseResponse(
                    success = True,
                    message = "Пользователь успешно добавлен в базу данных",
                    item = self._build_user(user)
                )
                
    async def get_user(self, chat_id: int) -> BaseResponse[OutputUser | None]:
        async with self.Session() as session:
            if user :=  await session.scalar(select(User).where(User.chat_id == chat_id)):
                return BaseResponse(
                    success = True,
                    message = "Пользователь найден",
                    item = self._build_user(user)
                )
            return BaseResponse(
                success = False,
                message = "Пользователь не найден",
                item = None
            )
            
    async def delete_user(self, chat_id: int) -> BaseResponse[bool]:
        async with self.Session() as session:
            async with session.begin():
                if user := await session.scalar(select(User).where(User.chat_id == chat_id)):
                    session.delete(user)
                    return BaseResponse(
                        success = True,
                        message = "Пользователь удален",
                        item = True
                    )
                return BaseResponse(
                    success = False,
                    message = "Пользователь не найден",
                    item = False
                )
                
    async def _user_in_base(self, chat_id: int) -> bool:
        async with self.Session() as session:
            async with session.begin():
                if await session.scalar(select(User).where(User.chat_id == chat_id)):
                    return True
                return False