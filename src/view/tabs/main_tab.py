"""
Вкладка "Главная" V2 - с полем "Бюллетень".
"""

import ttkbootstrap as ttk
from tkinter import Listbox, Scrollbar
from ttkbootstrap.constants import *
from tkinter import filedialog, messagebox
import os


class MainTab:
    """Вкладка для выбора файлов и запуска обработки V2."""
    
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
        self.clear_files_btn.pack(side=LEFT, padx=(0, 5))
        
        # Поле "Бюллетень" (НОВОЕ)
        bulletin_frame = ttk.LabelFrame(self.frame, text="Параметры отчета", padding=10)
        bulletin_frame.pack(fill=X, pady=(0, 10))
        
        ttk.Label(bulletin_frame, text="Бюллетень:").pack(side=LEFT, padx=(0, 10))
        
        self.bulletin_entry = ttk.Entry(bulletin_frame, width=50)
        self.bulletin_entry.pack(side=LEFT, fill=X, expand=True)
        
        ttk.Label(
            bulletin_frame, 
            text="(оставьте пустым, если не требуется)",
            font=('Segoe UI', 9),
            bootstyle=SECONDARY
        ).pack(side=LEFT, padx=(10, 0))
        
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
        # Проверяем наличие файлов
        if not self.controller.get_selected_files():
            messagebox.showwarning("Предупреждение", "Не выбраны файлы для обработки!")
            return
        
        # Сохраняем значение бюллетеня
        bulletin = self.bulletin_entry.get().strip()
        self.controller.set_bulletin(bulletin)
        
        self.log("\n" + "=" * 80)
        self.log("🚀 ЗАПУСК ОБРАБОТКИ")
        self.log("=" * 80)
        if bulletin:
            self.log(f"📋 Бюллетень: {bulletin}")
        
        # Обрабатываем файлы
        success, ioc_data = self.controller.process_files(log_callback=self.log)
        
        if not success or not ioc_data:
            self.log("\n❌ Обработка завершилась с ошибкой.")
            messagebox.showerror("Ошибка", "Не удалось извлечь IOC из файлов.")
            return
        
        # Проверяем наличие IOC
        total_iocs = sum(len(iocs) for iocs in ioc_data.values())
        if total_iocs == 0:
            self.log("\n⚠️ В документах не найдено ни одного IOC.")
            messagebox.showinfo("Информация", "В выбранных документах не найдено ни одного IOC.")
            return
        
        # Автоматическая генерация имени файла
        selected_files = self.controller.get_selected_files()
        if len(selected_files) == 1:
            input_filename = os.path.splitext(os.path.basename(selected_files[0]))[0]
        else:
            input_filename = "multiple_files"

        from datetime import datetime
        current_time = datetime.now().strftime('%d-%m-%y-%H-%M')
        default_filename = f"ioc_report_{input_filename}_{current_time}.xlsx"

        # Диалог сохранения с предложенным именем
        output_path = filedialog.asksaveasfilename(
            title="Сохранить отчет как...",
            defaultextension=".xlsx",
            filetypes=[("Excel Files", "*.xlsx"), ("All Files", "*.*")],
            initialfile=default_filename
        )

        if not output_path:
            self.log("\n⚠️ Сохранение отменено пользователем.")
            return
        
        # Генерируем отчеты
        success, queries_path = self.controller.generate_reports(
            ioc_data,
            output_path,
            log_callback=self.log
        )
        
        if success:
            self.log("\n" + "=" * 80)
            self.log("✅ ОБРАБОТКА ЗАВЕРШЕНА УСПЕШНО")
            self.log("=" * 80 + "\n")
            
            # Предлагаем открыть файл
            result = messagebox.askyesno(
                "Успех",
                f"Отчеты успешно созданы!\n\n"
                f"📊 {os.path.basename(output_path)}\n"
                f"📝 {os.path.basename(queries_path) if queries_path else 'N/A'}\n\n"
                "Открыть .xlsx отчет?"
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
    
    def get_frame(self):
        """Возвращает фрейм вкладки."""
        return self.frame
