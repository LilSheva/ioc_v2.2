"""Контроллер приложения для координации между моделью и представлением."""

import os
from typing import List, Optional, Tuple
from ..model.config_manager import ConfigManager
from ..model.ioc_parser_v21_fixed import IOCParser
from ..model.report_generator import ReportGenerator


class AppController:
    """Главный контроллер приложения."""

    def __init__(self, config_path: str = None):
        """Инициализация контроллера.

        Args:
            config_path: Обратная совместимость. Если передан путь к .txt —
                         берётся его директория как state_dir. Иначе
                         трактуется как state_dir напрямую. None — умолчание.
        """
        if config_path and config_path.endswith('.txt'):
            state_dir = os.path.dirname(os.path.abspath(config_path)) or '.'
        else:
            state_dir = config_path
        self.config_manager = ConfigManager(state_dir)
        self.selected_files: List[str] = []
        self.last_ioc_data = None
        self.last_query_data = None
        self.last_bdu_data = []
        self.bulletin = ""
        self.mode = "fstek"
        self.uri_clean_mode = "domain"
        self.event_type = "Фишинговая рассылка электронной почты. Вредоносные вложения"
    
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

            # Фильтрация unblock IOC (только ГосСОПКА)
            if self.mode == "gossopka":
                unblock_iocs = {}
                for ioc_type, ioc_list in ioc_data.items():
                    unblocked = [x for x in ioc_list if x[2].get("status") == "unblock"]
                    kept = [x for x in ioc_list if x[2].get("status") != "unblock"]
                    if unblocked:
                        unblock_iocs[ioc_type] = unblocked
                    ioc_data[ioc_type] = kept

                if unblock_iocs:
                    total_unblock = sum(len(v) for v in unblock_iocs.values())
                    log(f"\n⚠️ Найдено {total_unblock} IOC на РАЗБЛОКИРОВКУ (исключены из отчёта):")
                    for ioc_type, items in unblock_iocs.items():
                        for _, cleaned, meta in items:
                            log(f"   🔓 [{ioc_type}] {cleaned} (файл: {meta['filename']})")

            # Дедупликация по cleaned значению
            total_before = sum(len(v) for v in ioc_data.values())
            for ioc_type in ioc_data:
                seen = set()
                deduped = []
                for item in ioc_data[ioc_type]:
                    if item[1] not in seen:
                        seen.add(item[1])
                        deduped.append(item)
                ioc_data[ioc_type] = deduped
            total_after = sum(len(v) for v in ioc_data.values())

            if total_before != total_after:
                log(f"\n🔄 Удалено дубликатов: {total_before - total_after}")

            # Подсчитываем результаты
            total_iocs = sum(len(iocs) for iocs in ioc_data.values())

            log(f"\n✨ Извлечение завершено!")
            log(f"📊 Найдено IOC по типам:")

            for ioc_type, iocs in ioc_data.items():
                if iocs:
                    if self.mode == "gossopka":
                        blocks = sum(1 for x in iocs if x[2].get("status") == "block")
                        searches = sum(1 for x in iocs if x[2].get("status") == "search")
                        log(f"   • {ioc_type}: {len(iocs)} (🔒 block: {blocks}, 🔍 search: {searches})")
                    else:
                        log(f"   • {ioc_type}: {len(iocs)}")
                else:
                    log(f"   • {ioc_type}: 0")

            log(f"\n📈 Всего уникальных IOC: {total_iocs}")

            # Извлекаем BDU-идентификаторы
            bdu_list = parser.extract_bdu_identifiers(self.selected_files)
            if bdu_list:
                log(f"\n📋 Найдено {len(bdu_list)} BDU-идентификаторов уязвимостей")
                for bdu_id, fname in bdu_list:
                    log(f"   • {bdu_id} ({fname})")
            self.last_bdu_data = bdu_list

            # Сохраняем для последующего использования
            self.last_ioc_data = ioc_data

            return True, ioc_data
            
        except Exception as e:
            log(f"\n❌ Критическая ошибка: {str(e)}")
            return False, None
    
    def generate_reports(self, ioc_data: dict, output_xlsx_path: str,
                        log_callback=None) -> Tuple[bool, Optional[str]]:
        """Генерирует отчёт .xlsx (с листами IOC Report и Запросы) + файл фильтров."""
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

            # Генерируем .xlsx отчет (IOC Report + Запросы)
            log("   • Создание .xlsx отчета...")
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

            # Генерируем данные запросов для GUI
            self.last_query_data = generator.generate_query_data(ioc_data)

            # Генерируем файл фильтров
            filter_filename = self.generate_filters_filename()
            filters_path = os.path.join(os.path.dirname(output_xlsx_path), filter_filename)
            self.generate_filters_file(ioc_data, filters_path, log_callback=log_callback)

            # Сохраняем BDU в текстовый файл
            base_name = os.path.splitext(output_xlsx_path)[0]
            if self.last_bdu_data:
                bdu_path = f"{base_name}_bdu.txt"
                with open(bdu_path, 'w', encoding='utf-8') as f:
                    f.write("BDU-идентификаторы уязвимостей\n")
                    f.write("=" * 40 + "\n\n")
                    for bdu_id, fname in self.last_bdu_data:
                        f.write(f"{bdu_id}  ({fname})\n")
                log(f"   ✅ BDU-идентификаторы сохранены: {os.path.basename(bdu_path)}")

            log("\n🎉 Все отчеты успешно созданы!")

            return True, None

        except Exception as e:
            log(f"\n❌ Ошибка при генерации отчетов: {str(e)}")
            return False, None
    
    @staticmethod
    def build_query(template, ioc_values, join_op):
        """Обёртка для сборки запроса из шаблона и списка IOC."""
        return ReportGenerator._build_query(template, ioc_values, join_op)

    def get_last_query_data(self):
        """Возвращает данные последних сгенерированных запросов."""
        return self.last_query_data
    
    def move_ioc_priority(self, index: int, direction: int) -> bool:
        """Изменяет приоритет IOC."""
        return self.config_manager.move_ioc(index, direction)

    def reset_ioc_to_default(self, index: int) -> bool:
        """Сбрасывает один IOC к значениям по умолчанию."""
        return self.config_manager.reset_ioc_to_default(index)

    def reset_all_to_defaults(self) -> None:
        """Сбрасывает всю конфигурацию к умолчаниям."""
        self.config_manager.reset_all_to_defaults()

    def get_state_file_path(self) -> str:
        """Возвращает путь к файлу настроек."""
        return self.config_manager.state_file_path

    def generate_filters_file(self, ioc_data: dict,
                             output_path: str, log_callback=None) -> bool:
        """
        Генерирует файл "Фильтры.xlsx" программно.

        Args:
            ioc_data: Данные IOC
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
            success = generator.generate_filters_xlsx(ioc_data, output_path, log_callback=log_callback)

            if success:
                return True
            else:
                log("❌ Ошибка при создании файла фильтров.")
                return False

        except Exception as e:
            log(f"❌ Ошибка при генерации фильтров: {str(e)}")
            return False
