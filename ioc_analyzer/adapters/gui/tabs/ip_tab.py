"""
Вкладка "IP управление" — списки IP на блокировку и разблокировку.
"""

import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from tkinter import messagebox

from ioc_analyzer.adapters.gui.tabs.ip_sections import (
    create_block_section,
    create_unblock_section,
    status_bootstyle
)


class IPTab:
    """Вкладка для отображения IP на блокировку/разблокировку."""

    def __init__(self, parent, controller):
        self.controller = controller
        self.frame = ttk.Frame(parent, padding=10)
        self.block_send_status: dict = {}
        self._last_block_ip_set: set = set()
        self.status_labels: dict = {}
        self.send_button = None
        self._setup_ui()

    def _setup_ui(self):
        """Создание элементов интерфейса."""
        info_frame = ttk.Frame(self.frame)
        info_frame.pack(fill=X, pady=(0, 10))

        self.info_label = ttk.Label(
            info_frame,
            text="Сгенерируйте отчёт на вкладке «Главная» для отображения IP адресов",
            font=("TkDefaultFont", 10)
        )
        self.info_label.pack()

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
        for ioc in ip_list:
            # ioc - это доменный объект IOC
            if mode == "fstek" or ioc.status == "block":
                block_ips.append((ioc.clean_value, ioc.source_file))

        # Сброс статусов отправки, если набор IP изменился
        current_set = {ip for ip, _ in block_ips}
        if current_set != self._last_block_ip_set:
            self.block_send_status = {}
            self._last_block_ip_set = current_set
        self.status_labels = {}
        self.send_button = None

        # Собираем IP на разблокировку (только ГосСОПКА)
        unblock_ips = []
        if mode == "gossopka" and unblock_data:
            for ioc in unblock_data.get('IP', []):
                unblock_ips.append((ioc.clean_value, ioc.source_file))

        total = len(block_ips) + len(unblock_ips)
        self.info_label.config(text=f"Всего IP адресов: {total}")

        # Секция "На блокировку"
        create_block_section(self, self.scrollable_frame, block_ips)

        # Секция "На разблокировку" (только ГосСОПКА)
        if mode == "gossopka":
            create_unblock_section(self, self.scrollable_frame, unblock_ips)

    def send_block_ips(self, block_ips):
        """Отправляет IP на блокировку через контроллер."""
        if not block_ips:
            return

        if self.send_button is not None:
            self.send_button.configure(state="disabled", text="Отправка...")
            self.send_button.update_idletasks()

        try:
            per_ip = self.controller.send_ips_to_api(block_ips)
        except Exception as e:
            per_ip = {ip: {"status": "UNEXPECTED", "text": f"Ошибка: {e.__class__.__name__}"}
                      for ip, _ in block_ips}

        self.block_send_status.update(per_ip)
        for ip, lbl in self.status_labels.items():
            info = self.block_send_status.get(ip)
            if info:
                lbl.configure(text=info["text"], bootstyle=status_bootstyle(info["status"]))

        if self.send_button is not None:
            self.send_button.configure(state="normal", text="Отправить на блокировку")

        first = next(iter(per_ip.values()), None)
        if first and first.get("status") == "NO_CONFIG":
            messagebox.showwarning(
                "API не настроен",
                "Укажите URL и ключ API на вкладке настроек, чтобы отправлять IP на блокировку."
            )

    def copy_all_ips(self, ip_list):
        """Копирует все IP в буфер обмена."""
        try:
            text = "\n".join(ip for ip, _ in ip_list)
            self.frame.clipboard_clear()
            self.frame.clipboard_append(text)
            self.frame.update()
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось скопировать:\n{str(e)}")

    def copy_single_ip(self, ip):
        """Копирует один IP в буфер обмена."""
        try:
            self.frame.clipboard_clear()
            self.frame.clipboard_append(ip)
            self.frame.update()
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось скопировать:\n{str(e)}")

    def get_frame(self):
        return self.frame
