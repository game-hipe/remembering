from aiogram import Router

from .add_memory import MemoryRouter
from .show_memory import ShowMemory

from ...manager.memories import Memories


def setup(memories: Memories) -> list[Router]:
    """Создание всех роутеров

    Args:
        memories (Memories): Экземпляр менеджера для работы с воспоминаниями.

    Returns:
        list[Router]: Список роутеров.
    """

    return [MemoryRouter(memories).router, ShowMemory(memories).router]
