"""
Вкладка "Настройка IOC" V2 - упрощенная версия.
"""

import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from tkinter import messagebox


class SettingsTab:
    """Вкладка для настройки параметров IOC V2."""
    
    def __init__(self, parent, controller):
        """Инициализация вкладки."""
        self.controller = controller
        self.frame = ttk.Frame(parent, padding=10)
        self.ioc_widgets = []
        
        self._setup_ui()
        self._load_config()
    
    def _setup_ui(self):
        """Создание элементов интерфейса."""
        # Верхняя панель с кнопками
        top_frame = ttk.Frame(self.frame)
        top_frame.pack(fill=X, pady=(0, 10))
        
        self.save_btn = ttk.Button(
            top_frame,
            text="💾 Сохранить все настройки",
            command=self._save_config,
            bootstyle=SUCCESS
        )
        self.save_btn.pack(side=LEFT, padx=(0, 5))
        
        # Информация
        info_label = ttk.Label(
            top_frame,
            text="ℹ️ Редактирование множественных шаблонов доступно через config.txt",
            font=('Segoe UI', 9),
            bootstyle=INFO
        )
        info_label.pack(side=LEFT, padx=10)
        
        # Скроллируемая область для блоков IOC
        canvas_frame = ttk.Frame(self.frame)
        canvas_frame.pack(fill=BOTH, expand=True)
        
        self.canvas = ttk.Canvas(canvas_frame)
        scrollbar = ttk.Scrollbar(canvas_frame, orient=VERTICAL, command=self.canvas.yview)
        
        self.scrollable_frame = ttk.Frame(self.canvas)
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )
        
        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor=NW)
        self.canvas.configure(yscrollcommand=scrollbar.set)
        
        self.canvas.pack(side=LEFT, fill=BOTH, expand=True)
        scrollbar.pack(side=RIGHT, fill=Y)
        
        # Биндинг для прокрутки колесом мыши
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)
    
    def _on_mousewheel(self, event):
        """Обработчик прокрутки колесом мыши."""
        self.canvas.yview_scroll(int(-1*(event.delta/120)), "units")
    
    def _load_config(self):
        """Загружает конфигурацию и создает блоки настроек."""
        config_data = self.controller.get_config_data()
        
        # Очищаем предыдущие виджеты
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
        self.ioc_widgets.clear()
        
        # Создаем блоки для каждого IOC
        for idx, ioc_config in enumerate(config_data):
            self._create_ioc_block(idx, ioc_config)
    
    def _create_ioc_block(self, index, ioc_config):
        """Создает упрощенный блок настроек для одного IOC."""
        # Основной фрейм блока
        block_frame = ttk.LabelFrame(
            self.scrollable_frame,
            text=f"{ioc_config['name']} - {ioc_config['report_type']}",
            padding=10
        )
        block_frame.pack(fill=X, pady=(0, 5))
        
        # Словарь для хранения виджетов этого блока
        widgets = {'index': index, 'frame': block_frame}
        
        # Верхняя строка: Чекбокс + Кнопки приоритета
        top_row = ttk.Frame(block_frame)
        top_row.pack(fill=X, pady=(0, 10))
        
        # Чекбокс "Включено"
        enabled_var = ttk.BooleanVar(value=ioc_config.get('enabled', True))
        enabled_check = ttk.Checkbutton(
            top_row,
            text="✓ Включено",
            variable=enabled_var,
            bootstyle="success-round-toggle"
        )
        enabled_check.pack(side=LEFT)
        widgets['enabled_var'] = enabled_var
        
        # Кнопки приоритета
        priority_frame = ttk.Frame(top_row)
        priority_frame.pack(side=RIGHT)
        
        up_btn = ttk.Button(
            priority_frame,
            text="▲",
            command=lambda: self._move_ioc(index, -1),
            bootstyle=INFO,
            width=3
        )
        up_btn.pack(side=LEFT, padx=(0, 2))
        
        down_btn = ttk.Button(
            priority_frame,
            text="▼",
            command=lambda: self._move_ioc(index, 1),
            bootstyle=INFO,
            width=3
        )
        down_btn.pack(side=LEFT)
        
        # Основные поля настроек
        fields_frame = ttk.Frame(block_frame)
        fields_frame.pack(fill=X, pady=(0, 10))

        # Тип в отчете
        self._create_text_field(
            fields_frame, "Тип в отчете:",
            ioc_config.get('report_type', ''), widgets, 'report_type'
        )
        
        # Статусы
        self._create_text_field(
            fields_frame, "Статус NTA:", 
            ioc_config.get('nta_status', ''), widgets, 'nta_status'
        )
        
        self._create_text_field(
            fields_frame, "Статус SIEM (Tools):", 
            ioc_config.get('siem_tools_status', ''), widgets, 'siem_tools_status'
        )
        
        self._create_text_field(
            fields_frame, "Статус SIEM (MP):", 
            ioc_config.get('siem_status', ''), widgets, 'siem_status'
        )
        
        # Информация о шаблонах
        info_frame = ttk.LabelFrame(block_frame, text="Шаблоны запросов", padding=10)
        info_frame.pack(fill=X)
        
        mp10_count = len(ioc_config.get('mp10_templates', []))
        nad_count = len(ioc_config.get('nad_templates', []))
        
        ttk.Label(
            info_frame,
            text=f"MP10 шаблонов: {mp10_count} | NAD шаблонов: {nad_count}",
            font=('Segoe UI', 10)
        ).pack()
        
        ttk.Label(
            info_frame,
            text="Для редактирования шаблонов используйте config.txt",
            font=('Segoe UI', 9),
            bootstyle=SECONDARY
        ).pack()
        
        # Сохраняем виджеты
        self.ioc_widgets.append(widgets)
    
    def _create_text_field(self, parent, label, value, widgets_dict, key):
        """Создает однострочное текстовое поле с меткой."""
        row_frame = ttk.Frame(parent)
        row_frame.pack(fill=X, pady=2)
        
        lbl = ttk.Label(row_frame, text=label, width=22, anchor=W)
        lbl.pack(side=LEFT, padx=(0, 10))
        
        entry = ttk.Entry(row_frame)
        entry.insert(0, value)
        entry.pack(side=LEFT, fill=X, expand=True)
        
        widgets_dict[key] = entry
    
    def _move_ioc(self, index, direction):
        """Перемещает IOC вверх или вниз."""
        success = self.controller.move_ioc_priority(index, direction)
        if success:
            self._load_config()
        else:
            if direction == -1:
                messagebox.showinfo("Информация", "Этот IOC уже в начале списка.")
            else:
                messagebox.showinfo("Информация", "Этот IOC уже в конце списка.")
    
    def _save_config(self):
        """Сохраняет все настройки IOC."""
        try:
            # Собираем данные из виджетов
            updated_config = []
            current_config = self.controller.get_config_data()
            
            for widget_set in self.ioc_widgets:
                idx = widget_set['index']
                original = current_config[idx]
                
                ioc_data = {
                    'enabled': widget_set['enabled_var'].get(),
                    'name': original['name'],
                    'regex': original['regex'],
                    'report_type': widget_set['report_type'].get(),
                    'nta_status': widget_set['nta_status'].get(),
                    'siem_tools_status': widget_set['siem_tools_status'].get(),
                    'siem_status': widget_set['siem_status'].get(),
                    'mp10_templates': original['mp10_templates'],
                    'nad_templates': original['nad_templates']
                }
                
                updated_config.append(ioc_data)
            
            # Сохраняем
            success = self.controller.save_config(updated_config)
            
            if success:
                messagebox.showinfo("Успех", "Настройки успешно сохранены!")
            else:
                messagebox.showerror("Ошибка", "Не удалось сохранить настройки.")
        
        except Exception as e:
            messagebox.showerror("Ошибка", f"Произошла ошибка при сохранении:\n{str(e)}")
    
    def get_frame(self):
        """Возвращает фрейм вкладки."""
        return self.frame
