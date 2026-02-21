"""
Вкладка "Инструкция" — справочная информация о работе программы.
"""

import ttkbootstrap as ttk
from ttkbootstrap.constants import *


class InfoTab:
    """Вкладка с инструкцией по работе с программой."""

    def __init__(self, parent, controller):
        self.controller = controller
        self.frame = ttk.Frame(parent, padding=20)
        self._setup_ui()

    def _setup_ui(self):
        """Создание интерфейса."""
        center = ttk.Frame(self.frame)
        center.place(relx=0.5, rely=0.5, anchor="center")

        ttk.Label(
            center,
            text="РАБОТАЕТ — НЕ ТРОГАЙ",
            font=("TkDefaultFont", 42, "bold"),
            bootstyle=DANGER,
        ).pack(pady=(0, 20))

        ttk.Label(
            center,
            text="(c) Отдел ИБ",
            font=("TkDefaultFont", 14),
            bootstyle=SECONDARY,
        ).pack()

    def get_frame(self):
        return self.frame
