from datetime import datetime
from typing import List, Literal, TypeAlias

from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy import String, ForeignKey, Integer, DateTime

from .. import config

_TypeFormat: TypeAlias = Literal["video", "photo", "text"]

__all__ = ["Memory", "User"]


class Base(DeclarativeBase): ...


class Memory(Base):
    """
    ORM-модель для хранения воспоминаний пользователей в базе данных.

    Содержит информацию о заголовке, содержании, типе медиа (текст, фото, видео),
    пути к файлу (если есть) и ссылке на пользователя. Связана с таблицей 'memory'.
    """

    __tablename__ = "memory"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(255))
    content: Mapped[str] = mapped_column(String(2048))
    type: Mapped[_TypeFormat] = mapped_column(String(10))
    item: Mapped[str] = mapped_column(String(2048), nullable=True)

    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"))
    sent_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=True, default=lambda: datetime.now(config.APP_TZ)
    )

    user: Mapped[User] = relationship(  # noqa
        "User", back_populates="memories"
    )

    def __repr__(self):
        """
        Возвращает строковое представление объекта Memory.

        Обрезает длинные поля title и content до 30 символов для читаемости.

        :return: Строковое представление объекта
        :rtype: str
        """
        return "Memory(id={}, title={}, content={}, type={}, user_id={})".format(
            self.id, self.title[:30], self.content[:30], self.type, self.user_id
        )


class User(Base):
    """
    ORM-модель для хранения данных пользователей в базе данных.

    Содержит основную информацию о пользователе: имя, идентификатор чата в Telegram,
    интервал напоминаний. Связана с воспоминаниями через отношение один-ко-многим.
    Обеспечивает каскадное удаление воспоминаний при удалении пользователя.
    """

    __tablename__ = "user"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    chat_id: Mapped[int] = mapped_column(Integer(), unique=True)
    interval: Mapped[int] = mapped_column(Integer(), default=300)

    last_sent_at: Mapped[datetime] = mapped_column(
        DateTime(), nullable=True, default= lambda: datetime.now(config.APP_TZ)
    )
    memories: Mapped[List[Memory]] = relationship(
        "Memory", back_populates="user", cascade="all, delete-orphan", lazy="joined"
    )

    def __repr__(self):
        """
        Возвращает строковое представление объекта User.

        :return: Строковое описание пользователя с основными полями
        :rtype: str
        """
        return "User(id={}, name={}, chat_id={}, interval={})".format(
            self.id, self.name, self.chat_id, self.interval
        )
