"""
Контроллер приложения V2.
Координирует взаимодействие между моделью и представлением.
"""

import os
from typing import List, Optional, Tuple
from ..model.config_manager import ConfigManager
from ..model.ioc_parser_v21_fixed import IOCParser
from ..model.report_generator import ReportGenerator


class AppController:
    """Главный контроллер приложения V2."""
    
    def __init__(self, config_path: str = "config.txt"):
        """Инициализация контроллера."""
        self.config_manager = ConfigManager(config_path)
        self.selected_files: List[str] = []
        self.last_ioc_data = None
        self.last_query_data = None
        self.bulletin = ""  # Новое поле для бюллетеня
    
    def get_config_data(self):
        """Возвращает текущую конфигурацию."""
        return self.config_manager.get_config()
    
    def save_config(self, updated_config):
        """Сохраняет обновленную конфигурацию."""
        self.config_manager.config_data = updated_config
        return self.config_manager.save_config()
    
    def add_files(self, file_paths: List[str]) -> int:
        """Добавляет файлы в список для обработки."""
        added = 0
        for file_path in file_paths:
            if file_path not in self.selected_files:
                if os.path.exists(file_path) and file_path.lower().endswith('.docx'):
                    self.selected_files.append(file_path)
                    added += 1
        return added
    
    def clear_files(self) -> None:
        """Очищает список выбранных файлов."""
        self.selected_files.clear()
    
    def get_selected_files(self) -> List[str]:
        """Возвращает список выбранных файлов."""
        return self.selected_files.copy()
    
    def set_bulletin(self, bulletin: str) -> None:
        """Устанавливает значение бюллетеня."""
        self.bulletin = bulletin
    
    def get_bulletin(self) -> str:
        """Возвращает текущее значение бюллетеня."""
        return self.bulletin
    
    def validate_files(self) -> Tuple[bool, str]:
        """Валидация выбранных файлов."""
        if not self.selected_files:
            return False, "Не выбраны файлы для обработки."
        
        # Проверяем существование файлов
        for file_path in self.selected_files:
            if not os.path.exists(file_path):
                return False, f"Файл не найден: {file_path}"
            if not file_path.lower().endswith('.docx'):
                return False, f"Неверный формат файла: {file_path}"
        
        # Проверяем наличие включенных IOC
        enabled_iocs = self.config_manager.get_enabled_iocs()
        if not enabled_iocs:
            return False, "Нет включенных типов IOC в настройках."
        
        return True, "Валидация успешна."
    
    def process_files(self, log_callback=None) -> Tuple[bool, Optional[dict]]:
        """Обрабатывает выбранные файлы и извлекает IOC."""
        def log(message):
            if log_callback:
                log_callback(message)
        
        try:
            # Валидация
            valid, msg = self.validate_files()
            if not valid:
                log(f"❌ Ошибка валидации: {msg}")
                return False, None
            
            log("🔍 Начало обработки файлов...")
            log(f"📂 Файлов для обработки: {len(self.selected_files)}")
            
            # Создаем парсер с текущей конфигурацией
            enabled_iocs = self.config_manager.get_enabled_iocs()
            log(f"✅ Включенных типов IOC: {len(enabled_iocs)}")
            
            parser = IOCParser(enabled_iocs)
            
            # Извлекаем IOC
            log("\n📖 Чтение документов...")
            ioc_data = parser.parse(self.selected_files)
            
            # Подсчитываем результаты
            total_iocs = sum(len(iocs) for iocs in ioc_data.values())
            
            log(f"\n✨ Извлечение завершено!")
            log(f"📊 Найдено IOC по типам:")
            
            for ioc_type, iocs in ioc_data.items():
                log(f"   • {ioc_type}: {len(iocs)}")
            
            log(f"\n📈 Всего уникальных IOC: {total_iocs}")
            
            # Сохраняем для последующего использования
            self.last_ioc_data = ioc_data
            
            return True, ioc_data
            
        except Exception as e:
            log(f"\n❌ Критическая ошибка: {str(e)}")
            return False, None
    
    def generate_reports(self, ioc_data: dict, output_xlsx_path: str, 
                        log_callback=None) -> Tuple[bool, Optional[str]]:
        """Генерирует оба отчета (.xlsx и _queries.txt)."""
        def log(message):
            if log_callback:
                log_callback(message)
        
        try:
            # Проверяем наличие IOC
            if not ioc_data:
                log("❌ Нет данных IOC для генерации отчетов.")
                return False, None
            
            total_iocs = sum(len(iocs) for iocs in ioc_data.values())
            if total_iocs == 0:
                log("⚠️ Не найдено ни одного IOC для генерации отчетов.")
                return False, None
            
            log("\n📝 Генерация отчетов...")
            
            # Создаем генератор отчетов
            all_iocs = self.config_manager.get_enabled_iocs()
            generator = ReportGenerator(all_iocs)
            
            # Генерируем .xlsx отчет
            log("   • Создание .xlsx отчета (10 столбцов)...")
            xlsx_success = generator.generate_xlsx_report(ioc_data, output_xlsx_path, self.bulletin)
            
            if not xlsx_success:
                log("❌ Ошибка при создании .xlsx отчета.")
                return False, None
            
            log(f"   ✅ .xlsx отчет сохранен: {os.path.basename(output_xlsx_path)}")
            
            # Генерируем .txt файл с запросами
            base_name = os.path.splitext(output_xlsx_path)[0]
            queries_path = f"{base_name}_queries.txt"
            
            log("   • Создание файла запросов (объединенные запросы)...")
            queries_success = generator.generate_queries_report(ioc_data, queries_path)
            
            if not queries_success:
                log("❌ Ошибка при создании файла запросов.")
                return True, None
            
            log(f"   ✅ Файл запросов сохранен: {os.path.basename(queries_path)}")
            
            # Генерируем данные запросов для GUI
            self.last_query_data = generator.generate_query_data(ioc_data)
            
            log("\n🎉 Все отчеты успешно созданы!")
            
            return True, queries_path
            
        except Exception as e:
            log(f"\n❌ Ошибка при генерации отчетов: {str(e)}")
            return False, None
    
    def get_last_query_data(self):
        """Возвращает данные последних сгенерированных запросов."""
        return self.last_query_data
    
    def move_ioc_priority(self, index: int, direction: int) -> bool:
        """Изменяет приоритет IOC."""
        return self.config_manager.move_ioc(index, direction)
