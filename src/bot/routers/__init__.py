from aiogram import Router

from .add_memory import MemoryRouter
from .show_memory import ShowMemory
from .start import Start

from ...manager.memories import Memories


def setup(memories: Memories) -> list[Router]:
    """Создание всех роутеров

    Args:
        memories (Memories): Экземпляр менеджера для работы с воспоминаниями.

    Returns:
        list[Router]: Список роутеров.
    """

    return [
        Start(memories).router,
        MemoryRouter(memories).router,
        ShowMemory(memories).router,
    ]
