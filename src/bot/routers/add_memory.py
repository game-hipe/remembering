from string import Template
from typing import Awaitable

from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from aiogram.filters import Command, StateFilter
from aiogram.exceptions import TelegramBadRequest
from aiogram import F

from .base import BaseRouter
from ...core.entites import TextMemory, PhotoMemory, VideoMemory
from ...core import config
from ...core.entites import OutputMemory

SUCCESS_ADDED_TEXT = Template(
    "📝 <b>Воспоминание сохранено!</b>\n\n"
    "📌 <b>Заголовок:</b> ${title}\n"
    "📝 <b>Описание:</b> ${content}"
)

UNSUCCESS_ADDED_TEXT = Template(
    "❌ <b>Не удалось сохранить воспоминание</b>\n\n<b>Сообщение:</b> ${message}"
)


class AddMemory(StatesGroup):
    waiting_title = State()
    waiting_content = State()
    waiting_photo = State()


class MemoryRouter(BaseRouter):
    """
    Маршрутизатор для обработки создания и сохранения воспоминаний через FSM (Finite State Machine).

    Класс управляет процессом пошагового ввода данных пользователем:
    - Заголовок
    - Описание
    - Фото или видео (опционально)
    Состояния управляются через FSMContext, а данные сохраняются через менеджер.

    Использует состояние AddMemory для отслеживания этапов ввода.
    """

    def connect_routers(self):
        """
        Настраивает обработчики сообщений для различных этапов FSM.

        Регистрирует обработчики для:
        - Начала добавления воспоминания (/addmemory)
        - Ввода заголовка
        - Ввода описания
        - Выбора медиа (фото, видео или "нет")
        - Обработки некорректного ввода на этапе медиа
        """
        self.router.message.register(
            self.add_memory, Command("addmemory"), StateFilter(None)
        )

        self.router.message.register(
            self.get_title, StateFilter(AddMemory.waiting_title)
        )

        self.router.message.register(
            self.get_content, StateFilter(AddMemory.waiting_content)
        )

        # Обработка отсутствия медиа
        self.router.message.register(
            self.handle_no_media,
            StateFilter(AddMemory.waiting_photo),
            F.text.lower().strip() == "нет",
        )

        # Обработка фото
        self.router.message.register(
            self.handle_with_photo, StateFilter(AddMemory.waiting_photo), F.photo
        )

        # Обработка видео
        self.router.message.register(
            self.handle_with_video, StateFilter(AddMemory.waiting_photo), F.video
        )

        # Обработка некорректного ввода на этапе медиа
        self.router.message.register(
            self.handle_wrong_input, StateFilter(AddMemory.waiting_photo)
        )

    async def add_memory(self, message: Message, state: FSMContext):
        """
        Начинает процесс добавления воспоминания.

        Отправляет запрос на ввод заголовка и переводит FSM в состояние waiting_title.

        :param message: Объект входящего сообщения от пользователя
        :param state: Контекст состояния FSM
        """
        await message.answer("Введите заголовок воспоминания:")
        await state.set_state(AddMemory.waiting_title)

    async def get_title(self, message: Message, state: FSMContext):
        """
        Обрабатывает ввод заголовка воспоминания.

        Проверяет:
        - Наличие текста
        - Непустое значение
        - Длину (не более 255 символов)
        При успехе сохраняет заголовок и переходит к вводу описания.

        :param message: Сообщение с заголовком
        :param state: Контекст состояния FSM
        """
        if message.text is None:
            await message.answer("Пожалуйста, введите заголовок воспоминания")
            return
        elif not message.text.strip():
            await message.answer(
                "Заголовок не может быть пустым. Пожалуйста, введите заголовок воспоминания"
            )
            return
        elif len(message.text) > 255:
            await message.answer(
                "Заголовок слишком длинный. Пожалуйста, введите заголовок не длиннее 255 символов"
            )
            return

        await state.update_data(title=message.text)
        await message.answer("Теперь введите описание воспоминания:")
        await state.set_state(AddMemory.waiting_content)

    async def get_content(self, message: Message, state: FSMContext):
        """
        Обрабатывает ввод описания воспоминания.

        Проверяет:
        - Наличие текста
        - Непустое значение
        - Длину (не более 2048 символов)
        При успехе сохраняет описание и переходит к этапу медиа.

        :param message: Сообщение с описанием
        :param state: Контекст состояния FSM
        """
        if message.text is None:
            await message.answer("Пожалуйста, введите описание воспоминания")
            return
        elif not message.text.strip():
            await message.answer(
                "Описание не может быть пустым. Пожалуйста, введите описание воспоминания"
            )
            return
        elif len(message.text) > 2048:
            await message.answer(
                "Описание слишком длинное. Пожалуйста, введите описание не длиннее 2048 символов"
            )
            return

        await state.update_data(content=message.text)
        await message.answer(
            "Теперь отправьте фото/видео для воспоминания (Либо 'нет' для без фото):"
        )
        await state.set_state(AddMemory.waiting_photo)

    async def handle_no_media(self, message: Message, state: FSMContext):
        """
        Обрабатывает выбор отсутствия медиа (ввод 'нет').

        Извлекает ранее введённые заголовок и описание,
        сохраняет воспоминание без медиа через менеджер.

        :param message: Сообщение с текстом "нет"
        :param state: Контекст состояния FSM
        """
        data = await state.get_data()
        title = data.get("title")
        content = data.get("content")

        response = await self.save_memory(message.chat.id, title, content)
        if response.success:
            await self._safe_send_message(
                message.answer(
                    SUCCESS_ADDED_TEXT.substitute(title=title, content=content)
                ),
                message,
                response.item,
            )
        else:
            await message.answer(
                UNSUCCESS_ADDED_TEXT.substitute(message=response.message)
            )

        await state.clear()

    async def handle_with_photo(self, message: Message, state: FSMContext):
        """
        Обрабатывает загрузку фото.

        Скачивает фото, сохраняет его на диск,
        затем сохраняет воспоминание с указанием типа 'photo'.

        :param message: Сообщение с фото
        :param state: Контекст состояния FSM
        """
        photo_id = message.photo[-1].file_id
        file_path = config.PATH_IMAGE / f"{photo_id}.jpg"
        await message.bot.download(photo_id, file_path)

        data = await state.get_data()
        title = data.get("title")
        content = data.get("content")

        response = await self.save_memory_with_media(
            message.chat.id, title, content, file_path, "photo"
        )
        if response.success:
            await self._safe_send_message(
                message.answer_photo(
                    photo_id,
                    caption=SUCCESS_ADDED_TEXT.substitute(title=title, content=content),
                ),
                message,
                response.item,
            )
        else:
            await message.answer(
                caption=UNSUCCESS_ADDED_TEXT.substitute(message=response.message)
            )

        await message.answer("Воспоминание сохранено с фото!")
        await state.clear()

    async def handle_with_video(self, message: Message, state: FSMContext):
        """
        Обрабатывает загрузку видео.

        Скачивает видео, сохраняет его на диск,
        затем сохраняет воспоминание с указанием типа 'video'.

        :param message: Сообщение с видео
        :param state: Контекст состояния FSM
        """
        video_id = message.video.file_id
        file_path = config.PATH_VIDEO / f"{video_id}.mp4"
        await message.bot.download(video_id, file_path)

        data = await state.get_data()
        title = data.get("title")
        content = data.get("content")

        response = await self.save_memory_with_media(
            message.chat.id, title, content, file_path, "video"
        )
        if response.success:
            await self._safe_send_message(
                message.answer_video(
                    video_id,
                    caption=SUCCESS_ADDED_TEXT.substitute(title=title, content=content),
                ),
                message,
                response.item,
            )
        else:
            await message.answer(
                caption=UNSUCCESS_ADDED_TEXT.substitute(message=response.message)
            )

        await state.clear()

    async def handle_wrong_input(self, message: Message, state: FSMContext):
        """
        Обрабатывает некорректный ввод на этапе отправки медиа.

        Напоминает пользователю, что нужно отправить фото, видео или написать 'нет'.

        :param message: Сообщение с некорректным содержанием
        :param state: Контекст состояния FSM
        """
        await message.answer("Пожалуйста, отправьте фото, видео или напишите 'нет'")

    async def save_memory(self, chat_id: int, title: str, content: str):
        """
        Сохраняет текстовое воспоминание (без медиа) через менеджер.

        :param chat_id: Идентификатор чата пользователя
        :param title: Заголовок воспоминания
        :param content: Описание воспоминания
        :return: Результат операции сохранения (объект с полями success, message)
        """
        return await self.manager.add_memory(
            chat_id, TextMemory(title=title, content=content)
        )

    async def save_memory_with_media(
        self, chat_id: int, title: str, content: str, path: str, type: str
    ):
        """
        Сохраняет воспоминание с медиа (фото или видео) через менеджер.

        В зависимости от типа создаёт объект PhotoMemory или VideoMemory.

        :param chat_id: Идентификатор чата пользователя
        :param title: Заголовок воспоминания
        :param content: Описание воспоминания
        :param path: Путь к сохранённому файлу
        :param type: Тип медиа ('photo' или 'video')
        :return: Результат операции сохранения
        """
        factory = PhotoMemory if type == "photo" else VideoMemory
        return await self.manager.add_memory(
            chat_id, factory(title=title, content=content, item=path)
        )

    async def _safe_send_message(
        self, awaitable: Awaitable, message: Message, memory: OutputMemory
    ):
        """
        Обрабатывает возможные ошибки при отправке сообщения.

        :param awaitable: Асинхронная операция отправки сообщения
        :param message: Сообщение, которое отправлено
        :param memory: Воспоминание, которое было отправлено
        """
        try:
            await awaitable

        except TelegramBadRequest as e:
            await message.answer(
                UNSUCCESS_ADDED_TEXT.substitute(
                    message=f"Ошибка во время парсинга ответа: {str(e)}"
                )
            )
            await self.manager.delete_memory(memory.id)

        except Exception as e:
            await message.answer(
                UNSUCCESS_ADDED_TEXT.substitute(
                    message=f"Ошибка во время добавление в память: {str(e)}"
                )
            )
            await self.manager.delete_memory(memory.id)
