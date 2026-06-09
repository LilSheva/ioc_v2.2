"""
Вкладка "Настройка IOC" — редактирование шаблонов запросов в GUI.
"""

import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from tkinter import messagebox
from ioc_analyzer.adapters.gui.tabs.settings_widgets import create_ioc_block


class SettingsTab:
    """Вкладка для настройки параметров IOC."""

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
            top_frame, text="Сохранить все настройки",
            command=self._save_config, bootstyle=SUCCESS
        )
        self.save_btn.pack(side=LEFT, padx=(0, 5))

        self.reset_all_btn = ttk.Button(
            top_frame, text="Сбросить все",
            command=self._reset_all, bootstyle="danger-outline"
        )
        self.reset_all_btn.pack(side=LEFT, padx=(0, 10))

        state_path = self.controller.get_state_file_path()
        ttk.Label(
            top_frame, text=f"Файл: {state_path}",
            font=("Segoe UI", 8), bootstyle=SECONDARY
        ).pack(side=LEFT, padx=(5, 0))

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
            create_ioc_block(self, self.scrollable_frame, idx, ioc_config)

    def _read_list_entries(self, widgets, key) -> list:
        """Читает значения из списка Entry-виджетов, пропуская пустые."""
        return [
            e.get().strip()
            for e in widgets.get(key, [])
            if e.winfo_exists() and e.get().strip()
        ]

    def move_ioc(self, index, direction):
        success = self.controller.move_ioc_priority(index, direction)
        if success:
            self._load_config()
        else:
            msg = "Этот IOC уже в начале списка." if direction == -1 else "Этот IOC уже в конце списка."
            messagebox.showinfo("Информация", msg)

    def reset_single_ioc(self, index):
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

    def _save_config(self):
        try:
            updated_config = []
            current_config = self.controller.get_config_data()

            for widget_set in self.ioc_widgets:
                idx = widget_set['index']
                original = current_config[idx]
                is_file = original['name'] == 'File'

                mp10_templates = self._read_list_entries(widget_set, 'mp10_template_entries')
                nad_templates = self._read_list_entries(widget_set, 'nad_template_entries')

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
