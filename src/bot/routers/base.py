from string import Template
from abc import ABC, abstractmethod

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.types import FSInputFile
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from ...manager.memories import Memories
from ...core import OutputMemory
from .tools import id_extracter


MEMORY_TEXT = Template(
    "📖 <b>${title}</b>\n━━━━━━━━━━━━━━━━━━━━\n📝 ${text}\n━━━━━━━━━━━━━━━━━━━━"
)


class BaseRouter(ABC):
    """
    Абстрактный базовый класс для всех роутеров, обрабатывающих воспоминания.

    Предоставляет общую функциональность:
    - Регистрацию обработчиков
    - Отправку воспоминаний с учётом типа медиа
    - Унифицированную клавиатуру
    - Обработку удаления воспоминаний

    Наследники обязаны реализовать метод connect_routers() для настройки маршрутов.
    """

    def __init__(self, manager: Memories):
        """
        Инициализирует базовый роутер.

        Создаёт экземпляр Router, сохраняет менеджер данных и
        автоматически регистрирует обработчики.

        :param manager: Экземпляр менеджера для работы с воспоминаниями
        :type manager: Memories
        """
        self.manager = manager
        self.router = Router()
        self.connect_routers()
        self.__connect_base()

    @abstractmethod
    def connect_routers(self):
        """
        Абстрактный метод для регистрации обработчиков сообщений.

        Должен быть реализован в дочерних классах для настройки
        маршрутов на команды, состояния и другие события.
        """

    def __connect_base(self):
        """
        Приватный метод для подключения базовых обработчиков.

        Регистрирует обработчик callback-запросов для удаления воспоминаний
        по префиксу 'delete-memory'.
        """
        self.router.callback_query.register(
            self.delete_memory, F.data.startswith("delete-memory")
        )

    async def send_memeory(self, message: Message, memory: OutputMemory):
        """
        Отправляет воспоминание пользователю с учётом его типа.

        В зависимости от типа воспоминания (текст, фото, видео) использует
        соответствующий метод отправки с поддержкой медиа и клавиатуры.

        :param message: Объект входящего сообщения для ответа
        :type message: aiogram.types.Message
        :param memory: Объект воспоминания для отправки
        :type memory: OutputMemory
        """
        if memory.type == "text":
            await message.answer(
                self._build_text(memory),
                reply_markup=self._build_memory_keyboard(memory),
            )
        elif memory.type == "photo":
            await message.answer_photo(
                FSInputFile(memory.item),
                caption=self._build_text(memory),
                reply_markup=self._build_memory_keyboard(memory),
            )
        elif memory.type == "video":
            await message.answer_video(
                FSInputFile(memory.item),
                caption=self._build_text(memory),
                reply_markup=self._build_memory_keyboard(memory),
            )

    def _build_text(self, memory: OutputMemory) -> str:
        """
        Формирует текстовое представление воспоминания.

        Использует шаблон MEMORY_TEXT для подстановки заголовка и содержания.

        :param memory: Объект воспоминания
        :type memory: OutputMemory
        :return: Отформатированный текст с HTML-разметкой
        :rtype: str
        """
        return MEMORY_TEXT.substitute(title=memory.title, text=memory.content)

    def _build_memory_keyboard(self, memory: OutputMemory) -> InlineKeyboardMarkup:
        """
        Создаёт инлайн-клавиатуру для управления воспоминанием.

        Добавляет кнопку удаления с callback_data, включающим ID воспоминания.

        :param memory: Объект воспоминания
        :type memory: OutputMemory
        :return: Объект клавиатуры с одной кнопкой удаления
        :rtype: InlineKeyboardMarkup
        """
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="🗑️ Удалить", callback_data=f"delete-memory-{memory.id}"
                    )
                ]
            ]
        )

    async def delete_memory(self, call: CallbackQuery):
        """
        Обрабатывает запрос на удаление воспоминания.

        Извлекает ID из callback_data, удаляет воспоминание через менеджер,
        удаляет исходное сообщение и отправляет пользователю результат операции.

        :param call: Объект callback-запроса от нажатия кнопки
        :type call: aiogram.types.CallbackQuery
        """
        memory_id = id_extracter(call.data)
        result = await self.manager.delete_memory(memory_id)

        await call.message.delete()

        if result.success:
            if result.item:
                await call.message.answer("<b>Воспоминание успешно удалено!</b>")
            else:
                await call.message.answer("<b>Воспоминание не найдено... (╥﹏╥)</b>")
        else:
            await call.message.answer(
                f"<b>Не удалось удалить воспоминание... (╥﹏╥)</b>\n\nОшибка: {result.message}"
            )
