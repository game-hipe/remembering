import random
from string import Template

from aiogram.types import Message
from aiogram.filters import Command

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from .base import BaseRouter
from ...core import config
from ...core.entites import OutputMemory

FIND_TEXT = Template(
    "<b>Найдено ${count} количество напоминаний</b>\n"
    "<b>Напоминании:</b>\n"
    "${items}\n\n"
    "<code>${citate}</code>"
)

class ShowMemory(BaseRouter):
    def connect_routers(self):
        self.router.message.register(
            self.show_memory,
            Command("showmemory")
        )
        
    async def show_memory(self, msg: Message):
        response = await self.manager.get_memories(msg.chat.id)
        
        if response.success:
            await msg.answer(
                FIND_TEXT.substitute(
                    count = len(response.item),
                    items = '\n'.join(f"{index}. {item.title}" for index, item in enumerate(response.item, 1)),
                    citate = random.choice(config.citates).strip()
                ),
                reply_markup = self._generate_keyboard(response.item)
            )
        else:
            await msg.answer(
                "<b>Не удалось получить данные... (╥﹏╥)</b>\n\nПопробуйте позже!"
            )
            
    def _generate_keyboard(self, items: list[OutputMemory], max_length: int = 3):
        inline_keyboard = []
        keybard = []
        
        for indx, item in enumerate(items, 1):
            if not indx % max_length:
                inline_keyboard.append(
                    keybard
                )
                keybard.clear()
                continue
            
            keybard.append(
                InlineKeyboardButton(
                    text = item.title,
                    callback_data = f"get-memory-{item.id}"
                )
            )
        if keybard:
            inline_keyboard.append(
                keybard
            )
            
        return InlineKeyboardMarkup(
            inline_keyboard = inline_keyboard
        )