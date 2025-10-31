"""
Точка входа в приложение IOC Parser V2.
Обрабатывает запуск как в консольном, так и в бесконсольном режиме (.exe).
"""

import sys
import os


def setup_console_mode():
    """Настройка режима консоли для избежания ошибок при запуске .exe файла."""
    if sys.stdout is None:
        sys.stdout = open(os.devnull, 'w')
    if sys.stderr is None:
        sys.stderr = open(os.devnull, 'w')


def main():
    """Главная функция приложения."""
    # Настройка консольного режима
    setup_console_mode()
    
    try:
        # Импорты после настройки консоли
        from src.controller.app_controller import AppController
        from src.view.main_view import MainView
        
        # Создание контроллера
        controller = AppController(config_path="config.txt")
        
        # Создание и запуск GUI
        view = MainView(controller)
        view.run()
        
    except Exception as e:
        # В случае критической ошибки пытаемся показать messagebox
        try:
            from tkinter import messagebox
            messagebox.showerror(
                "Критическая ошибка",
                f"Не удалось запустить приложение:\n\n{str(e)}"
            )
        except:
            pass
        
        sys.exit(1)


if __name__ == "__main__":
    main()
