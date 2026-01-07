from typing import List, Literal, TypeAlias

from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy import String, ForeignKey, Integer

_TypeFormat :TypeAlias = Literal['video', 'photo', 'text']

__all__ = [
    "Memory",
    "User"
]

class Base(DeclarativeBase):
    ...

class Memeory(Base):
    __tablename__ = "memory"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(255))
    content: Mapped[str] = mapped_column(String(2048))
    type: Mapped[_TypeFormat] = mapped_column(String(10))
    item: Mapped[str] = mapped_column(String(2048), nullable=True)
    
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"))
    
    user: Mapped[User] = relationship(
        "User",
        back_populates="memories"
    )
    
    def __repr__(self):
        return 'Memory(id={}, title={}, content={}, type={}, user_id={})'.format(
            self.id,
            self.title[:30],
            self.content[:30],
            self.type,
            self.user_id
        )
    
class User(Base):
    __tablename__ = "user"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    chat_id: Mapped[int] = mapped_column(Integer(), unique=True)
    interval: Mapped[int] = mapped_column(Integer(), default=300)
    
    memories: Mapped[List[Memeory]] = relationship(
        "Memeory",
        back_populates="user",
        cascade="all, delete-orphan"
    )
    
    def __repr__(self):
        return 'User(id={}, name={}, chat_id={}, interval={})'.format(
            self.id,
            self.name,
            self.chat_id,
            self.interval
        )