from abc import ABC, abstractmethod

from aiogram import Router

from ...manager.memories import Memories


class BaseRouter(ABC):
    """Базовый роутер"""

    def __init__(self, manager: Memories):
        self.manager = manager
        self.router = Router()

        self.connect_routers()

    @abstractmethod
    def connect_routers(self):
        """Подключить роутеры"""
