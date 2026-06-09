"""
Чтение секретов: файл (тест/отладка) или переменная окружения (прод).
"""

import logging
import os

logger = logging.getLogger("ioc_analyzer.credentials")

_EMPTY_MARKERS = {"", "-"}


def resolve_secret(password_file: str = "", password_env_var: str = "EWS_PASSWORD") -> str:
    """
    Возвращает пароль EWS из файла или переменной окружения.

    Приоритет: ``password_file`` (если задан и не ``"-"``) → env ``password_env_var``.
    """
    file_path = (password_file or "").strip()
    if file_path not in _EMPTY_MARKERS:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                value = f.read().strip()
            if value:
                return value
            logger.warning("Файл пароля '%s' пуст.", file_path)
        except OSError as e:
            logger.error("Не удалось прочитать файл пароля '%s': %s", file_path, e)

    env_name = (password_env_var or "EWS_PASSWORD").strip() or "EWS_PASSWORD"
    value = os.environ.get(env_name, "").strip()
    if not value:
        logger.warning("Переменная окружения '%s' для пароля EWS пуста.", env_name)
    return value
