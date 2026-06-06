"""Утилиты для работы с путями и файлами."""

import os
import sys


def get_application_base_path():
    """
    Определяет базовый путь приложения.

    Возвращает корректный путь независимо от того, запущено ли
    приложение из исходников или собрано в .exe через PyInstaller.

    Returns:
        str: Абсолютный путь к директории приложения
    """
    if getattr(sys, 'frozen', False):
        # Приложение запущено как .exe (PyInstaller)
        # sys.executable - это путь к .exe файлу
        return os.path.dirname(os.path.abspath(sys.executable))
    else:
        # Приложение запущено из исходников
        # Возвращаем корневую директорию проекта (на уровень выше src/)
        return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


