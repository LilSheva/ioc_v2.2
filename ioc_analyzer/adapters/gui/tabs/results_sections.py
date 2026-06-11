"""
Строки и секции для вкладки "Результаты запросов".
"""

import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from tkinter import messagebox


def create_query_row(tab_obj, parent, query_data) -> None:
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
    sys_style = 'warning' if system == 'MP10' else ('info' if system == 'NAD' else 'secondary')
    ttk.Label(
        row_frame, text=system, anchor=W,
        bootstyle=sys_style, font=("TkDefaultFont", 9, "bold")
    ).grid(row=0, column=1, sticky=EW, padx=5)

    # ... Часть ...
    ttk.Label(row_frame, text=query_data.get('chunk_label', ''), anchor=W).grid(
        row=0, column=2, sticky=EW, padx=5
    )

    # Entry
    query_entry = ttk.Entry(row_frame)
    query_entry.insert(0, query_data['query'])
    query_entry.config(state='readonly')
    query_entry.grid(row=0, column=3, sticky=EW, padx=5)
    widgets['query_entry'] = query_entry

    # Кнопка копирования
    copy_btn = ttk.Button(
        row_frame,
        text="Копировать",
        command=lambda w=widgets: copy_query(tab_obj, w),
        bootstyle=INFO,
        width=12
    )
    copy_btn.grid(row=0, column=4, padx=5)

    completed_var = ttk.BooleanVar(value=False)
    completed_check = ttk.Checkbutton(
        row_frame,
        text="Выполнено",
        variable=completed_var,
        bootstyle="success-round-toggle"
    )
    completed_check.grid(row=0, column=5, padx=5)
    widgets['completed_var'] = completed_var

    tab_obj.query_widgets.append(widgets)


def copy_query(tab_obj, widgets) -> None:
    """Копирует запрос в буфер обмена."""
    try:
        query_text = widgets['query']
        tab_obj.frame.clipboard_clear()
        tab_obj.frame.clipboard_append(query_text)
        tab_obj.frame.update()
        widgets['completed_var'].set(False)
    except Exception as e:
        messagebox.showerror("Ошибка", f"Не удалось скопировать запрос:\n{str(e)}")


def rebuild_group_queries(tab_obj, group_idx) -> None:
    """Пересобирает строки запросов для группы с учётом chunk_size."""
    rows_frame = tab_obj.group_frames.get(group_idx)
    group_data = tab_obj.group_data_cache.get(group_idx)
    if not rows_frame or not group_data:
        return

    # Очищаем строки
    for w in rows_frame.winfo_children():
        w.destroy()

    # Удаляем старые виджеты этой группы
    tab_obj.query_widgets = [
        qw for qw in tab_obj.query_widgets if qw.get('_group_idx') != group_idx
    ]

    cleaned_iocs = group_data.get('cleaned_iocs', [])
    ioc_count = len(cleaned_iocs)
    chunk_var = tab_obj.chunk_size_vars.get(group_idx)

    chunk_size = ioc_count
    if chunk_var:
        try:
            val = chunk_var.get()
            if 1 <= val <= ioc_count:
                chunk_size = val
        except Exception as e:
            import logging
            logging.getLogger("ioc_analyzer.gui.results_sections").debug(
                "Не удалось прочитать размер чанка, используется размер по умолчанию: %s", e
            )

    # Разделение по чанкам
    if chunk_size >= ioc_count:
        chunks = [cleaned_iocs]
    else:
        chunks = [cleaned_iocs[i:i + chunk_size] for i in range(0, ioc_count, chunk_size)]
    total_chunks = len(chunks)

    # Строим по чанкам
    for query_info in group_data.get('queries', []):
        template = query_info.get('template', '')
        join_op = query_info.get('join_op', ' OR ')
        ioc_name = query_info['ioc_name']
        system = query_info['system']

        for chunk_idx, chunk in enumerate(chunks):
            chunk_label = f"{chunk_idx + 1}/{total_chunks}" if total_chunks > 1 else ""
            query_text = tab_obj.controller.build_query(template, chunk, join_op)

            row_data = {
                '_group_idx': group_idx,
                'ioc_name': ioc_name,
                'system': system,
                'chunk_label': chunk_label,
                'query': query_text,
                'completed': False
            }
            create_query_row(tab_obj, rows_frame, row_data)
