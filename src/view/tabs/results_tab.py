"""
Вкладка "Результаты запросов" - интерактивная таблица с поисковыми запросами.
Поддержка разбивки запросов на чанки (max IOC на запрос).
"""

import math
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from tkinter import messagebox


class ResultsTab:
    """Вкладка для отображения и управления результатами запросов."""

    def __init__(self, parent, controller):
        self.controller = controller
        self.frame = ttk.Frame(parent, padding=10)
        self.query_widgets = []

        # Данные для чанков
        self.chunk_size_vars = {}   # group_idx → IntVar (max IOC per query)
        self.group_frames = {}      # group_idx → rows_frame (контейнер строк)
        self.group_data_cache = {}  # group_idx → group_data

        self._setup_ui()

    def _setup_ui(self):
        """Создание элементов интерфейса."""
        info_frame = ttk.Frame(self.frame)
        info_frame.pack(fill=X, pady=(0, 10))

        self.info_label = ttk.Label(
            info_frame,
            text="Сгенерируйте отчет на вкладке 'Главная' для отображения запросов",
            font=("TkDefaultFont", 10)
        )
        self.info_label.pack()

        self.refresh_btn = ttk.Button(
            info_frame,
            text="Обновить данные",
            command=self.refresh_data,
            bootstyle=PRIMARY
        )
        self.refresh_btn.pack(pady=5)

        # Скроллируемая область
        canvas_frame = ttk.Frame(self.frame)
        canvas_frame.pack(fill=BOTH, expand=True)

        self.canvas = ttk.Canvas(canvas_frame)
        scrollbar = ttk.Scrollbar(canvas_frame, orient=VERTICAL, command=self.canvas.yview)

        self.scrollable_frame = ttk.Frame(self.canvas)
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )

        self._canvas_window = self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor=NW)
        self.canvas.configure(yscrollcommand=scrollbar.set)

        self.canvas.pack(side=LEFT, fill=BOTH, expand=True)
        scrollbar.pack(side=RIGHT, fill=Y)

        # Растягиваем содержимое на всю ширину canvas
        self.canvas.bind("<Configure>", self._on_canvas_configure)

        # Скролл колесиком только когда курсор над этим canvas
        self.canvas.bind("<Enter>", lambda e: self.canvas.bind_all("<MouseWheel>", self._on_mousewheel))
        self.canvas.bind("<Leave>", lambda e: self.canvas.unbind_all("<MouseWheel>"))

    def _on_canvas_configure(self, event):
        """Подгоняет ширину scrollable_frame под ширину canvas."""
        self.canvas.itemconfig(self._canvas_window, width=event.width)

    def _on_mousewheel(self, event):
        self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def refresh_data(self):
        """Загружает и отображает данные запросов."""
        query_data = self.controller.get_last_query_data()

        if not query_data:
            self.info_label.config(
                text="Нет данных для отображения. Сначала сгенерируйте отчет на вкладке 'Главная'."
            )
            return

        # Очищаем предыдущие виджеты и кеши
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
        self.query_widgets.clear()
        self.chunk_size_vars.clear()
        self.group_frames.clear()
        self.group_data_cache.clear()

        # Обновляем информационную метку
        total_queries = sum(len(group['queries']) for group in query_data)
        self.info_label.config(
            text=f"Всего запросов: {total_queries} | Групп IOC: {len(query_data)}"
        )

        for group_idx, group in enumerate(query_data):
            self._create_group_section(group, group_idx)

    def _create_group_section(self, group_data, group_idx):
        """Создает секцию для группы запросов одного типа IOC."""
        self.group_data_cache[group_idx] = group_data
        ioc_count = group_data.get('ioc_count', 0)

        if group_idx > 0:
            separator = ttk.Separator(self.scrollable_frame, orient=HORIZONTAL)
            separator.pack(fill=X, pady=10)

        group_frame = ttk.LabelFrame(
            self.scrollable_frame,
            text=f"  {group_data['group_name']}  ({ioc_count} IOC)",
            padding=10
        )
        group_frame.pack(fill=X, pady=(0, 5))

        # --- Верхняя строка: IOC count + Spinbox ---
        top_row = ttk.Frame(group_frame)
        top_row.pack(fill=X, pady=(0, 8))

        ttk.Label(
            top_row,
            text=f"IOC: {ioc_count}",
            font=("TkDefaultFont", 10, "bold")
        ).pack(side=LEFT)

        # Spinbox для chunk size (справа)
        spin_frame = ttk.Frame(top_row)
        spin_frame.pack(side=RIGHT)

        ttk.Label(spin_frame, text="Макс. IOC в запросе:").pack(side=LEFT, padx=(0, 5))

        chunk_var = ttk.IntVar(value=ioc_count if ioc_count > 0 else 1)
        self.chunk_size_vars[group_idx] = chunk_var

        spinbox = ttk.Spinbox(
            spin_frame,
            from_=1,
            to=max(ioc_count, 1),
            textvariable=chunk_var,
            width=8,
            command=lambda gi=group_idx: self._on_chunk_size_changed(gi)
        )
        spinbox.pack(side=LEFT)
        # Bind Enter key for manual input
        spinbox.bind('<Return>', lambda e, gi=group_idx: self._on_chunk_size_changed(gi))

        # --- Заголовок таблицы ---
        header_frame = ttk.Frame(group_frame)
        header_frame.pack(fill=X, pady=(0, 5))

        col_config = [
            (0, 1, 80),   # IOC
            (1, 1, 70),   # Система
            (2, 0, 50),   # Часть
            (3, 4, 300),  # Запрос
            (4, 0, 100),  # Копировать
            (5, 0, 80),   # Выполнено
        ]
        for col, weight, minsize in col_config:
            header_frame.columnconfigure(col, weight=weight, minsize=minsize)

        headers = ["IOC", "Система", "Часть", "Запрос", "", ""]
        for col, header_text in enumerate(headers):
            if header_text:
                lbl = ttk.Label(
                    header_frame,
                    text=header_text,
                    font=("TkDefaultFont", 9, "bold"),
                    anchor=W
                )
                lbl.grid(row=0, column=col, sticky=EW, padx=5)

        # --- Контейнер для строк запросов ---
        rows_frame = ttk.Frame(group_frame)
        rows_frame.pack(fill=X)
        self.group_frames[group_idx] = rows_frame

        # Первоначальная сборка (без разбивки)
        self._rebuild_group_queries(group_idx)

    def _on_chunk_size_changed(self, group_idx):
        """Обработчик изменения spinbox — пересобирает запросы для группы."""
        self._rebuild_group_queries(group_idx)

    def _rebuild_group_queries(self, group_idx):
        """Пересобирает строки запросов для группы с учётом chunk_size."""
        rows_frame = self.group_frames.get(group_idx)
        group_data = self.group_data_cache.get(group_idx)
        if not rows_frame or not group_data:
            return

        # Очищаем строки
        for w in rows_frame.winfo_children():
            w.destroy()

        # Удаляем старые виджеты этой группы из query_widgets
        self.query_widgets = [
            qw for qw in self.query_widgets if qw.get('_group_idx') != group_idx
        ]

        cleaned_iocs = group_data.get('cleaned_iocs', [])
        ioc_count = len(cleaned_iocs)
        chunk_var = self.chunk_size_vars.get(group_idx)

        chunk_size = ioc_count  # default — без разбивки
        if chunk_var:
            try:
                val = chunk_var.get()
                if 1 <= val <= ioc_count:
                    chunk_size = val
            except (ValueError, TypeError):
                pass

        # Разбиваем IOC на чанки
        if chunk_size >= ioc_count:
            chunks = [cleaned_iocs]
        else:
            chunks = [
                cleaned_iocs[i:i + chunk_size]
                for i in range(0, ioc_count, chunk_size)
            ]
        total_chunks = len(chunks)

        # Для каждого template × chunk создаём строку
        for query_info in group_data.get('queries', []):
            template = query_info.get('template', '')
            join_op = query_info.get('join_op', ' OR ')
            ioc_name = query_info['ioc_name']
            system = query_info['system']

            for chunk_idx, chunk in enumerate(chunks):
                if total_chunks > 1:
                    chunk_label = f"{chunk_idx + 1}/{total_chunks}"
                else:
                    chunk_label = ""

                query_text = self.controller.build_query(template, chunk, join_op)

                row_data = {
                    '_group_idx': group_idx,
                    'ioc_name': ioc_name,
                    'system': system,
                    'chunk_label': chunk_label,
                    'query': query_text,
                    'completed': False
                }
                self._create_query_row(rows_frame, row_data)

    def _create_query_row(self, parent, query_data):
        """Создает строку с одним запросом (6 столбцов)."""
        row_frame = ttk.Frame(parent)
        row_frame.pack(fill=X, pady=2)

        col_config = [
            (0, 1, 80),
            (1, 1, 70),
            (2, 0, 50),
            (3, 4, 300),
            (4, 0, 100),
            (5, 0, 80),
        ]
        for col, weight, minsize in col_config:
            row_frame.columnconfigure(col, weight=weight, minsize=minsize)

        widgets = query_data.copy()

        # Колонка 0: IOC Name
        ttk.Label(row_frame, text=query_data['ioc_name'], anchor=W).grid(
            row=0, column=0, sticky=EW, padx=5
        )

        # Колонка 1: Система (цветовая маркировка)
        system = query_data['system']
        if system == 'MP10':
            sys_style = 'warning'
        elif system == 'NAD':
            sys_style = 'info'
        else:
            sys_style = 'secondary'
        ttk.Label(
            row_frame, text=system, anchor=W,
            bootstyle=sys_style, font=("TkDefaultFont", 9, "bold")
        ).grid(row=0, column=1, sticky=EW, padx=5)

        # Колонка 2: Часть (chunk label)
        ttk.Label(row_frame, text=query_data.get('chunk_label', ''), anchor=W).grid(
            row=0, column=2, sticky=EW, padx=5
        )

        # Колонка 3: Запрос (readonly Entry)
        query_entry = ttk.Entry(row_frame)
        query_entry.insert(0, query_data['query'])
        query_entry.config(state='readonly')
        query_entry.grid(row=0, column=3, sticky=EW, padx=5)
        widgets['query_entry'] = query_entry

        # Колонка 4: Кнопка "Копировать"
        copy_btn = ttk.Button(
            row_frame,
            text="Копировать",
            command=lambda w=widgets: self._copy_query(w),
            bootstyle=INFO,
            width=12
        )
        copy_btn.grid(row=0, column=4, padx=5)

        # Колонка 5: Чекбокс "Выполнено"
        completed_var = ttk.BooleanVar(value=False)
        completed_check = ttk.Checkbutton(
            row_frame,
            text="Выполнено",
            variable=completed_var,
            bootstyle="success-round-toggle"
        )
        completed_check.grid(row=0, column=5, padx=5)
        widgets['completed_var'] = completed_var

        self.query_widgets.append(widgets)

    def _copy_query(self, widgets):
        """Копирует запрос в буфер обмена."""
        try:
            query_text = widgets['query']
            self.frame.clipboard_clear()
            self.frame.clipboard_append(query_text)
            self.frame.update()
            widgets['completed_var'].set(False)
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось скопировать запрос:\n{str(e)}")

    def get_frame(self):
        """Возвращает фрейм вкладки."""
        return self.frame
