"""
Вкладка "Результаты запросов" - интерактивная таблица с поисковыми запросами.
"""

import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from tkinter import messagebox


class ResultsTab:
    """Вкладка для отображения и управления результатами запросов."""
    
    def __init__(self, parent, controller):
        """
        Инициализация вкладки.
        
        Args:
            parent: Родительский виджет (Notebook)
            controller: Контроллер приложения
        """
        self.controller = controller
        self.frame = ttk.Frame(parent, padding=10)
        self.query_widgets = []  # Список виджетов для каждого запроса
        
        self._setup_ui()
    
    def _setup_ui(self):
        """Создание элементов интерфейса."""
        # Верхняя панель с информацией
        info_frame = ttk.Frame(self.frame)
        info_frame.pack(fill=X, pady=(0, 10))
        
        self.info_label = ttk.Label(
            info_frame,
            text="ℹ️ Сгенерируйте отчет на вкладке 'Главная' для отображения запросов",
            font=("TkDefaultFont", 10)
        )
        self.info_label.pack()
        
        # Кнопка обновления
        self.refresh_btn = ttk.Button(
            info_frame,
            text="🔄 Обновить данные",
            command=self.refresh_data,
            bootstyle=PRIMARY
        )
        self.refresh_btn.pack(pady=5)
        
        # Скроллируемая область для таблицы
        canvas_frame = ttk.Frame(self.frame)
        canvas_frame.pack(fill=BOTH, expand=True)
        
        self.canvas = ttk.Canvas(canvas_frame)
        scrollbar = ttk.Scrollbar(canvas_frame, orient=VERTICAL, command=self.canvas.yview)
        
        self.scrollable_frame = ttk.Frame(self.canvas)
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )
        
        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor=NW)
        self.canvas.configure(yscrollcommand=scrollbar.set)
        
        self.canvas.pack(side=LEFT, fill=BOTH, expand=True)
        scrollbar.pack(side=RIGHT, fill=Y)
        
        # Биндинг для прокрутки колесом мыши
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)
    
    def _on_mousewheel(self, event):
        """Обработчик прокрутки колесом мыши."""
        self.canvas.yview_scroll(int(-1*(event.delta/120)), "units")
    
    def refresh_data(self):
        """Загружает и отображает данные запросов."""
        query_data = self.controller.get_last_query_data()
        
        if not query_data:
            self.info_label.config(
                text="⚠️ Нет данных для отображения. Сначала сгенерируйте отчет на вкладке 'Главная'."
            )
            return
        
        # Очищаем предыдущие виджеты
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
        self.query_widgets.clear()
        
        # Обновляем информационную метку
        total_queries = sum(len(group['queries']) for group in query_data)
        self.info_label.config(
            text=f"📊 Всего запросов: {total_queries} | Групп IOC: {len(query_data)}"
        )
        
        # Создаем таблицу для каждой группы
        for group_idx, group in enumerate(query_data):
            self._create_group_section(group, group_idx)
    
    def _create_group_section(self, group_data, group_idx):
        """
        Создает секцию для группы запросов одного типа IOC.
        
        Args:
            group_data: Данные группы (имя и список запросов)
            group_idx: Индекс группы
        """
        # Разделитель между группами
        if group_idx > 0:
            separator = ttk.Separator(self.scrollable_frame, orient=HORIZONTAL)
            separator.pack(fill=X, pady=10)
        
        # Заголовок группы
        group_frame = ttk.LabelFrame(
            self.scrollable_frame,
            text=f"🔍 {group_data['group_name']}",
            padding=10
        )
        group_frame.pack(fill=X, pady=(0, 5))
        
        # Заголовок таблицы
        header_frame = ttk.Frame(group_frame)
        header_frame.pack(fill=X, pady=(0, 5))
        
        # Настраиваем сетку столбцов
        header_frame.columnconfigure(0, weight=1, minsize=150)  # IOC Name
        header_frame.columnconfigure(1, weight=1, minsize=100)  # System
        header_frame.columnconfigure(2, weight=4, minsize=300)  # Query
        header_frame.columnconfigure(3, weight=0, minsize=100)  # Copy Button
        header_frame.columnconfigure(4, weight=0, minsize=100)  # Checkbox
        
        headers = ["Имя IOC", "Система", "Запрос", "", ""]
        for col, header_text in enumerate(headers):
            if header_text:  # Пропускаем пустые заголовки для кнопки и чекбокса
                lbl = ttk.Label(
                    header_frame,
                    text=header_text,
                    font=("TkDefaultFont", 9, "bold"),
                    anchor=W
                )
                lbl.grid(row=0, column=col, sticky=EW, padx=5)
        
        # Строки с запросами
        for query_idx, query in enumerate(group_data['queries']):
            self._create_query_row(group_frame, query, query_idx)
    
    def _create_query_row(self, parent, query_data, row_idx):
        """
        Создает строку с одним запросом.
        
        Args:
            parent: Родительский фрейм
            query_data: Данные запроса
            row_idx: Индекс строки
        """
        row_frame = ttk.Frame(parent)
        row_frame.pack(fill=X, pady=2)
        
        # Настраиваем сетку столбцов (такую же, как в заголовке)
        row_frame.columnconfigure(0, weight=1, minsize=150)
        row_frame.columnconfigure(1, weight=1, minsize=100)
        row_frame.columnconfigure(2, weight=4, minsize=300)
        row_frame.columnconfigure(3, weight=0, minsize=100)
        row_frame.columnconfigure(4, weight=0, minsize=100)
        
        # Словарь для хранения виджетов
        widgets = query_data.copy()
        
        # Колонка 1: Имя IOC
        ioc_label = ttk.Label(row_frame, text=query_data['ioc_name'], anchor=W)
        ioc_label.grid(row=0, column=0, sticky=EW, padx=5)
        
        # Колонка 2: Система
        system_label = ttk.Label(row_frame, text=query_data['system'], anchor=W)
        system_label.grid(row=0, column=1, sticky=EW, padx=5)
        
        # Колонка 3: Запрос (в Entry для возможности выделения)
        query_entry = ttk.Entry(row_frame)
        query_entry.insert(0, query_data['query'])
        query_entry.config(state='readonly')
        query_entry.grid(row=0, column=2, sticky=EW, padx=5)
        widgets['query_entry'] = query_entry
        
        # Колонка 4: Кнопка "Копировать"
        copy_btn = ttk.Button(
            row_frame,
            text="📋 Копировать",
            command=lambda w=widgets: self._copy_query(w),
            bootstyle=INFO,
            width=12
        )
        copy_btn.grid(row=0, column=3, padx=5)
        
        # Колонка 5: Чекбокс "Выполнено"
        completed_var = ttk.BooleanVar(value=query_data.get('completed', False))
        completed_check = ttk.Checkbutton(
            row_frame,
            text="Выполнено",
            variable=completed_var,
            bootstyle="success-round-toggle"
        )
        completed_check.grid(row=0, column=4, padx=5)
        widgets['completed_var'] = completed_var
        
        # Сохраняем виджеты
        self.query_widgets.append(widgets)
    
    def _copy_query(self, widgets):
        """
        Копирует запрос в буфер обмена и снимает чекбокс.
        
        Args:
            widgets: Словарь с виджетами строки
        """
        try:
            # Получаем текст запроса
            query_text = widgets['query']
            
            # Копируем в буфер обмена
            self.frame.clipboard_clear()
            self.frame.clipboard_append(query_text)
            self.frame.update()
            
            # Снимаем чекбокс "Выполнено"
            widgets['completed_var'].set(False)
            
            # Визуальная обратная связь
            # (можно добавить временное изменение цвета кнопки)
            
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось скопировать запрос:\n{str(e)}")
    
    def get_frame(self):
        """Возвращает фрейм вкладки."""
        return self.frame
