"""
Вкладка "Результаты запросов" — отображает интерактивную таблицу запросов.
"""

import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from ioc_analyzer.adapters.gui.tabs.results_sections import rebuild_group_queries


class ResultsTab:
    """Вкладка для отображения результатов запросов."""

    def __init__(self, parent, controller):
        self.controller = controller
        self.frame = ttk.Frame(parent, padding=10)
        self.query_widgets = []

        self.chunk_size_vars = {}   # group_idx -> IntVar
        self.group_frames = {}      # group_idx -> rows_frame
        self.group_data_cache = {}  # group_idx -> group_data

        self._setup_ui()

    def _setup_ui(self):
        """Создание интерфейса."""
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

        self.canvas.bind("<Configure>", self._on_canvas_configure)
        self.canvas.bind("<Enter>", lambda e: self.canvas.bind_all("<MouseWheel>", self._on_mousewheel))
        self.canvas.bind("<Leave>", lambda e: self.canvas.unbind_all("<MouseWheel>"))

    def _on_canvas_configure(self, event):
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

        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
        self.query_widgets.clear()
        self.chunk_size_vars.clear()
        self.group_frames.clear()
        self.group_data_cache.clear()

        total_queries = sum(len(group['queries']) for group in query_data)
        self.info_label.config(
            text=f"Всего запросов: {total_queries} | Групп IOC: {len(query_data)}"
        )

        for group_idx, group in enumerate(query_data):
            self._create_group_section(group, group_idx)

    def _create_group_section(self, group_data, group_idx):
        """Создает секцию для группы запросов."""
        self.group_data_cache[group_idx] = group_data
        ioc_count = group_data.get('ioc_count', 0)

        if group_idx > 0:
            ttk.Separator(self.scrollable_frame, orient=HORIZONTAL).pack(fill=X, pady=10)

        group_frame = ttk.LabelFrame(
            self.scrollable_frame,
            text=f"  {group_data['group_name']}  ({ioc_count} IOC)",
            padding=10
        )
        group_frame.pack(fill=X, pady=(0, 5))

        top_row = ttk.Frame(group_frame)
        top_row.pack(fill=X, pady=(0, 8))

        ttk.Label(top_row, text=f"IOC: {ioc_count}", font=("TkDefaultFont", 10, "bold")).pack(side=LEFT)

        spin_frame = ttk.Frame(top_row)
        spin_frame.pack(side=RIGHT)
        ttk.Label(spin_frame, text="Макс. IOC в запросе:").pack(side=LEFT, padx=(0, 5))

        chunk_var = ttk.IntVar(value=ioc_count if ioc_count > 0 else 1)
        self.chunk_size_vars[group_idx] = chunk_var

        spinbox = ttk.Spinbox(
            spin_frame, from_=1, to=max(ioc_count, 1),
            textvariable=chunk_var, width=8,
            command=lambda gi=group_idx: rebuild_group_queries(self, gi)
        )
        spinbox.pack(side=LEFT)
        spinbox.bind('<Return>', lambda e, gi=group_idx: rebuild_group_queries(self, gi))

        # Заголовки
        header_frame = ttk.Frame(group_frame)
        header_frame.pack(fill=X, pady=(0, 5))

        col_config = [
            (0, 1, 80), (1, 1, 70), (2, 0, 50),
            (3, 4, 300), (4, 0, 100), (5, 0, 80),
        ]
        for col, weight, minsize in col_config:
            header_frame.columnconfigure(col, weight=weight, minsize=minsize)

        headers = ["IOC", "Система", "Часть", "Запрос", "", ""]
        for col, txt in enumerate(headers):
            if txt:
                ttk.Label(header_frame, text=txt, font=("TkDefaultFont", 9, "bold"), anchor=W).grid(row=0, column=col, sticky=EW, padx=5)

        rows_frame = ttk.Frame(group_frame)
        rows_frame.pack(fill=X)
        self.group_frames[group_idx] = rows_frame

        # Наполняем строки
        rebuild_group_queries(self, group_idx)

    def get_frame(self):
        return self.frame
