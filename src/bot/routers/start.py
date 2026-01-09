from aiogram.types import Message
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext

from ._defaults import DEFAULT_KEYBOARD
from .base import BaseRouter

START_TEXT = (
    "👋 <b>Добро пожаловать!</b>\n\n"
    "Я - <b>Remembering Bot</b> - ваш помощник в запоминании важных моментов.\n"
    "Я помогу вам запоминать любые важные моменты, которые вы хотите сохранить."
    "\n\nИспользуйте /help для получения списка команд."
)

HELP_TEXT = (
    "📚 <b>Помощь</b> - <code>Серьёзно?</code>\n\n"
    "<b>Основные команды:</b>\n"
    "- /start - Начать работу с ботом\n"
    "- /help - Показать справку\n"
    "- /cancel - Отменить текущее действие\n"
    "<b>Команды для воспоминаний:</b>\n"
    "- /addmemory - Добавить новое воспоминание\n"
    "- /showmemory - Показать список воспоминаний"
)


class Start(BaseRouter):
    def connect_routers(self):
        self.router.message.register(self.start, Command("start"))
        self.router.message.register(self.help, Command("help"))
        self.router.message.register(self.cancel, Command("cancel"))

    async def start(self, message: Message):
        await message.answer(START_TEXT, reply_markup=DEFAULT_KEYBOARD)

    async def help(self, message: Message):
        await message.answer(HELP_TEXT, reply_markup=DEFAULT_KEYBOARD)

    async def cancel(self, message: Message, state: FSMContext):
        await state.clear()
        await message.answer(
            "<b>Состояние сброшено!</b>", reply_markup=DEFAULT_KEYBOARD
        )
