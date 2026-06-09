"""Вкладка "Главная" с полями управления и логированием."""

import os
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from tkinter import filedialog, messagebox, END, NORMAL, DISABLED, WORD

from ioc_analyzer.adapters.gui.tabs.main_actions import run_generation_flow


class MainTab:
    """Вкладка для выбора файлов и запуска обработки."""

    def __init__(self, parent, controller):
        self.controller = controller
        self.frame = ttk.Frame(parent, padding=10)
        self._setup_ui()

    def _setup_ui(self):
        """Создание элементов интерфейса."""
        # 1. Выбор файлов
        file_frame = ttk.LabelFrame(self.frame, text="Выбор файлов", padding=10)
        file_frame.pack(fill=X, pady=(0, 8))

        tree_frame = ttk.Frame(file_frame)
        tree_frame.pack(fill=X, pady=(0, 8))

        self.file_tree = ttk.Treeview(
            tree_frame, columns=("name",), show="", height=5, selectmode="browse"
        )
        self.file_tree.column("name", stretch=True, anchor=W)
        tree_scroll = ttk.Scrollbar(tree_frame, orient=VERTICAL, command=self.file_tree.yview)
        self.file_tree.configure(yscrollcommand=tree_scroll.set)
        self.file_tree.pack(side=LEFT, fill=X, expand=True)
        tree_scroll.pack(side=RIGHT, fill=Y)

        btn_frame = ttk.Frame(file_frame)
        btn_frame.pack(fill=X)

        self.add_files_btn = ttk.Button(btn_frame, text="Добавить файлы...", command=self._add_files, bootstyle=PRIMARY)
        self.add_files_btn.pack(side=LEFT, padx=(0, 5))

        self.clear_files_btn = ttk.Button(btn_frame, text="Очистить список", command=self._clear_files, bootstyle="secondary-outline")
        self.clear_files_btn.pack(side=LEFT)

        self.file_count_label = ttk.Label(btn_frame, text="Файлов: 0", bootstyle=SECONDARY)
        self.file_count_label.pack(side=RIGHT, padx=(10, 0))

        # 2. Параметры отчёта
        params_container = ttk.Frame(self.frame)
        params_container.pack(fill=X, pady=(0, 8))

        left_side = ttk.Frame(params_container)
        left_side.pack(side=LEFT, fill=BOTH, expand=True)

        params_frame = ttk.LabelFrame(left_side, text="Параметры отчёта", padding=10)
        params_frame.pack(fill=X)
        params_frame.columnconfigure(1, weight=1)

        # Режим работы
        ttk.Label(params_frame, text="Режим работы:", width=16, anchor=W).grid(row=0, column=0, sticky=W, padx=(0, 10), pady=3)
        mode_row = ttk.Frame(params_frame)
        mode_row.grid(row=0, column=1, sticky=W, pady=3)
        self.mode_var = ttk.StringVar(value="fstek")
        ttk.Radiobutton(mode_row, text="ФСТЕК", variable=self.mode_var, value="fstek", command=self._on_mode_changed, bootstyle="primary").pack(side=LEFT, padx=(0, 15))
        ttk.Radiobutton(mode_row, text="ГосСОПКА", variable=self.mode_var, value="gossopka", command=self._on_mode_changed, bootstyle="primary").pack(side=LEFT)

        # Очистка URI
        ttk.Label(params_frame, text="Очистка URI:", width=16, anchor=W).grid(row=1, column=0, sticky=W, padx=(0, 10), pady=3)
        uri_row = ttk.Frame(params_frame)
        uri_row.grid(row=1, column=1, sticky=W, pady=3)
        self.uri_clean_var = ttk.StringVar(value="domain")
        ttk.Radiobutton(uri_row, text="До уникального префикса", variable=self.uri_clean_var, value="unique", command=self._on_uri_mode_changed, bootstyle="info").pack(side=LEFT, padx=(0, 15))
        ttk.Radiobutton(uri_row, text="Только домен", variable=self.uri_clean_var, value="domain", command=self._on_uri_mode_changed, bootstyle="info").pack(side=LEFT)

        # Бюллетень
        ttk.Label(params_frame, text="Бюллетень:", width=16, anchor=W).grid(row=2, column=0, sticky=W, padx=(0, 10), pady=3)
        bulletin_row = ttk.Frame(params_frame)
        bulletin_row.grid(row=2, column=1, sticky=EW, pady=3)
        bulletin_row.columnconfigure(0, weight=1)
        self.bulletin_entry = ttk.Entry(bulletin_row)
        self.bulletin_entry.grid(row=0, column=0, sticky=EW)
        self.bulletin_hint = ttk.Label(bulletin_row, text="(для режима ФСТЕК)", font=("Segoe UI", 9), bootstyle=SECONDARY)
        self.bulletin_hint.grid(row=0, column=1, padx=(10, 0))

        self.generate_btn = ttk.Button(left_side, text="Сформировать отчёты", command=self._generate_reports, bootstyle=SUCCESS)
        self.generate_btn.pack(fill=X, pady=(8, 0), ipady=6)

        # 3. Журнал работы
        log_frame = ttk.LabelFrame(self.frame, text="Журнал работы", padding=10)
        log_frame.pack(fill=BOTH, expand=True)

        log_top = ttk.Frame(log_frame)
        log_top.pack(fill=X, pady=(0, 5))
        self.clear_log_btn = ttk.Button(log_top, text="Очистить", command=self._clear_log, bootstyle="secondary-outline")
        self.clear_log_btn.pack(side=RIGHT)

        log_text_frame = ttk.Frame(log_frame)
        log_text_frame.pack(fill=BOTH, expand=True)
        log_scrollbar = ttk.Scrollbar(log_text_frame)
        log_scrollbar.pack(side=RIGHT, fill=Y)

        self.log_text = ttk.Text(log_text_frame, height=10, yscrollcommand=log_scrollbar.set, wrap=WORD, state=DISABLED, font=("Consolas", 10))
        self.log_text.pack(side=LEFT, fill=BOTH, expand=True)
        log_scrollbar.config(command=self.log_text.yview)

    def _add_files(self):
        file_paths = filedialog.askopenfilenames(
            title="Выберите .docx файлы",
            filetypes=[("Word Documents", "*.docx"), ("All Files", "*.*")]
        )
        if file_paths:
            added = self.controller.add_files(list(file_paths))
            self._update_file_list()
            self.log(f"Добавлено файлов: {added}")

            if self.mode_var.get() == "fstek":
                auto_bulletin = self.controller.auto_fill_bulletin()
                if auto_bulletin:
                    self.bulletin_entry.delete(0, END)
                    self.bulletin_entry.insert(0, auto_bulletin)
                    self.log(f"Бюллетень определен автоматически: {auto_bulletin}")

    def _clear_files(self):
        if len(self.file_tree.get_children()) > 0:
            confirm = messagebox.askyesno("Подтверждение", "Очистить список выбранных файлов?")
            if confirm:
                self.controller.clear_files()
                self._update_file_list()
                if self.mode_var.get() == "fstek":
                    self.bulletin_entry.delete(0, END)
                self.log("Список файлов очищен.")

    def _update_file_list(self):
        for item in self.file_tree.get_children():
            self.file_tree.delete(item)
        files = self.controller.get_selected_files()
        for file_path in files:
            self.file_tree.insert("", END, values=(os.path.basename(file_path),))
        self.file_count_label.configure(text=f"Файлов: {len(files)}")

    def _generate_reports(self):
        run_generation_flow(self)

    def _clear_log(self):
        self.log_text.config(state=NORMAL)
        self.log_text.delete(1.0, END)
        self.log_text.config(state=DISABLED)

    def log(self, message):
        self.log_text.config(state=NORMAL)
        self.log_text.insert(END, message + "\n")
        self.log_text.see(END)
        self.log_text.config(state=DISABLED)
        self.log_text.update_idletasks()

    def _on_mode_changed(self):
        mode = self.mode_var.get()
        if mode == "fstek":
            self.bulletin_hint.config(text="(автозаполнение или ввод вручную)")
            self.bulletin_entry.config(state=NORMAL)
            if self.controller.get_selected_files():
                auto_bulletin = self.controller.auto_fill_bulletin()
                if auto_bulletin:
                    self.bulletin_entry.delete(0, END)
                    self.bulletin_entry.insert(0, auto_bulletin)
        else:
            self.bulletin_hint.config(text="(игнорируется в режиме ГосСОПКА)")

    def _on_uri_mode_changed(self):
        pass

    def get_frame(self):
        return self.frame
