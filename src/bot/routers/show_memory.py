import random
from string import Template

from aiogram import F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command, StateFilter

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from .tools import id_extracter
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
        self.router.message.register(
            self.show_memorys, Command("showmemory"), StateFilter(None)
        )
        self.router.message.register(
            self.show_memorys, F.text == "📋 Список воспоминаний", StateFilter(None)
        )

        self.router.callback_query.register(
            self.show_memory, F.data.startswith("get-memory")
        )

    async def show_memory(self, call: CallbackQuery):
        id = id_extracter(call.data)
        memory = await self.manager.get_memory(id)

        await call.message.delete()
        if not memory.success:
            await call.message.answer(
                "<b>Не удалось получить данные... (╥﹏╥)</b>",
            )
            return

        elif memory.item is None:
            await call.message.answer(
                "<b>Не удалось получить данные... (╥﹏╥)</b>",
            )
            return

        else:
            await self.send_memeory(call.message, memory.item)

    async def show_memorys(self, message: Message):
        """
        Обрабатывает команду /showmemory и отображает список воспоминаний.

        Получает список воспоминаний пользователя через менеджер,
        формирует ответное сообщение со списком и случайной цитатой,
        прикрепляет клавиатуру с выбором воспоминаний.

        :param message: Входящее сообщение от пользователя
        """
        response = await self.manager.get_memories(message.chat.id)

        if response.success:
            await message.answer(
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
            await message.answer(
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
        current_row = []  # Переименуем для ясности

        for indx, item in enumerate(items, 1):
            current_row.append(
                InlineKeyboardButton(
                    text=item.title, callback_data=f"get-memory-{item.id}"
                )
            )

            if not indx % max_length:
                inline_keyboard.append(current_row)  # Добавляем текущий ряд
                current_row = []  # Создаем НОВЫЙ список для следующего ряда

        # Добавляем последний неполный ряд
        if current_row:
            inline_keyboard.append(current_row)

        return InlineKeyboardMarkup(inline_keyboard=inline_keyboard)
