from loguru import logger

from ..core import BaseResponse


def except_handler(func):
    """
    Декоратор для централизованной обработки исключений в асинхронных функциях.

    Перехватывает любые исключения, возникающие при выполнении декорируемой функции,
    логирует детали ошибки и возвращает стандартный объект BaseResponse с флагом неудачи.
    Используется для обеспечения стабильности и единообразия ответов в бизнес-логике.

    :param func: Асинхронная функция, подлежащая оборачиванию
    :type func: callable
    :return: Обёрнутая функция с обработкой исключений
    :rtype: callable
    """

    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            logger.error(
                f"Ошибка в функции '{func.__name__}' (error-type={type(e)}, error={e})",
            )
            return BaseResponse(
                success=False,
                message=f"Ошибка во время выполнения функции '{func.__name__}' (error={e})",
                item=None,
            )

    return wrapper
