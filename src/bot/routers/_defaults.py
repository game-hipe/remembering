from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

DEFAULT_KEYBOARD = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="📝 Добавить воспоминание"),
            KeyboardButton(text="📋 Список воспоминаний"),
        ],
        # [KeyboardButton(text="⚙️ Личные настройки")],
    ],
    resize_keyboard=True,
)

CANCEL_KEYBOARD = ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="❌ ОТМЕНА")]])
