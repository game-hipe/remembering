import asyncio
from string import Template

from aiogram import Bot
from loguru import logger

from ..manager.memories import Memories
from ..core.entites import OutputUser, OutputMemory

REMEMBER_MORE_TEXT = Template(
    "Привет! Хотел бы напомнить у тебя <b>${count}</b> напоминаний.\n\n"
    "${items}\nЛучше посмотри!"
)
REMEMBER_TEXT = Template(
    "Привет! У тебя не законченоое дело <b>${title}</b>.\n\n"
    "Вот что ты себе оставил:\n<b>${content}</b>\n"
    "Ты хотел это себе напомнить в {date}"
)

class Notification:
    """
    Сервис уведомлений для отправки напоминаний пользователям по расписанию.

    Класс отвечает за регулярную проверку истекших воспоминаний через менеджер
    и отправку соответствующих уведомлений пользователям через Telegram-бота.
    Поддерживает пакетную обработку пользователей и настраиваемые интервалы.

    :param manager: Экземпляр менеджера воспоминаний для получения данных о пользователях и их напоминаниях.
    :type manager: Memories
    :param bot: Экземпляр Telegram-бота для отправки сообщений.
    :type bot: Bot
    :param batch_size: Количество пользователей, обрабатываемых за одну итерацию, по умолчанию 100.
    :type batch_size: int
    :param interval: Интервал (в секундах) между проверками уведомлений, по умолчанию 300 (5 минут).
    :type interval: float
    """

    def __init__(
        self,
        manager: Memories,
        bot: Bot,
        *,
        batch_size: int = 100,
        interval: float = 300,
    ) -> None:
        self.batch_size = batch_size
        self.manager = manager
        self.bot = bot
        self.interval = interval

    async def start(self) -> None:
        """
        Запускает бесконечный цикл проверки и отправки уведомлений.

        Периодически получает пакеты пользователей, определяет у кого истекли напоминания,
        и отправляет соответствующие сообщения. После каждой итерации делает паузу
        в соответствии с заданным интервалом.

        :return: Ничего не возвращает (запускает бесконечный цикл).
        :rtype: None
        """
        while True:
            logger.info("Начинаем отправлять сообщение...")
            async for users in self.manager.get_users(self.batch_size):
                if not users.item:
                    break
                logger.info(
                    f"Отправка уведомлений пользователям {[x.chat_id for x in users.item]}"
                )

                expired_users = self._get_expired_users(users.item)
                await self._batch_send(expired_users)
            logger.success("Успешно удалось отправить сообщение.")
            logger.info(f"Ожидание {self.interval} секунд.")
            await asyncio.sleep(self.interval)

    async def _batch_send(self, users: list[OutputUser]) -> None:
        """
        Асинхронно отправляет сообщения группе пользователей с истекшими воспоминаниями.

        Для каждого пользователя формирует текст уведомления: если одно воспоминание —
        отправляет его заголовок и содержание, если несколько — отправляет количество.

        :param users: Список пользователей с истекшими воспоминаниями.
        :type users: list[OutputUser]
        :return: Ничего не возвращает.
        :rtype: None
        """
        tasks = []
        for user in users:
            if len(user.memories) == 1:
                memories = user.memories[0]
                tasks.append(
                    asyncio.create_task(self._send_message(
                        user.chat_id,
                        REMEMBER_TEXT.substitute(
                            title=memories.title,
                            content=memories.content,
                            date=memories.remind_to.strftime("%d-%m-%Y, %H:%M:%S"),
                        ),
                    ))
                )
            else:
                tasks.append(
                    asyncio.create_task(
                        self._send_message(
                        user.chat_id,
                        REMEMBER_MORE_TEXT.substitute(
                            count=len(user.memories), items=self._build_items(user.memories)
                        ),
                    ))
                )
        # Замечание: задачи не собираются через asyncio.gather, возможно упущение
        await asyncio.gather(*tasks)

    async def _send_message(self, chat_id: int, text: str) -> None:
        """
        Отправляет сообщение указанному пользователю через бота.

        :param chat_id: Идентификатор чата пользователя в Telegram.
        :type chat_id: int
        :param text: Текст сообщения для отправки.
        :type text: str
        :return: Ничего не возвращает.
        :rtype: None
        """
        await self.bot.send_message(chat_id=chat_id, text=text)

    def _get_expired_users(self, users: list[OutputUser]) -> list[OutputUser]:
        """
        Фильтрует пользователей, у которых есть хотя бы одно истекшее воспоминание.

        :param users: Список пользователей для проверки.
        :type users: list[OutputUser]
        :return: Список пользователей с истекшими воспоминаниями.
        :rtype: list[OutputUser]
        """
        result = []
        for user in users:
            if memory := self._get_expired(user):
                result.append(
                    OutputUser(
                        name=user.name,
                        chat_id=user.chat_id,
                        interval=user.interval,
                        id=user.id,
                        memories=memory,
                    )
                )
        return result

    def _get_expired(self, user: OutputUser) -> list[OutputMemory]:
        """
        Извлекает список истекших воспоминаний пользователя.

        :param user: Объект пользователя с набором воспоминаний.
        :type user: OutputUser
        :return: Список воспоминаний, у которых установлен флаг `is_expired`.
        :rtype: list[OutputMemory]
        """
        tasks = []
        for task in user.memories:
            if task.is_expired:
                tasks.append(task)
        return tasks

    def _build_items(self, memories: list[OutputMemory]) -> str:
        """
        Формирует строковое представление списка воспоминаний для вставки в сообщение.

        Каждое воспоминание отображается с индексом, заголовком и обрезанным содержанием (до 10 символов).

        :param memories: Список воспоминаний для форматирования.
        :type memories: list[OutputMemory]
        :return: Отформатированная строка с перечислением воспоминаний.
        :rtype: str
        """
        return "\n".join(
            [
                f"{index}. {memory.title} - {memory.content[:20] if memory.content[:20] == memory.content else memory.content[:20] + '...'}"
                for index, memory in enumerate(memories, 1)
            ]
        )