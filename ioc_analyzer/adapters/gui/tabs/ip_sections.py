"""
Вспомогательные панели для вкладки "IP управление".
"""

import ttkbootstrap as ttk
from ttkbootstrap.constants import *


def status_bootstyle(status_code: str) -> str:
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


def create_block_section(tab_obj, parent_frame, block_ips) -> None:
    """Секция IP на блокировку."""
    section = ttk.LabelFrame(
        parent_frame,
        text=f"  На блокировку ({len(block_ips)})  ",
        padding=10
    )
    section.pack(fill=X, pady=(0, 10))

    if not block_ips:
        ttk.Label(section, text="Нет IP на блокировку").pack(anchor=W)
        return

    btn_frame = ttk.Frame(section)
    btn_frame.pack(fill=X, pady=(0, 8))

    copy_all_btn = ttk.Button(
        btn_frame,
        text="Копировать все",
        command=lambda: tab_obj.copy_all_ips(block_ips),
        bootstyle=SUCCESS
    )
    copy_all_btn.pack(side=LEFT)

    tab_obj.send_button = ttk.Button(
        btn_frame,
        text="Отправить на блокировку",
        command=lambda: tab_obj.send_block_ips(block_ips),
        bootstyle=DANGER,
    )
    tab_obj.send_button.pack(side=LEFT, padx=(8, 0))

    # Заголовки
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

        status_info = tab_obj.block_send_status.get(ip)
        if status_info:
            text = status_info["text"]
            style = status_bootstyle(status_info["status"])
        else:
            text = "Не отправлено"
            style = SECONDARY

        lbl = ttk.Label(row, text=text, anchor=W, bootstyle=style)
        lbl.grid(row=0, column=2, sticky=EW, padx=5)
        tab_obj.status_labels[ip] = lbl


def create_unblock_section(tab_obj, parent_frame, unblock_ips) -> None:
    """Секция IP на разблокировку."""
    section = ttk.LabelFrame(
        parent_frame,
        text=f"  На разблокировку ({len(unblock_ips)})  ",
        padding=10
    )
    section.pack(fill=X, pady=(0, 10))

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

    btn_frame = ttk.Frame(section)
    btn_frame.pack(fill=X, pady=(0, 8))

    copy_all_btn = ttk.Button(
        btn_frame,
        text="Копировать все",
        command=lambda: tab_obj.copy_all_ips(unblock_ips),
        bootstyle="warning"
    )
    copy_all_btn.pack(side=LEFT)

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
            command=lambda v=ip: tab_obj.copy_single_ip(v),
            bootstyle=INFO,
            width=12
        ).grid(row=0, column=2, padx=5)
