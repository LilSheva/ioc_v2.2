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

        # Кнопки справа: настройки ⚙ и тоглер темы
        self._is_dark = True

        self._theme_btn = ttk.Button(
            header_frame,
            text="☀️ Переходи на сторону добра",
            command=self._toggle_theme,
            bootstyle="warning-outline",
        )
        self._theme_btn.pack(side=RIGHT)

        self._settings_btn = ttk.Button(
            header_frame,
            text="⚙",
            command=self._open_settings_dialog,
            bootstyle="secondary-outline",
            width=3,
        )
        self._settings_btn.pack(side=RIGHT, padx=(0, 8))

        # ── Разделитель ──
        ttk.Separator(self.root, orient=HORIZONTAL).pack(fill=X, padx=10)

        # ── Вкладки ──
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=BOTH, expand=True, padx=10, pady=(8, 5))

        self.main_tab = MainTab(self.notebook, self.controller)
        self.results_tab = ResultsTab(self.notebook, self.controller)
        self.ip_tab = IPTab(self.notebook, self.controller)

        self.notebook.add(self.main_tab.get_frame(), text="  Главная  ")
        self.notebook.add(self.results_tab.get_frame(), text="  Результаты запросов  ")
        self.notebook.add(self.ip_tab.get_frame(), text="  IP управление  ")

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

        # ── Кнопка "?" — инструкция в правом нижнем углу ──
        self._info_btn = ttk.Button(
            self.root,
            text="?",
            command=self._open_info_dialog,
            bootstyle="info",
            width=3,
        )
        self._info_btn.place(relx=1.0, rely=1.0, anchor="se", x=-20, y=-20)

        self.notebook.bind("<<NotebookTabChanged>>", self._on_tab_changed)

    def _on_tab_changed(self, event):
        current_tab = self.notebook.index(self.notebook.select())
        if current_tab == 1:
            if self.controller.get_last_query_data():
                self.results_tab.refresh_data()
        elif current_tab == 2:
            self.ip_tab.refresh_data()

    def _open_settings_dialog(self):
        """Открывает настройки IOC в модальном окне."""
        dialog = ttk.Toplevel(self.root)
        dialog.title("Настройка IOC")
        dialog.geometry("950x650")
        dialog.transient(self.root)
        dialog.grab_set()

        # Центрируем относительно главного окна
        dialog.update_idletasks()
        x = self.root.winfo_x() + (self.root.winfo_width() - 950) // 2
        y = self.root.winfo_y() + (self.root.winfo_height() - 650) // 2
        dialog.geometry(f"+{x}+{y}")

        settings_tab = SettingsTab(dialog, self.controller)
        settings_tab.get_frame().pack(fill=BOTH, expand=True)

    def _open_info_dialog(self):
        """Открывает инструкцию в модальном окне."""
        dialog = ttk.Toplevel(self.root)
        dialog.title("Инструкция")
        dialog.geometry("850x600")
        dialog.transient(self.root)

        # Центрируем относительно главного окна
        dialog.update_idletasks()
        x = self.root.winfo_x() + (self.root.winfo_width() - 850) // 2
        y = self.root.winfo_y() + (self.root.winfo_height() - 600) // 2
        dialog.geometry(f"+{x}+{y}")

        info_tab = InfoTab(dialog, self.controller)
        info_tab.get_frame().pack(fill=BOTH, expand=True)

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
