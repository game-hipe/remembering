from cachetools import TTLCache
from typing import Callable, Dict, Any, Awaitable

from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery, TelegramObject

from ..manager.memories import Memories


def get_middleware(memories: Memories):
    
    class RegistrationMiddleware(BaseMiddleware):
        def __init__(self):
            super().__init__()
            self.cache = TTLCache(maxsize = 65536, ttl=43200)
            
        async def __call__(
            self,
            handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
            event: TelegramObject,
            data: Dict[str, Any]
        ) -> Any:
            
            if isinstance(event, (Message, CallbackQuery)):
                user = event.from_user
                chat_id = event.chat.id if isinstance(event, Message) else event.message.chat.id
                if chat_id in self.cache:
                    return await handler(event, data)
                
                await memories.add_user(chat_id, user.first_name)
                self.cache[chat_id] = True
            
            # Продолжаем выполнение
            return await handler(event, data)
        
    return RegistrationMiddleware()