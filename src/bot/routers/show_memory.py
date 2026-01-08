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
    """
    Маршрутизатор для отображения списка воспоминаний пользователя.

    Обрабатывает команду /showmemory, получает список воспоминаний
    через менеджер и предоставляет пользователю интерактивную клавиатуру
    для выбора конкретного воспоминания.
    """

    def connect_routers(self):
        """
        Регистрирует обработчики команд для маршрутизатора.

        Настраивает обработку команды /showmemory.
        """
        self.router.message.register(self.show_memory, Command("showmemory"))

    async def show_memory(self, msg: Message):
        """
        Обрабатывает команду /showmemory и отображает список воспоминаний.

        Получает список воспоминаний пользователя через менеджер,
        формирует ответное сообщение со списком и случайной цитатой,
        прикрепляет клавиатуру с выбором воспоминаний.

        :param msg: Входящее сообщение от пользователя
        """
        response = await self.manager.get_memories(msg.chat.id)

        if response.success:
            await msg.answer(
                FIND_TEXT.substitute(
                    count=len(response.item),
                    items="\n".join(
                        f"{index}. {item.title}"
                        for index, item in enumerate(response.item, 1)
                    ),
                    citate=random.choice(config.citates).strip(),
                ),
                reply_markup=self._generate_keyboard(response.item),
            )
        else:
            await msg.answer(
                "<b>Не удалось получить данные... (╥﹏╥)</b>\n\nПопробуйте позже!"
            )

    def _generate_keyboard(self, items: list[OutputMemory], max_length: int = 3):
        """
        Генерирует инлайн-клавиатуру для выбора воспоминаний.

        Кнопки группируются по строкам (по умолчанию не более 3 в строке).
        Каждая кнопка содержит заголовок воспоминания и callback_data в формате 'get-memory-{id}'.

        :param items: Список объектов воспоминаний (с атрибутами title и id)
        :param max_length: Максимальное количество кнопок в одной строке (по умолчанию 3)
        :return: Объект InlineKeyboardMarkup с сформированной клавиатурой
        """
        inline_keyboard = []
        keybard = []

        for indx, item in enumerate(items, 1):
            if not indx % max_length:
                inline_keyboard.append(keybard)
                keybard.clear()
                continue

            keybard.append(
                InlineKeyboardButton(
                    text=item.title, callback_data=f"get-memory-{item.id}"
                )
            )
        if keybard:
            inline_keyboard.append(keybard)

        return InlineKeyboardMarkup(inline_keyboard=inline_keyboard)
