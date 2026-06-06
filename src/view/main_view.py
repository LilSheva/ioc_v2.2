"""
Главное окно приложения с вкладками.
"""

import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from .tabs.main_tab import MainTab
from .tabs.settings_tab import SettingsTab
from .tabs.results_tab import ResultsTab
from .tabs.ip_tab import IPTab
from .tabs.info_tab import InfoTab


class MainView:
    """Главное окно приложения."""

    def __init__(self, controller):
        self.controller = controller

        self.root = ttk.Window(
            title="IOC Parser v2.2",
            themename="darkly",
            size=(1200, 800),
            resizable=(True, True)
        )

        self.root.minsize(900, 600)
        self.root.position_center()
        self._setup_ui()
        self._apply_rounded_styles()

    def _setup_ui(self):
        """Создание элементов интерфейса."""
        # ── Заголовок: одна строка, название слева, кнопки справа ──
        header_frame = ttk.Frame(self.root, padding=(15, 10))
        header_frame.pack(fill=X, side=TOP)

        title_left = ttk.Frame(header_frame)
        title_left.pack(side=LEFT)

        ttk.Label(
            title_left,
            text="IOC Parser",
            font=("Segoe UI", 17, "bold"),
            bootstyle=PRIMARY
        ).pack(side=LEFT)

        ttk.Label(
            title_left,
            text="  v2.2",
            font=("Segoe UI", 11),
            bootstyle=SECONDARY
        ).pack(side=LEFT, pady=(4, 0))

        ttk.Label(
            title_left,
            text="   |   Анализатор индикаторов компрометации",
            font=("Segoe UI", 11),
            bootstyle=SECONDARY
        ).pack(side=LEFT, pady=(4, 0))

        # Кнопки справа: инструкция ?, настройки ⚙, тоглер темы
        self._is_dark = True

        self._theme_btn = ttk.Button(
            header_frame,
            text="☀️ Переходи на сторону добра",
            command=self._toggle_theme,
            bootstyle="warning-outline",
        )
        self._theme_btn.pack(side=RIGHT)

        # Кнопка инструкции "?"
        self._info_btn = ttk.Button(
            header_frame,
            text=" ? ",
            command=self._toggle_info_tab,
            bootstyle="info-outline",
            width=4,
        )
        self._info_btn.pack(side=RIGHT, padx=(0, 8))

        # Кнопка настроек "⚙"
        self._settings_btn = ttk.Button(
            header_frame,
            text=" ⚙ ",
            command=self._toggle_settings_tab,
            bootstyle="light",
            width=4,
        )
        self._settings_btn.pack(side=RIGHT, padx=(0, 4))

        # ── Разделитель ──
        ttk.Separator(self.root, orient=HORIZONTAL).pack(fill=X, padx=10)

        # ── Вкладки ──
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=BOTH, expand=True, padx=10, pady=(8, 5))

        self.main_tab = MainTab(self.notebook, self.controller)
        self.results_tab = ResultsTab(self.notebook, self.controller)
        self.ip_tab = IPTab(self.notebook, self.controller)
        self.settings_tab = SettingsTab(self.notebook, self.controller)
        self.info_tab = InfoTab(self.notebook, self.controller)

        self.notebook.add(self.main_tab.get_frame(), text="  Главная  ")
        self.notebook.add(self.results_tab.get_frame(), text="  Результаты запросов  ")
        self.notebook.add(self.ip_tab.get_frame(), text="  IP управление  ")
        self.notebook.add(self.settings_tab.get_frame(), text="  Настройка IOC  ")
        self.notebook.add(self.info_tab.get_frame(), text="  Инструкция  ")

        # Скрываем вкладки настроек и инструкции из полоски табов
        self.notebook.hide(3)  # Настройка IOC
        self.notebook.hide(4)  # Инструкция

        self._settings_visible = False
        self._info_visible = False

        # ── Футер ──
        footer_frame = ttk.Frame(self.root, padding=(15, 6))
        footer_frame.pack(fill=X, side=BOTTOM)

        ttk.Separator(self.root, orient=HORIZONTAL).pack(fill=X, padx=10, side=BOTTOM)

        ttk.Label(
            footer_frame,
            text="IOC Parser v2.2  |  .docx → .xlsx",
            font=("Segoe UI", 9),
            bootstyle=SECONDARY
        ).pack(side=LEFT)

        self.notebook.bind("<<NotebookTabChanged>>", self._on_tab_changed)

    def _on_tab_changed(self, event):
        current_tab = self.notebook.index(self.notebook.select())
        if current_tab == 1:
            if self.controller.get_last_query_data():
                self.results_tab.refresh_data()
        elif current_tab == 2:
            self.ip_tab.refresh_data()

        # Скрываем вкладки настроек/инструкции когда они не активны
        if current_tab != 3:
            self.notebook.hide(3)
        if current_tab != 4:
            self.notebook.hide(4)

        # Обновляем стили кнопок
        self._update_header_buttons(current_tab)

    def _update_header_buttons(self, current_tab):
        """Обновляет стили кнопок настроек/инструкции."""
        if current_tab == 3:
            self._settings_btn.configure(bootstyle="light")
            self._settings_visible = True
        else:
            self._settings_btn.configure(bootstyle="light-outline" if not self._is_dark else "light")
            self._settings_visible = False

        if current_tab == 4:
            self._info_btn.configure(bootstyle="info")
            self._info_visible = True
        else:
            self._info_btn.configure(bootstyle="info-outline")
            self._info_visible = False

    def _toggle_settings_tab(self):
        """Переключает отображение вкладки настроек."""
        current_tab = self.notebook.index(self.notebook.select())
        if current_tab == 3:
            # Уже на настройках — возвращаемся на Главную
            self.notebook.select(0)
            self._settings_visible = False
            self._settings_btn.configure(bootstyle="light")
        else:
            # Переключаемся на настройки
            self.notebook.select(3)
            self._settings_visible = True
            self._settings_btn.configure(bootstyle="light")

    def _toggle_info_tab(self):
        """Переключает отображение вкладки инструкции."""
        current_tab = self.notebook.index(self.notebook.select())
        if current_tab == 4:
            # Уже на инструкции — возвращаемся на Главную
            self.notebook.select(0)
            self._info_visible = False
            self._info_btn.configure(bootstyle="info-outline")
        else:
            # Переключаемся на инструкцию
            self.notebook.select(4)
            self._info_visible = True
            self._info_btn.configure(bootstyle="info")

    def _apply_rounded_styles(self):
        """Увеличенные отступы на всех виджетах — мягкий, «пухлый» вид."""
        s = self.root.style

        # Кнопки: больше внутреннего пространства → визуально мягче
        s.configure('TButton', padding=(12, 6))

        # Поля ввода: выше, воздушнее
        s.configure('TEntry', padding=(8, 5))
        s.configure('TSpinbox', padding=(8, 5))
        s.configure('TCombobox', padding=(8, 5))

        # Радиокнопки и чекбоксы: немного больше отступа
        s.configure('TRadiobutton', padding=(6, 4))
        s.configure('TCheckbutton', padding=(6, 4))

        # Заголовки LabelFrame: шрифт Segoe UI
        s.configure('TLabelframe.Label', font=("Segoe UI", 10))

        # Вкладки Notebook: более высокие табы
        s.configure('TNotebook.Tab', padding=(14, 6))

    def _toggle_theme(self):
        """Переключает тему между тёмной и светлой."""
        if self._is_dark:
            self.root.style.theme_use("cosmo")
            self._theme_btn.configure(text="🌙 Переходи на тёмную сторону")
        else:
            self.root.style.theme_use("darkly")
            self._theme_btn.configure(text="☀️ Переходи на сторону добра")
        self._is_dark = not self._is_dark
        self._apply_rounded_styles()

    def run(self):
        self.root.mainloop()

    def destroy(self):
        self.root.destroy()
