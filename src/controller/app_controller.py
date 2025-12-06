"""Контроллер приложения для координации между моделью и представлением."""

import os
from typing import List, Optional, Tuple
from ..model.config_manager import ConfigManager
from ..model.ioc_parser_v21_fixed import IOCParser
from ..model.report_generator import ReportGenerator
from ..utils import get_default_filters_template_path


class AppController:
    """Главный контроллер приложения."""

    def __init__(self, config_path: str = "config.txt"):
        """Инициализация контроллера."""
        self.config_manager = ConfigManager(config_path)
        self.selected_files: List[str] = []
        self.last_ioc_data = None
        self.last_query_data = None
        self.bulletin = ""
        self.mode = "fstek"
        self.uri_clean_mode = "domain"
        self.event_type = "Фишинговая рассылка электронной почты. Вредоносные вложения"

        # Путь к файлу-референсу для фильтров
        # По умолчанию пытаемся найти в tst/
        default_template = get_default_filters_template_path()
        self.filters_template_path = default_template if os.path.exists(default_template) else None
    
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

    def set_mode(self, mode: str) -> None:
        """Устанавливает режим работы (fstek/gossopka)."""
        self.mode = mode

    def get_mode(self) -> str:
        """Возвращает текущий режим работы."""
        return self.mode

    def set_uri_clean_mode(self, mode: str) -> None:
        """Устанавливает режим очистки URI (unique/domain)."""
        self.uri_clean_mode = mode

    def get_uri_clean_mode(self) -> str:
        """Возвращает текущий режим очистки URI."""
        return self.uri_clean_mode

    def set_event_type(self, event_type: str) -> None:
        """Устанавливает тип события."""
        self.event_type = event_type

    def get_event_type(self) -> str:
        """Возвращает текущий тип события."""
        return self.event_type

    def set_filters_template_path(self, path: Optional[str]) -> None:
        """
        Устанавливает путь к файлу-референсу для фильтров.

        Args:
            path: Путь к .xlsx файлу-шаблону или None
        """
        if path and os.path.exists(path):
            self.filters_template_path = path
        else:
            self.filters_template_path = None

    def get_filters_template_path(self) -> Optional[str]:
        """
        Возвращает путь к файлу-референсу для фильтров.

        Returns:
            Путь к файлу или None если не установлен
        """
        return self.filters_template_path

    def has_filters_template(self) -> bool:
        """
        Проверяет наличие файла-референса для фильтров.

        Returns:
            True если файл установлен и существует
        """
        return self.filters_template_path is not None and os.path.exists(self.filters_template_path)

    def extract_bulletin_from_filename(self, filename: str) -> Optional[str]:
        """Извлекает номер бюллетеня из имени файла (формат: XXX XX XXXX)."""
        import re
        pattern = r'\b(\d+)\s+(\d+)\s+(\d+)\b'
        match = re.search(pattern, filename)

        if match:
            return f"{match.group(1)}/{match.group(2)}/{match.group(3)}"

        return None

    def auto_fill_bulletin(self) -> Optional[str]:
        """Автоматически определяет номер бюллетеня из имен файлов."""
        if not self.selected_files:
            return None

        bulletin_numbers = set()

        for file_path in self.selected_files:
            filename = os.path.basename(file_path)
            bulletin_num = self.extract_bulletin_from_filename(filename)

            if bulletin_num:
                bulletin_numbers.add(bulletin_num)

        if len(bulletin_numbers) == 1:
            return f"FSTEC {bulletin_numbers.pop()}"

        return None

    def extract_gossopka_info_from_filename(self, filename: str) -> Optional[dict]:
        """Извлекает информацию из имени файла ГосСОПКА (дата, номер, организация)."""
        import re
        pattern = r'Бюллетень\s+от\s+(\d{2}\.\d{2}\.\d{4})_(\d+)\s+(.+?)\.docx'
        match = re.search(pattern, filename, re.IGNORECASE)

        if match:
            return {
                "date": match.group(1),
                "number": match.group(2),
                "org": match.group(3).strip()
            }

        return None

    def generate_filters_filename(self) -> str:
        """Генерирует имя файла фильтров в зависимости от режима."""
        from datetime import datetime
        current_time = datetime.now().strftime('%d.%m.%Y %H-%M')

        if self.mode == "fstek":
            bulletin = self.bulletin or self.auto_fill_bulletin() or "Без бюллетеня"
            bulletin = bulletin.replace('/', '-')
            return f"Фильтры ({bulletin}) {current_time}.xlsx"

        else:
            info_list = []
            for file_path in self.selected_files:
                filename = os.path.basename(file_path)
                info = self.extract_gossopka_info_from_filename(filename)
                if info:
                    info_list.append(info)

            if not info_list:
                return f"Фильтры (ГосСОПКА) {current_time}.xlsx"

            groups = {}
            for info in info_list:
                key = (info["org"], info["date"])
                if key not in groups:
                    groups[key] = []
                groups[key].append(info["number"])

            if groups:
                (org, date), numbers = list(groups.items())[0]
                numbers_str = ",".join(sorted(numbers))
                return f"Фильтры ({org} от {date} ({numbers_str})) {current_time}.xlsx"

            return f"Фильтры (ГосСОПКА) {current_time}.xlsx"

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
            
            # Создаем парсер с текущей конфигурацией и режимом
            enabled_iocs = self.config_manager.get_enabled_iocs()
            log(f"✅ Включенных типов IOC: {len(enabled_iocs)}")

            parser = IOCParser(enabled_iocs, mode=self.mode)
            
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
            
            # Создаем генератор отчетов с параметрами
            all_iocs = self.config_manager.get_enabled_iocs()
            generator = ReportGenerator(all_iocs, uri_clean_mode=self.uri_clean_mode)

            # Генерируем .xlsx отчет
            log("   • Создание .xlsx отчета (10 столбцов)...")
            xlsx_success = generator.generate_xlsx_report(
                ioc_data, output_xlsx_path,
                bulletin=self.bulletin,
                mode=self.mode,
                event_type=self.event_type
            )
            
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

    def generate_filters_file(self, ioc_data: dict, template_path: str,
                             output_path: str, log_callback=None) -> bool:
        """
        Генерирует файл "Фильтры.xlsx" на основе шаблона.

        Args:
            ioc_data: Данные IOC
            template_path: Путь к шаблону
            output_path: Путь для сохранения
            log_callback: Функция для логирования

        Returns:
            True если успешно, False при ошибке
        """
        def log(message):
            if log_callback:
                log_callback(message)

        try:
            log("📋 Генерация файла фильтров...")

            # Создаем генератор с текущими параметрами
            all_iocs = self.config_manager.get_enabled_iocs()
            generator = ReportGenerator(all_iocs, uri_clean_mode=self.uri_clean_mode)

            # Генерируем файл фильтров
            success = generator.generate_filters_xlsx(ioc_data, template_path, output_path, log_callback=log_callback)

            if success:
                return True
            else:
                log("❌ Ошибка при создании файла фильтров.")
                return False

        except Exception as e:
            log(f"❌ Ошибка при генерации фильтров: {str(e)}")
            return False
