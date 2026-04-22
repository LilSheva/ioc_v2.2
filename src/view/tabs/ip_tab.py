"""
Вкладка "IP управление" — списки IP на блокировку и разблокировку.
"""

import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from tkinter import messagebox


class IPTab:
    """Вкладка для отображения IP на блокировку/разблокировку."""

    def __init__(self, parent, controller):
        self.controller = controller
        self.frame = ttk.Frame(parent, padding=10)
        self._block_send_status: dict = {}
        self._last_block_ip_set: set = set()
        self._status_labels: dict = {}
        self._send_button = None
        self._setup_ui()

    def _setup_ui(self):
        """Создание элементов интерфейса."""
        # Информационная метка
        info_frame = ttk.Frame(self.frame)
        info_frame.pack(fill=X, pady=(0, 10))

        self.info_label = ttk.Label(
            info_frame,
            text="Сгенерируйте отчёт на вкладке «Главная» для отображения IP адресов",
            font=("TkDefaultFont", 10)
        )
        self.info_label.pack()

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

        self._canvas_window = self.canvas.create_window(
            (0, 0), window=self.scrollable_frame, anchor=NW
        )
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
        """Загружает и отображает IP данные."""
        ioc_data = self.controller.last_ioc_data
        mode = self.controller.get_mode()
        unblock_data = self.controller.get_last_unblock_data()

        # Очищаем предыдущие виджеты
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()

        if not ioc_data:
            self.info_label.config(
                text="Нет данных для отображения. Сначала сгенерируйте отчёт на вкладке «Главная»."
            )
            return

        # Собираем IP на блокировку
        block_ips = []
        ip_list = ioc_data.get('IP', [])
        for _raw, cleaned, meta in ip_list:
            if mode == "fstek" or meta.get("status") == "block":
                block_ips.append((cleaned, meta.get("filename", "")))

        # Сброс статусов отправки, если набор IP изменился
        current_set = {ip for ip, _ in block_ips}
        if current_set != self._last_block_ip_set:
            self._block_send_status = {}
            self._last_block_ip_set = current_set
        self._status_labels = {}
        self._send_button = None

        # Собираем IP на разблокировку (только ГосСОПКА)
        unblock_ips = []
        if mode == "gossopka" and unblock_data:
            for _raw, cleaned, meta in unblock_data.get('IP', []):
                unblock_ips.append((cleaned, meta.get("filename", "")))

        total = len(block_ips) + len(unblock_ips)
        self.info_label.config(text=f"Всего IP адресов: {total}")

        # Секция "На блокировку"
        self._create_block_section(block_ips)

        # Секция "На разблокировку" (только ГосСОПКА)
        if mode == "gossopka":
            self._create_unblock_section(unblock_ips)

    def _create_block_section(self, block_ips):
        """Секция IP на блокировку."""
        section = ttk.LabelFrame(
            self.scrollable_frame,
            text=f"  На блокировку ({len(block_ips)})  ",
            padding=10
        )
        section.pack(fill=X, pady=(0, 10))

        if not block_ips:
            ttk.Label(section, text="Нет IP на блокировку").pack(anchor=W)
            return

        # Кнопки: "Копировать все" и "Отправить на блокировку"
        btn_frame = ttk.Frame(section)
        btn_frame.pack(fill=X, pady=(0, 8))

        copy_all_btn = ttk.Button(
            btn_frame,
            text="Копировать все",
            command=lambda: self._copy_all_ips(block_ips),
            bootstyle=SUCCESS
        )
        copy_all_btn.pack(side=LEFT)

        self._send_button = ttk.Button(
            btn_frame,
            text="Отправить на блокировку",
            command=lambda: self._send_block_ips(block_ips),
            bootstyle=DANGER,
        )
        self._send_button.pack(side=LEFT, padx=(8, 0))

        # Заголовки (3 колонки)
        header = ttk.Frame(section)
        header.pack(fill=X, pady=(0, 4))
        header.columnconfigure(0, weight=1, minsize=180)
        header.columnconfigure(1, weight=2, minsize=260)
        header.columnconfigure(2, weight=1, minsize=180)

        ttk.Label(header, text="IP адрес", font=("TkDefaultFont", 9, "bold"), anchor=W).grid(
            row=0, column=0, sticky=EW, padx=5
        )
        ttk.Label(header, text="Источник", font=("TkDefaultFont", 9, "bold"), anchor=W).grid(
            row=0, column=1, sticky=EW, padx=5
        )
        ttk.Label(header, text="Статус отправки", font=("TkDefaultFont", 9, "bold"), anchor=W).grid(
            row=0, column=2, sticky=EW, padx=5
        )

        # Строки
        self._status_labels = {}
        for ip, filename in block_ips:
            row = ttk.Frame(section)
            row.pack(fill=X, pady=1)
            row.columnconfigure(0, weight=1, minsize=180)
            row.columnconfigure(1, weight=2, minsize=260)
            row.columnconfigure(2, weight=1, minsize=180)

            ttk.Label(row, text=ip, anchor=W).grid(row=0, column=0, sticky=EW, padx=5)
            ttk.Label(row, text=filename, anchor=W, bootstyle=SECONDARY).grid(
                row=0, column=1, sticky=EW, padx=5
            )

            status_info = self._block_send_status.get(ip)
            if status_info:
                text = status_info["text"]
                style = self._status_bootstyle(status_info["status"])
            else:
                text = "Не отправлено"
                style = SECONDARY

            lbl = ttk.Label(row, text=text, anchor=W, bootstyle=style)
            lbl.grid(row=0, column=2, sticky=EW, padx=5)
            self._status_labels[ip] = lbl

    @staticmethod
    def _status_bootstyle(status_code: str) -> str:
        """Маппит код статуса API в bootstyle для окраски label."""
        if status_code == "OK":
            return SUCCESS
        if status_code == "ERROR_DUPLICATE":
            return INFO
        if status_code == "ERROR_DENY_NET":
            return WARNING
        if not status_code:
            return SECONDARY
        return DANGER

    def _send_block_ips(self, block_ips):
        """Отправляет IP на блокировку через контроллер и обновляет колонку статуса."""
        ip_values = [ip for ip, _ in block_ips]
        if not ip_values:
            return

        # Блокируем кнопку на время запроса
        if self._send_button is not None:
            self._send_button.configure(state="disabled", text="Отправка...")
            self._send_button.update_idletasks()

        try:
            per_ip = self.controller.send_ips_to_api(ip_values)
        except Exception as e:
            per_ip = {ip: {"status": "UNEXPECTED", "text": f"Ошибка: {e.__class__.__name__}"}
                      for ip in ip_values}

        # Сохраняем и отрисовываем
        self._block_send_status.update(per_ip)
        for ip, lbl in self._status_labels.items():
            info = self._block_send_status.get(ip)
            if info:
                lbl.configure(text=info["text"], bootstyle=self._status_bootstyle(info["status"]))

        if self._send_button is not None:
            self._send_button.configure(state="normal", text="Отправить на блокировку")

        # Если API не настроен — подсказка пользователю
        first = next(iter(per_ip.values()), None)
        if first and first.get("status") == "NO_CONFIG":
            messagebox.showwarning(
                "API не настроен",
                "Укажите URL и ключ API на вкладке настроек, чтобы отправлять IP на блокировку."
            )

    def _create_unblock_section(self, unblock_ips):
        """Секция IP на разблокировку."""
        section = ttk.LabelFrame(
            self.scrollable_frame,
            text=f"  На разблокировку ({len(unblock_ips)})  ",
            padding=10
        )
        section.pack(fill=X, pady=(0, 10))

        # Информационное предупреждение
        notice = ttk.Label(
            section,
            text="ℹ Разблокировка выполняется вручную через веб-интерфейс системы — автоматическая отправка недоступна.",
            font=("TkDefaultFont", 9),
            bootstyle="warning",
            wraplength=600,
            justify=LEFT,
        )
        notice.pack(anchor=W, pady=(0, 8))

        if not unblock_ips:
            ttk.Label(section, text="Нет IP на разблокировку").pack(anchor=W)
            return

        # Кнопка "Копировать все"
        btn_frame = ttk.Frame(section)
        btn_frame.pack(fill=X, pady=(0, 8))

        copy_all_btn = ttk.Button(
            btn_frame,
            text="Копировать все",
            command=lambda: self._copy_all_ips(unblock_ips),
            bootstyle="warning"
        )
        copy_all_btn.pack(side=LEFT)

        # Заголовки
        header = ttk.Frame(section)
        header.pack(fill=X, pady=(0, 4))
        header.columnconfigure(0, weight=1, minsize=200)
        header.columnconfigure(1, weight=2, minsize=300)
        header.columnconfigure(2, weight=0, minsize=100)

        ttk.Label(header, text="IP адрес", font=("TkDefaultFont", 9, "bold"), anchor=W).grid(
            row=0, column=0, sticky=EW, padx=5
        )
        ttk.Label(header, text="Источник", font=("TkDefaultFont", 9, "bold"), anchor=W).grid(
            row=0, column=1, sticky=EW, padx=5
        )

        # Строки с индивидуальной кнопкой копирования
        for ip, filename in unblock_ips:
            row = ttk.Frame(section)
            row.pack(fill=X, pady=1)
            row.columnconfigure(0, weight=1, minsize=200)
            row.columnconfigure(1, weight=2, minsize=300)
            row.columnconfigure(2, weight=0, minsize=100)

            ttk.Label(row, text=ip, anchor=W).grid(row=0, column=0, sticky=EW, padx=5)
            ttk.Label(row, text=filename, anchor=W, bootstyle=SECONDARY).grid(
                row=0, column=1, sticky=EW, padx=5
            )
            ttk.Button(
                row,
                text="Копировать",
                command=lambda v=ip: self._copy_single_ip(v),
                bootstyle=INFO,
                width=12
            ).grid(row=0, column=2, padx=5)

    def _copy_all_ips(self, ip_list):
        """Копирует все IP в буфер обмена (по одному на строку)."""
        try:
            text = "\n".join(ip for ip, _ in ip_list)
            self.frame.clipboard_clear()
            self.frame.clipboard_append(text)
            self.frame.update()
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось скопировать:\n{str(e)}")

    def _copy_single_ip(self, ip):
        """Копирует один IP в буфер обмена."""
        try:
            self.frame.clipboard_clear()
            self.frame.clipboard_append(ip)
            self.frame.update()
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось скопировать:\n{str(e)}")

    def get_frame(self):
        """Возвращает фрейм вкладки."""
        return self.frame
