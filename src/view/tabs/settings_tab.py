"""
Вкладка "Настройка IOC" V2 - редактирование шаблонов запросов в GUI.
"""

import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from tkinter import messagebox


class SettingsTab:
    """Вкладка для настройки параметров IOC V2."""

    def __init__(self, parent, controller):
        self.controller = controller
        self.frame = ttk.Frame(parent, padding=10)
        self.ioc_widgets = []

        self._setup_ui()
        self._load_config()

    def _setup_ui(self):
        top_frame = ttk.Frame(self.frame)
        top_frame.pack(fill=X, pady=(0, 10))

        self.save_btn = ttk.Button(
            top_frame,
            text="Сохранить все настройки",
            command=self._save_config,
            bootstyle=SUCCESS
        )
        self.save_btn.pack(side=LEFT, padx=(0, 5))

        self.reset_all_btn = ttk.Button(
            top_frame,
            text="Сбросить все",
            command=self._reset_all,
            bootstyle="danger-outline"
        )
        self.reset_all_btn.pack(side=LEFT, padx=(0, 10))

        state_path = self.controller.get_state_file_path()
        path_label = ttk.Label(
            top_frame,
            text=f"Файл: {state_path}",
            font=("Segoe UI", 8),
            bootstyle=SECONDARY
        )
        path_label.pack(side=LEFT, padx=(5, 0))

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

    def _load_config(self):
        config_data = self.controller.get_config_data()

        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
        self.ioc_widgets.clear()

        for idx, ioc_config in enumerate(config_data):
            self._create_ioc_block(idx, ioc_config)

    def _create_ioc_block(self, index, ioc_config):
        block_frame = ttk.LabelFrame(
            self.scrollable_frame,
            text=f"{ioc_config['name']} - {ioc_config['report_type']}",
            padding=10
        )
        block_frame.pack(fill=X, pady=(0, 5))

        widgets = {'index': index, 'frame': block_frame}

        # Верхняя строка: Чекбокс + Кнопки приоритета
        top_row = ttk.Frame(block_frame)
        top_row.pack(fill=X, pady=(0, 10))

        enabled_var = ttk.BooleanVar(value=ioc_config.get('enabled', True))
        enabled_check = ttk.Checkbutton(
            top_row,
            text="Включено",
            variable=enabled_var,
            bootstyle="success-round-toggle"
        )
        enabled_check.pack(side=LEFT)
        widgets['enabled_var'] = enabled_var

        priority_frame = ttk.Frame(top_row)
        priority_frame.pack(side=RIGHT)

        up_btn = ttk.Button(
            priority_frame, text="▲",
            command=lambda: self._move_ioc(index, -1),
            bootstyle=INFO, width=3
        )
        up_btn.pack(side=LEFT, padx=(0, 2))

        down_btn = ttk.Button(
            priority_frame, text="▼",
            command=lambda: self._move_ioc(index, 1),
            bootstyle=INFO, width=3
        )
        down_btn.pack(side=LEFT)

        reset_btn = ttk.Button(
            priority_frame, text="Сброс",
            command=lambda idx=index: self._reset_single_ioc(idx),
            bootstyle="warning-outline", width=6
        )
        reset_btn.pack(side=LEFT, padx=(10, 0))

        # Основные поля
        fields_frame = ttk.Frame(block_frame)
        fields_frame.pack(fill=X, pady=(0, 10))

        self._create_text_field(fields_frame, "Тип в отчете:", ioc_config.get('report_type', ''), widgets, 'report_type')
        self._create_text_field(fields_frame, "Статус NTA:", ioc_config.get('nta_status', ''), widgets, 'nta_status')
        self._create_text_field(fields_frame, "Статус SIEM (Tools):", ioc_config.get('siem_tools_status', ''), widgets, 'siem_tools_status')
        self._create_text_field(fields_frame, "Статус SIEM (MP):", ioc_config.get('siem_status', ''), widgets, 'siem_status')

        is_file = ioc_config['name'] == 'File'

        # Blacklist / Exclusions
        if is_file:
            # Для File используем исторические поля
            self._create_list_editor(
                block_frame,
                label="Исключения (точное совпадение имени файла):",
                values=ioc_config.get('filename_exclusions', []),
                widgets=widgets,
                key='filename_exclusions_entries'
            )
            self._create_list_editor(
                block_frame,
                label="Исключения (слово перед «файлом»):",
                values=ioc_config.get('file_blacklist', []),
                widgets=widgets,
                key='file_blacklist_entries'
            )
        else:
            self._create_list_editor(
                block_frame,
                label="Blacklist (точное совпадение IOC — исключить):",
                values=ioc_config.get('blacklist', []),
                widgets=widgets,
                key='blacklist_entries'
            )
            self._create_list_editor(
                block_frame,
                label="Exclusions (слово перед IOC — исключить):",
                values=ioc_config.get('exclusions', []),
                widgets=widgets,
                key='exclusions_entries'
            )

        # Шаблоны MP10
        mp10_frame = ttk.LabelFrame(block_frame, text="Шаблоны MP10", padding=5)
        mp10_frame.pack(fill=X, pady=(0, 5))

        mp10_entries = []
        widgets['mp10_template_entries'] = mp10_entries
        mp10_rows_frame = ttk.Frame(mp10_frame)
        mp10_rows_frame.pack(fill=X)

        for tmpl in ioc_config.get('mp10_templates', []):
            self._add_template_row(mp10_rows_frame, tmpl, mp10_entries)

        add_mp10_btn = ttk.Button(
            mp10_frame, text="+ Добавить шаблон MP10",
            command=lambda rf=mp10_rows_frame, el=mp10_entries: self._add_template_row(rf, '', el),
            bootstyle=OUTLINE
        )
        add_mp10_btn.pack(anchor=W, pady=(5, 0))

        # Шаблоны NAD
        nad_frame = ttk.LabelFrame(block_frame, text="Шаблоны NAD", padding=5)
        nad_frame.pack(fill=X, pady=(0, 5))

        nad_entries = []
        widgets['nad_template_entries'] = nad_entries
        nad_rows_frame = ttk.Frame(nad_frame)
        nad_rows_frame.pack(fill=X)

        for tmpl in ioc_config.get('nad_templates', []):
            self._add_template_row(nad_rows_frame, tmpl, nad_entries)

        add_nad_btn = ttk.Button(
            nad_frame, text="+ Добавить шаблон NAD",
            command=lambda rf=nad_rows_frame, el=nad_entries: self._add_template_row(rf, '', el),
            bootstyle=OUTLINE
        )
        add_nad_btn.pack(anchor=W, pady=(5, 0))

        self.ioc_widgets.append(widgets)

    def _create_list_editor(self, parent, label: str, values: list, widgets: dict, key: str):
        """Создаёт редактируемый список строк (blacklist / exclusions)."""
        frame = ttk.LabelFrame(parent, text=label, padding=5)
        frame.pack(fill=X, pady=(0, 5))

        rows_frame = ttk.Frame(frame)
        rows_frame.pack(fill=X)

        entries = []
        widgets[key] = entries

        for v in values:
            self._add_list_row(rows_frame, v, entries)

        add_btn = ttk.Button(
            frame, text="+ Добавить",
            command=lambda rf=rows_frame, el=entries: self._add_list_row(rf, '', el),
            bootstyle="secondary-outline"
        )
        add_btn.pack(anchor=W, pady=(4, 0))

    def _add_list_row(self, container, value: str, entries_list: list):
        row_frame = ttk.Frame(container)
        row_frame.pack(fill=X, pady=1)

        entry = ttk.Entry(row_frame)
        entry.insert(0, value)
        entry.pack(side=LEFT, fill=X, expand=True, padx=(0, 5))

        del_btn = ttk.Button(
            row_frame, text="✕",
            command=lambda rf=row_frame, e=entry, el=entries_list: self._remove_list_row(rf, e, el),
            bootstyle="danger-outline", width=3
        )
        del_btn.pack(side=RIGHT)
        entries_list.append(entry)

    def _remove_list_row(self, row_frame, entry, entries_list):
        if entry in entries_list:
            entries_list.remove(entry)
        row_frame.destroy()

    def _add_template_row(self, container, value, entries_list):
        row_frame = ttk.Frame(container)
        row_frame.pack(fill=X, pady=1)

        entry = ttk.Entry(row_frame)
        entry.insert(0, value)
        entry.pack(side=LEFT, fill=X, expand=True, padx=(0, 5))

        del_btn = ttk.Button(
            row_frame, text="✕",
            command=lambda rf=row_frame, e=entry, el=entries_list: self._remove_template_row(rf, e, el),
            bootstyle="danger-outline", width=3
        )
        del_btn.pack(side=RIGHT)
        entries_list.append(entry)

    def _remove_template_row(self, row_frame, entry, entries_list):
        if entry in entries_list:
            entries_list.remove(entry)
        row_frame.destroy()

    def _create_text_field(self, parent, label, value, widgets_dict, key):
        row_frame = ttk.Frame(parent)
        row_frame.pack(fill=X, pady=2)

        lbl = ttk.Label(row_frame, text=label, width=22, anchor=W)
        lbl.pack(side=LEFT, padx=(0, 10))

        entry = ttk.Entry(row_frame)
        entry.insert(0, value)
        entry.pack(side=LEFT, fill=X, expand=True)

        widgets_dict[key] = entry

    def _read_list_entries(self, widgets, key) -> list:
        """Читает значения из списка Entry-виджетов, пропуская пустые."""
        return [
            e.get().strip()
            for e in widgets.get(key, [])
            if e.winfo_exists() and e.get().strip()
        ]

    def _move_ioc(self, index, direction):
        success = self.controller.move_ioc_priority(index, direction)
        if success:
            self._load_config()
        else:
            msg = "Этот IOC уже в начале списка." if direction == -1 else "Этот IOC уже в конце списка."
            messagebox.showinfo("Информация", msg)

    def _reset_all(self):
        confirmed = messagebox.askyesno(
            "Сброс всех настроек",
            "Вернуть ВСЕ настройки IOC к значениям по умолчанию?\n\nНесохранённые изменения будут потеряны."
        )
        if not confirmed:
            return
        self.controller.reset_all_to_defaults()
        self._load_config()
        messagebox.showinfo("Готово", "Все настройки сброшены к значениям по умолчанию.")

    def _reset_single_ioc(self, index):
        config_data = self.controller.get_config_data()
        if not (0 <= index < len(config_data)):
            return
        ioc_name = config_data[index].get('name', '?')
        confirmed = messagebox.askyesno("Сброс настроек", f"Сбросить настройки «{ioc_name}» к значениям по умолчанию?")
        if not confirmed:
            return
        success = self.controller.reset_ioc_to_default(index)
        if success:
            self._load_config()
            messagebox.showinfo("Готово", f"Настройки «{ioc_name}» сброшены.")
        else:
            messagebox.showerror("Ошибка", f"Не удалось сбросить настройки «{ioc_name}».")

    def _save_config(self):
        try:
            updated_config = []
            current_config = self.controller.get_config_data()

            for widget_set in self.ioc_widgets:
                idx = widget_set['index']
                original = current_config[idx]
                is_file = original['name'] == 'File'

                mp10_templates = [
                    e.get().strip()
                    for e in widget_set['mp10_template_entries']
                    if e.winfo_exists() and e.get().strip()
                ]
                nad_templates = [
                    e.get().strip()
                    for e in widget_set['nad_template_entries']
                    if e.winfo_exists() and e.get().strip()
                ]

                ioc_data = {
                    'enabled': widget_set['enabled_var'].get(),
                    'name': original['name'],
                    'regex': original['regex'],
                    'report_type': widget_set['report_type'].get(),
                    'nta_status': widget_set['nta_status'].get(),
                    'siem_tools_status': widget_set['siem_tools_status'].get(),
                    'siem_status': widget_set['siem_status'].get(),
                    'mp10_templates': mp10_templates,
                    'nad_templates': nad_templates,
                }

                if is_file:
                    ioc_data['filename_exclusions'] = self._read_list_entries(widget_set, 'filename_exclusions_entries')
                    ioc_data['file_blacklist'] = self._read_list_entries(widget_set, 'file_blacklist_entries')
                else:
                    ioc_data['blacklist'] = self._read_list_entries(widget_set, 'blacklist_entries')
                    ioc_data['exclusions'] = self._read_list_entries(widget_set, 'exclusions_entries')

                updated_config.append(ioc_data)

            success = self.controller.save_config(updated_config)

            if success:
                messagebox.showinfo("Успех", "Настройки успешно сохранены!")
            else:
                messagebox.showerror("Ошибка", "Не удалось сохранить настройки.")

        except Exception as e:
            messagebox.showerror("Ошибка", f"Произошла ошибка при сохранении:\n{str(e)}")

    def get_frame(self):
        return self.frame
