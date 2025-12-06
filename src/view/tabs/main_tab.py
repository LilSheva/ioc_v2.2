"""Вкладка "Главная" с полями управления и логированием."""

import ttkbootstrap as ttk
from tkinter import Listbox, Scrollbar, END
from ttkbootstrap.constants import *
from tkinter import filedialog, messagebox
import os


class MainTab:
    """Вкладка для выбора файлов и запуска обработки."""

    def __init__(self, parent, controller):
        """Инициализация вкладки."""
        self.controller = controller
        self.frame = ttk.Frame(parent, padding=10)
        
        self._setup_ui()
    
    def _setup_ui(self):
        """Создание элементов интерфейса."""
        # Верхняя секция - работа с файлами
        file_frame = ttk.LabelFrame(self.frame, text="Выбор файлов", padding=10)
        file_frame.pack(fill=BOTH, expand=False, pady=(0, 10))
        
        # Listbox для отображения файлов
        list_frame = ttk.Frame(file_frame)
        list_frame.pack(fill=BOTH, expand=True, pady=(0, 10))
        
        scrollbar = Scrollbar(list_frame)
        scrollbar.pack(side=RIGHT, fill=Y)
        
        self.file_listbox = Listbox(
            list_frame,
            height=6,
            bg='#2b3e50',
            fg='white',
            selectbackground='#4e73df',
            selectforeground='white',
            yscrollcommand=scrollbar.set,
            borderwidth=0,
            highlightthickness=1,
            highlightbackground='#374850',
            highlightcolor='#4e73df',
            font=('Segoe UI', 10)
        )
        self.file_listbox.pack(side=LEFT, fill=BOTH, expand=True)
        scrollbar.config(command=self.file_listbox.yview)
        
        # Кнопки управления файлами
        btn_frame = ttk.Frame(file_frame)
        btn_frame.pack(fill=X)
        
        self.add_files_btn = ttk.Button(
            btn_frame,
            text="📁 Добавить файлы...",
            command=self._add_files,
            bootstyle=PRIMARY
        )
        self.add_files_btn.pack(side=LEFT, padx=(0, 5))
        
        self.clear_files_btn = ttk.Button(
            btn_frame,
            text="🗑️ Очистить список",
            command=self._clear_files,
            bootstyle=SECONDARY
        )
        self.clear_files_btn.pack(side=LEFT, padx=(0, 10))

        # Статус фильтров (в той же строке)
        self.filters_status_label = ttk.Label(
            btn_frame,
            text="",
            font=('Segoe UI', 8),
            foreground='white',
            wraplength=250
        )
        self.filters_status_label.pack(side=LEFT, padx=(0, 5))

        # Кнопка выбора файла-референса (в той же строке)
        self.filters_btn = ttk.Button(
            btn_frame,
            text="🔄 Указать файл-референс",
            command=self._select_filters_template,
            bootstyle=DANGER
        )
        self.filters_btn.pack(side=LEFT)

        # Секция "Параметры отчета"
        bulletin_frame = ttk.LabelFrame(self.frame, text="Параметры отчета", padding=10)
        bulletin_frame.pack(fill=X, pady=(0, 10))

        # Строка 1: Режим работы
        mode_row = ttk.Frame(bulletin_frame)
        mode_row.pack(fill=X, pady=(0, 10))

        ttk.Label(mode_row, text="Режим работы:", width=15).pack(side=LEFT, padx=(0, 10))

        self.mode_var = ttk.StringVar(value="fstek")

        mode_radio_frame = ttk.Frame(mode_row)
        mode_radio_frame.pack(side=LEFT)

        ttk.Radiobutton(
            mode_radio_frame,
            text="ФСТЕК",
            variable=self.mode_var,
            value="fstek",
            command=self._on_mode_changed,
            bootstyle="primary"
        ).pack(side=LEFT, padx=(0, 15))

        ttk.Radiobutton(
            mode_radio_frame,
            text="ГосСОПКА",
            variable=self.mode_var,
            value="gossopka",
            command=self._on_mode_changed,
            bootstyle="primary"
        ).pack(side=LEFT)

        # Строка 2: Режим очистки URI
        uri_mode_row = ttk.Frame(bulletin_frame)
        uri_mode_row.pack(fill=X, pady=(0, 10))

        ttk.Label(uri_mode_row, text="Очистка URI:", width=15).pack(side=LEFT, padx=(0, 10))

        self.uri_clean_var = ttk.StringVar(value="domain")

        uri_radio_frame = ttk.Frame(uri_mode_row)
        uri_radio_frame.pack(side=LEFT)

        ttk.Radiobutton(
            uri_radio_frame,
            text="До уникального префикса",
            variable=self.uri_clean_var,
            value="unique",
            command=self._on_uri_mode_changed,
            bootstyle="info"
        ).pack(side=LEFT, padx=(0, 15))

        ttk.Radiobutton(
            uri_radio_frame,
            text="Только домен",
            variable=self.uri_clean_var,
            value="domain",
            command=self._on_uri_mode_changed,
            bootstyle="info"
        ).pack(side=LEFT)

        # Строка 3: Бюллетень (для режима ФСТЕК)
        bulletin_row = ttk.Frame(bulletin_frame)
        bulletin_row.pack(fill=X)

        self.bulletin_label = ttk.Label(bulletin_row, text="Бюллетень:", width=15)
        self.bulletin_label.pack(side=LEFT, padx=(0, 10))

        self.bulletin_entry = ttk.Entry(bulletin_row, width=50)
        self.bulletin_entry.pack(side=LEFT, fill=X, expand=True)

        self.bulletin_hint = ttk.Label(
            bulletin_row,
            text="(для режима ФСТЕК)",
            font=('Segoe UI', 9),
            bootstyle=SECONDARY
        )
        self.bulletin_hint.pack(side=LEFT, padx=(10, 0))
        
        # Кнопка генерации
        generate_frame = ttk.Frame(self.frame)
        generate_frame.pack(fill=X, pady=(0, 10))
        
        self.generate_btn = ttk.Button(
            generate_frame,
            text="⚡ Сформировать отчеты",
            command=self._generate_reports,
            bootstyle=SUCCESS,
            width=30
        )
        self.generate_btn.pack(side=RIGHT)
        
        # Нижняя секция - логи
        log_frame = ttk.LabelFrame(self.frame, text="Журнал работы", padding=10)
        log_frame.pack(fill=BOTH, expand=True)
        
        # Текстовое поле для логов
        log_text_frame = ttk.Frame(log_frame)
        log_text_frame.pack(fill=BOTH, expand=True, pady=(0, 10))
        
        log_scrollbar = ttk.Scrollbar(log_text_frame)
        log_scrollbar.pack(side=RIGHT, fill=Y)
        
        self.log_text = ttk.Text(
            log_text_frame,
            height=12,
            yscrollcommand=log_scrollbar.set,
            wrap=WORD,
            state=DISABLED
        )
        self.log_text.pack(side=LEFT, fill=BOTH, expand=True)
        log_scrollbar.config(command=self.log_text.yview)
        
        # Кнопка очистки логов
        self.clear_log_btn = ttk.Button(
            log_frame,
            text="🧹 Очистить лог",
            command=self._clear_log,
            bootstyle=SECONDARY
        )
        self.clear_log_btn.pack()

        # Обновляем статус фильтров при инициализации
        self._update_filters_status()
    
    def _add_files(self):
        """Обработчик добавления файлов."""
        file_paths = filedialog.askopenfilenames(
            title="Выберите .docx файлы",
            filetypes=[("Word Documents", "*.docx"), ("All Files", "*.*")]
        )

        if file_paths:
            added = self.controller.add_files(list(file_paths))
            self._update_file_list()
            self.log(f"✅ Добавлено файлов: {added}")

            if self.mode_var.get() == "fstek":
                auto_bulletin = self.controller.auto_fill_bulletin()
                if auto_bulletin:
                    self.bulletin_entry.delete(0, END)
                    self.bulletin_entry.insert(0, auto_bulletin)
                    self.log(f"📋 Бюллетень определен автоматически: {auto_bulletin}")
    
    def _clear_files(self):
        """Обработчик очистки списка файлов."""
        if self.file_listbox.size() > 0:
            confirm = messagebox.askyesno(
                "Подтверждение",
                "Очистить список выбранных файлов?"
            )
            if confirm:
                self.controller.clear_files()
                self._update_file_list()

                if self.mode_var.get() == "fstek":
                    self.bulletin_entry.delete(0, END)

                self.log("🗑️ Список файлов очищен.")
    
    def _update_file_list(self):
        """Обновляет отображение списка файлов."""
        self.file_listbox.delete(0, END)
        files = self.controller.get_selected_files()
        
        for file_path in files:
            display_name = os.path.basename(file_path)
            self.file_listbox.insert(END, display_name)
    
    def _generate_reports(self):
        """Обработчик генерации отчетов."""
        if not self.controller.get_selected_files():
            messagebox.showwarning("Предупреждение", "Не выбраны файлы для обработки!")
            return

        bulletin = self.bulletin_entry.get().strip()
        self.controller.set_bulletin(bulletin)

        mode = self.mode_var.get()
        self.controller.set_mode(mode)

        uri_clean_mode = self.uri_clean_var.get()
        self.controller.set_uri_clean_mode(uri_clean_mode)

        self.log("\n" + "=" * 80)
        self.log("🚀 ЗАПУСК ОБРАБОТКИ")
        self.log("=" * 80)
        self.log(f"⚙️ Режим работы: {mode.upper()}")
        self.log(f"🔗 Очистка URI: {'До уникального префикса' if uri_clean_mode == 'unique' else 'Только домен'}")
        if mode == "fstek" and bulletin:
            self.log(f"📋 Бюллетень: {bulletin}")

        success, ioc_data = self.controller.process_files(log_callback=self.log)

        if not success or not ioc_data:
            self.log("\n❌ Обработка завершилась с ошибкой.")
            messagebox.showerror("Ошибка", "Не удалось извлечь IOC из файлов.")
            return

        total_iocs = sum(len(iocs) for iocs in ioc_data.values())
        if total_iocs == 0:
            self.log("\n⚠️ В документах не найдено ни одного IOC.")
            messagebox.showinfo("Информация", "В выбранных документах не найдено ни одного IOC.")
            return

        selected_files = self.controller.get_selected_files()
        if len(selected_files) == 1:
            input_filename = os.path.splitext(os.path.basename(selected_files[0]))[0]
        else:
            input_filename = "multiple_files"

        from datetime import datetime
        current_time = datetime.now().strftime('%d-%m-%y-%H-%M')
        default_filename = f"ioc_report_{input_filename}_{current_time}.xlsx"

        output_path = filedialog.asksaveasfilename(
            title="Сохранить отчет как...",
            defaultextension=".xlsx",
            filetypes=[("Excel Files", "*.xlsx"), ("All Files", "*.*")],
            initialfile=default_filename
        )

        if not output_path:
            self.log("\n⚠️ Сохранение отменено пользователем.")
            return

        success, queries_path = self.controller.generate_reports(
            ioc_data,
            output_path,
            log_callback=self.log
        )

        filters_path = None
        # Используем путь к референсу из контроллера
        if self.controller.has_filters_template():
            template_path = self.controller.get_filters_template_path()
            filter_filename = self.controller.generate_filters_filename()
            filters_path = os.path.join(os.path.dirname(output_path), filter_filename)

            self.controller.generate_filters_file(
                ioc_data,
                template_path,
                filters_path,
                log_callback=self.log
            )

        if success:
            self.log("\n" + "=" * 80)
            self.log("✅ ОБРАБОТКА ЗАВЕРШЕНА УСПЕШНО")
            self.log("=" * 80 + "\n")

            message_parts = [
                "Отчеты успешно созданы!",
                "",
                f"📊 {os.path.basename(output_path)}",
                f"📝 {os.path.basename(queries_path) if queries_path else 'N/A'}"
            ]
            if filters_path and os.path.exists(filters_path):
                message_parts.append(f"🔍 {os.path.basename(filters_path)}")
            message_parts.append("")
            message_parts.append("Открыть .xlsx отчет?")

            result = messagebox.askyesno(
                "Успех",
                "\n".join(message_parts)
            )
            
            if result:
                try:
                    os.startfile(output_path)
                except:
                    import subprocess
                    try:
                        subprocess.run(['xdg-open', output_path])
                    except:
                        self.log("⚠️ Не удалось автоматически открыть файл.")
        else:
            messagebox.showerror("Ошибка", "Произошла ошибка при генерации отчетов.")
    
    def _clear_log(self):
        """Очищает текстовое поле логов."""
        self.log_text.config(state=NORMAL)
        self.log_text.delete(1.0, END)
        self.log_text.config(state=DISABLED)
    
    def log(self, message):
        """Добавляет сообщение в лог."""
        self.log_text.config(state=NORMAL)
        self.log_text.insert(END, message + "\n")
        self.log_text.see(END)
        self.log_text.config(state=DISABLED)
        self.log_text.update_idletasks()

    def _on_mode_changed(self):
        """Обработчик изменения режима работы."""
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
        """Обработчик изменения режима очистки URI."""
        pass

    def _update_filters_status(self):
        """Обновляет статус отображения файла-референса для фильтров."""
        has_template = self.controller.has_filters_template()

        if has_template:
            template_path = self.controller.get_filters_template_path()
            filename = os.path.basename(template_path) if template_path else "файл"
            self.filters_status_label.config(
                text=f"✅ Фильтры найдены:\n{filename}"
            )
            self.filters_btn.config(
                text="🔄 Поменять файл-референс",
                bootstyle=SUCCESS
            )
        else:
            self.filters_status_label.config(
                text="❌ Фильтры не найдены.\nМожете указать где они"
            )
            self.filters_btn.config(
                text="🔄 Указать файл-референс",
                bootstyle=DANGER
            )

    def _select_filters_template(self):
        """Обработчик выбора файла-референса для фильтров."""
        file_path = filedialog.askopenfilename(
            title="Выберите файл-шаблон фильтров",
            filetypes=[("Excel Files", "*.xlsx"), ("All Files", "*.*")],
            initialfile="Фильтры (Переделанные).xlsx"
        )

        if file_path:
            self.controller.set_filters_template_path(file_path)
            self._update_filters_status()

            if self.controller.has_filters_template():
                self.log(f"Файл-референс для фильтров установлен: {os.path.basename(file_path)}")
            else:
                self.log("Ошибка: выбранный файл не существует.")
                messagebox.showerror("Ошибка", "Выбранный файл не существует.")

    def get_frame(self):
        """Возвращает фрейм вкладки."""
        return self.frame
