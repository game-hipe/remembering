import os

from pathlib import Path
from typing import Any, TypeVar, Optional, Generic

from pydantic import BaseModel, field_validator

__all__ = [
    'TextMemory',
    'VideoMemory',
    'PhotoMemory',
    "BaseUser",
    "OutputUser",
    "BaseResponse",
    "OutputMemory"
]

T = TypeVar("T")

class BaseResponse(BaseModel, Generic[T]):
    """Базовый ответ"""
    success: bool
    message: str
    item: Optional[T] = None

class BaseMemeory(BaseModel):
    title: str
    content: str
    
    @field_validator('title')
    def title_validator(cls, v: Any):
        if not isinstance(v, str):
            raise TypeError(
                "Название должно быть строкой."
            )
            
        if len(v.strip()) == 0:
            raise ValueError(
                "Название не может быть пустым."
            )
            
        if len(v) > 255:
            raise ValueError(
                "Название не может быть длиннее 255 символов."
            )
        return v
            
    @field_validator('content')
    def content_validator(cls, v: Any):
        if not isinstance(v, str):
            raise TypeError(
                "Название должно быть строкой."
            )
            
        if len(v.strip()) == 0:
            raise ValueError(
                "Содержание не может быть пустым."
            )
            
        if len(v) > 2048:
            raise ValueError(
                "Содержание не может быть длиннее 2048 символов."
            )
        return v
            
class BaseItemMemory(BaseMemeory):
    item: Path
    
    @field_validator('item')
    def photo_validator(cls, v: Any):
        if not os.path.exists(v):
            raise FileNotFoundError(
                "Файл не найден."
            )
        elif Path(v).suffix not in ['.mp4', '.jpg', '.png']:
            raise ValueError(
                "Файл должен быть в поддеживаемом формате"
            )
        return Path(v)

class BaseUser(BaseModel):
    """Базовый пользователь"""
    name: str
    chat_id: int
    interval: int
    
class OutputUser(BaseUser):
    """Базовый пользователь с ID"""
    id: int
          
class TextMemory(BaseMemeory):
    """Сохраняет воспоминание без 'фото/видео'

    Args:
        title (str): Заголовок мысли.
        content (str): Содержание мысли.
    """
    
    type: str = 'text'
    
class VideoMemory(BaseItemMemory):
    """Сохраняет воспоминание с 'видео'

    Args:
        title (str): Заголовок мысли.
        content (str): Содержание мысли.
        item (Path): Путь к видео файлу (mp4).
    """
    
    type: str = 'video'
    
class PhotoMemory(BaseItemMemory):
    """Сохраняет воспоминание с 'фото'

    Args:
        title (str): Заголовок мысли.
        content (str): Содержание мысли.
        item (Path): Путь к фото файлу (jpg).
    """
    
    type: str = 'photo'
    
class OutputMemory(BaseMemeory):
    """Выход воспомнинаний"""
    id: int
    type: str
    user_id: int
    item: Optional[Path] = None