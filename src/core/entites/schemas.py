import os
from datetime import datetime
from pathlib import Path
from typing import Any, TypeVar, Optional, Generic, List

from pydantic import BaseModel, field_validator

__all__ = [
    "TextMemory",
    "VideoMemory",
    "PhotoMemory",
    "BaseUser",
    "OutputUser",
    "BaseResponse",
    "OutputMemory",
]

T = TypeVar("T")


class BaseResponse(BaseModel, Generic[T]):
    """
    Универсальная модель ответа для всех операций.

    Стандартизирует формат возвращаемых данных: статус успеха, сообщение и опциональные данные.

    :param success: Флаг успешности выполнения операции
    :type success: bool
    :param message: Описание результата операции (успех или причина ошибки)
    :type message: str
    :param item: Опциональные данные, возвращаемые при успехе (может быть None)
    :type item: Optional[T]
    """

    success: bool
    message: str
    item: Optional[T] = None


class BaseMemory(BaseModel):
    """
    Базовая модель воспоминания с валидацией заголовка и содержания.

    Служит родительским классом для всех типов воспоминаний.
    Обеспечивает проверку длины и типа данных.
    """

    title: str
    content: str
    remind_to: datetime | None = None

    @field_validator("title")
    def title_validator(cls, v: Any):
        """
        Валидирует поле 'title' (заголовок).

        Проверяет:
        - Является ли строкой
        - Не пустое ли значение
        - Не превышает ли 255 символов

        :param v: Проверяемое значение заголовка
        :type v: Any
        :return: Очищенное значение заголовка
        :raises TypeError: Если значение не является строкой
        :raises ValueError: Если значение пустое или слишком длинное
        """
        if not isinstance(v, str):
            raise TypeError("Название должно быть строкой.")
        if len(v.strip()) == 0:
            raise ValueError("Название не может быть пустым.")
        if len(v) > 255:
            raise ValueError("Название не может быть длиннее 255 символов.")
        return v

    @field_validator("content")
    def content_validator(cls, v: Any):
        """
        Валидирует поле 'content' (содержание).

        Проверяет:
        - Является ли строкой
        - Не пустое ли значение
        - Не превышает ли 2048 символов

        :param v: Проверяемое значение содержания
        :type v: Any
        :return: Очищенное значение содержания
        :raises TypeError: Если значение не является строкой
        :raises ValueError: Если значение пустое или слишком длинное
        """
        if not isinstance(v, str):
            raise TypeError("Содержание должно быть строкой.")
        if len(v.strip()) == 0:
            raise ValueError("Содержание не может быть пустым.")
        if len(v) > 2048:
            raise ValueError("Содержание не может быть длиннее 2048 символов.")
        return v

    @field_validator("remind_to")
    def datetime_validator(cls, v: Any):
        if not isinstance(v, datetime):
            return datetime.now()
        elif isinstance(v, datetime):
            return v
        else:
            raise ValueError("Неверный формат даты и времени")

    @property
    def is_expired(self) -> bool:
        return self.remind_to < datetime.now()


class BaseItemMemory(BaseMemory):
    """
    Модель воспоминания, содержащего медиафайл.

    Наследуется от BaseMemory и добавляет поле 'item' для хранения пути к файлу.
    """

    item: Path

    @field_validator("item")
    def photo_validator(cls, v: Any):
        """
        Валидирует путь к медиафайлу.

        Проверяет:
        - Существует ли файл
        - Является ли файл в поддерживаемом формате (.mp4, .jpg, .png)

        :param v: Путь к файлу (может быть строкой или Path)
        :type v: Any
        :return: Объект Path к существующему файлу
        :raises FileNotFoundError: Если файл не существует
        :raises ValueError: Если формат файла не поддерживается
        """
        if not os.path.exists(v):
            raise FileNotFoundError("Файл не найден.")
        elif Path(v).suffix not in [".mp4", ".jpg", ".png"]:
            raise ValueError("Файл должен быть в поддерживаемом формате")
        return Path(v)


class BaseUser(BaseModel):
    """
    Модель данных нового пользователя.

    Используется для передачи данных при регистрации пользователя.
    Не содержит ID, так как он присваивается при сохранении в БД.
    """

    name: str
    chat_id: int
    interval: int


class OutputUser(BaseUser):
    """
    Модель данных пользователя с идентификатором.

    Используется для возврата данных о пользователе из системы.
    Расширяет BaseUser полем 'id'.
    """

    id: int
    memories: List[OutputMemory] = []  # noqa


class TextMemory(BaseMemory):
    """
    Модель текстового воспоминания (без медиа).

    Предназначена для хранения мыслей или заметок с заголовком и содержанием.
    Тип автоматически устанавливается как 'text'.
    """

    type: str = "text"


class VideoMemory(BaseItemMemory):
    """
    Модель воспоминания с видео.

    Предназначена для хранения видео-воспоминаний. Проверяет,
    что файл существует и имеет расширение .mp4.
    Тип автоматически устанавливается как 'video'.
    """

    type: str = "video"


class PhotoMemory(BaseItemMemory):
    """
    Модель воспоминания с фото.

    Предназначена для хранения фото-воспоминаний. Проверяет,
    что файл существует и имеет расширение .jpg или .png.
    Тип автоматически устанавливается как 'photo'.
    """

    type: str = "photo"


class OutputMemory(BaseMemory):
    """
    Модель выходных данных воспоминания.

    Используется для возврата информации о воспоминании из системы.
    Содержит все необходимые поля, включая идентификаторы и тип.
    Поле 'item' может быть None (для текстовых воспоминаний).
    """

    id: int
    type: str
    user_id: int
    item: Optional[Path] = None
