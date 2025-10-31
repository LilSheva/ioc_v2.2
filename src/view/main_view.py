"""
Главное окно приложения с вкладками.
"""

import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from .tabs.main_tab import MainTab
from .tabs.settings_tab import SettingsTab
from .tabs.results_tab import ResultsTab


class MainView:
    """Главное окно приложения."""
    
    def __init__(self, controller):
        """
        Инициализация главного окна.
        
        Args:
            controller: Контроллер приложения
        """
        self.controller = controller
        
        # Создание главного окна
        self.root = ttk.Window(
            title="IOC Parser - Извлечение индикаторов компрометации",
            themename="darkly",
            size=(1200, 800),
            resizable=(True, True)
        )
        
        # Установка минимального размера окна
        self.root.minsize(900, 600)
        
        # Центрирование окна
        self.root.position_center()
        
        # Создание интерфейса
        self._setup_ui()
    
    def _setup_ui(self):
        """Создание элементов интерфейса."""
        # Заголовок приложения
        header_frame = ttk.Frame(self.root, padding=10)
        header_frame.pack(fill=X, side=TOP)
        
        title_label = ttk.Label(
            header_frame,
            text="🔍 IOC Parser - Анализатор индикаторов компрометации",
            font=("TkDefaultFont", 16, "bold"),
            bootstyle=PRIMARY
        )
        title_label.pack()
        
        subtitle_label = ttk.Label(
            header_frame,
            text="Извлечение IOC из документов Word и генерация отчетов",
            font=("TkDefaultFont", 10)
        )
        subtitle_label.pack(pady=(5, 0))
        
        # Разделитель
        separator = ttk.Separator(self.root, orient=HORIZONTAL)
        separator.pack(fill=X, padx=10)
        
        # Создание Notebook с вкладками
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=BOTH, expand=True, padx=10, pady=10)
        
        # Создание вкладок
        self.main_tab = MainTab(self.notebook, self.controller)
        self.settings_tab = SettingsTab(self.notebook, self.controller)
        self.results_tab = ResultsTab(self.notebook, self.controller)
        
        # Добавление вкладок в Notebook
        self.notebook.add(self.main_tab.get_frame(), text="  🏠 Главная  ")
        self.notebook.add(self.settings_tab.get_frame(), text="  ⚙️ Настройка IOC  ")
        self.notebook.add(self.results_tab.get_frame(), text="  📊 Результаты запросов  ")
        
        # Футер с информацией
        footer_frame = ttk.Frame(self.root, padding=10)
        footer_frame.pack(fill=X, side=BOTTOM)
        
        footer_label = ttk.Label(
            footer_frame,
            text="IOC Parser v2.2 | Поддержка форматов: .docx | Отчеты: .xlsx, .txt",
            font=("TkDefaultFont", 9),
            bootstyle=SECONDARY
        )
        footer_label.pack()
        
        # Биндинг событий
        self.notebook.bind("<<NotebookTabChanged>>", self._on_tab_changed)
    
    def _on_tab_changed(self, event):
        """
        Обработчик переключения вкладок.
        
        Args:
            event: Событие переключения вкладки
        """
        current_tab = self.notebook.index(self.notebook.select())
        
        # Если переключились на вкладку "Результаты запросов"
        if current_tab == 2:
            # Автоматически обновляем данные, если они есть
            if self.controller.get_last_query_data():
                self.results_tab.refresh_data()
    
    def run(self):
        """Запуск главного цикла приложения."""
        self.root.mainloop()
    
    def destroy(self):
        """Закрытие приложения."""
        self.root.destroy()
