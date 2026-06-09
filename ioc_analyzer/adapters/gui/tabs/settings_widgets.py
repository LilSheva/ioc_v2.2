"""
Формы и редакторы списков для вкладки "Настройка IOC".
"""

import ttkbootstrap as ttk
from ttkbootstrap.constants import *


def create_text_field(parent, label: str, value: str, widgets_dict: dict, key: str) -> None:
    """Создаёт строку ввода с текстовой меткой."""
    row_frame = ttk.Frame(parent)
    row_frame.pack(fill=X, pady=2)

    lbl = ttk.Label(row_frame, text=label, width=22, anchor=W)
    lbl.pack(side=LEFT, padx=(0, 10))

    entry = ttk.Entry(row_frame)
    entry.insert(0, value)
    entry.pack(side=LEFT, fill=X, expand=True)

    widgets_dict[key] = entry


def add_list_row(container, value: str, entries_list: list) -> None:
    """Добавляет строку в редактор списков."""
    row_frame = ttk.Frame(container)
    row_frame.pack(fill=X, pady=1)

    entry = ttk.Entry(row_frame)
    entry.insert(0, value)
    entry.pack(side=LEFT, fill=X, expand=True, padx=(0, 5))

    def remove_row():
        if entry in entries_list:
            entries_list.remove(entry)
        row_frame.destroy()

    del_btn = ttk.Button(
        row_frame, text="✕",
        command=remove_row,
        bootstyle="danger-outline", width=3
    )
    del_btn.pack(side=RIGHT)
    entries_list.append(entry)


def create_list_editor(parent, label: str, values: list, widgets: dict, key: str) -> None:
    """Создаёт редактор списка строк (blacklist / exclusions)."""
    frame = ttk.LabelFrame(parent, text=label, padding=5)
    frame.pack(fill=X, pady=(0, 5))

    rows_frame = ttk.Frame(frame)
    rows_frame.pack(fill=X)

    entries = []
    widgets[key] = entries

    for v in values:
        add_list_row(rows_frame, v, entries)

    add_btn = ttk.Button(
        frame, text="+ Добавить",
        command=lambda rf=rows_frame, el=entries: add_list_row(rf, '', el),
        bootstyle="secondary-outline"
    )
    add_btn.pack(anchor=W, pady=(4, 0))


def create_ioc_block(tab_obj, parent_frame, index: int, ioc_config: dict) -> None:
    """Отрисовывает один конфигурационный блок настроек типа IOC."""
    block_frame = ttk.LabelFrame(
        parent_frame,
        text=f"{ioc_config['name']} - {ioc_config['report_type']}",
        padding=10
    )
    block_frame.pack(fill=X, pady=(0, 5))

    widgets = {'index': index, 'frame': block_frame}

    top_row = ttk.Frame(block_frame)
    top_row.pack(fill=X, pady=(0, 10))

    enabled_var = ttk.BooleanVar(value=ioc_config.get('enabled', True))
    enabled_check = ttk.Checkbutton(
        top_row, text="Включено",
        variable=enabled_var, bootstyle="success-round-toggle"
    )
    enabled_check.pack(side=LEFT)
    widgets['enabled_var'] = enabled_var

    priority_frame = ttk.Frame(top_row)
    priority_frame.pack(side=RIGHT)

    up_btn = ttk.Button(
        priority_frame, text="▲",
        command=lambda: tab_obj.move_ioc(index, -1),
        bootstyle=INFO, width=3
    )
    up_btn.pack(side=LEFT, padx=(0, 2))

    down_btn = ttk.Button(
        priority_frame, text="▼",
        command=lambda: tab_obj.move_ioc(index, 1),
        bootstyle=INFO, width=3
    )
    down_btn.pack(side=LEFT)

    reset_btn = ttk.Button(
        priority_frame, text="Сброс",
        command=lambda: tab_obj.reset_single_ioc(index),
        bootstyle="warning-outline", width=6
    )
    reset_btn.pack(side=LEFT, padx=(10, 0))

    fields_frame = ttk.Frame(block_frame)
    fields_frame.pack(fill=X, pady=(0, 10))

    create_text_field(fields_frame, "Тип в отчете:", ioc_config.get('report_type', ''), widgets, 'report_type')
    create_text_field(fields_frame, "Статус NTA:", ioc_config.get('nta_status', ''), widgets, 'nta_status')
    create_text_field(fields_frame, "Статус SIEM (Tools):", ioc_config.get('siem_tools_status', ''), widgets, 'siem_tools_status')
    create_text_field(fields_frame, "Статус SIEM (MP):", ioc_config.get('siem_status', ''), widgets, 'siem_status')

    is_file = ioc_config['name'] == 'File'
    if is_file:
        create_list_editor(block_frame, "Исключения (точное совпадение имени файла):", ioc_config.get('filename_exclusions', []), widgets, 'filename_exclusions_entries')
        create_list_editor(block_frame, "Исключения (слово перед «файлом»):", ioc_config.get('file_blacklist', []), widgets, 'file_blacklist_entries')
    else:
        create_list_editor(block_frame, "Blacklist (точное совпадение IOC — исключить):", ioc_config.get('blacklist', []), widgets, 'blacklist_entries')
        create_list_editor(block_frame, "Exclusions (слово перед IOC — исключить):", ioc_config.get('exclusions', []), widgets, 'exclusions_entries')

    # Шаблоны MP10
    mp10_frame = ttk.LabelFrame(block_frame, text="Шаблоны MP10", padding=5)
    mp10_frame.pack(fill=X, pady=(0, 5))
    mp10_entries = []
    widgets['mp10_template_entries'] = mp10_entries
    mp10_rows_frame = ttk.Frame(mp10_frame)
    mp10_rows_frame.pack(fill=X)

    for tmpl in ioc_config.get('mp10_templates', []):
        add_list_row(mp10_rows_frame, tmpl, mp10_entries)

    ttk.Button(
        mp10_frame, text="+ Добавить шаблон MP10",
        command=lambda rf=mp10_rows_frame, el=mp10_entries: add_list_row(rf, '', el),
        bootstyle=OUTLINE
    ).pack(anchor=W, pady=(5, 0))

    # Шаблоны NAD
    nad_frame = ttk.LabelFrame(block_frame, text="Шаблоны NAD", padding=5)
    nad_frame.pack(fill=X, pady=(0, 5))
    nad_entries = []
    widgets['nad_template_entries'] = nad_entries
    nad_rows_frame = ttk.Frame(nad_frame)
    nad_rows_frame.pack(fill=X)

    for tmpl in ioc_config.get('nad_templates', []):
        add_list_row(nad_rows_frame, tmpl, nad_entries)

    ttk.Button(
        nad_frame, text="+ Добавить шаблон NAD",
        command=lambda rf=nad_rows_frame, el=nad_entries: add_list_row(rf, '', el),
        bootstyle=OUTLINE
    ).pack(anchor=W, pady=(5, 0))

    tab_obj.ioc_widgets.append(widgets)
