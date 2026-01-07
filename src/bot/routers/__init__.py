from aiogram import Router

from .add_memory import MemoryRouter
from .show_memory import ShowMemory

from ...manager.memories import Memories



def setup(memories: Memories) -> list[Router]:
    return [
        MemoryRouter(memories).router,
        ShowMemory(memories).router
    ]