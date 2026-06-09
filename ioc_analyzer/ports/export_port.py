"""
Порт для экспорта отчетов и работы с файловой системой.
"""

import abc
from ioc_analyzer.core.models import ReportData


class ExportPort(abc.ABC):
    """
    Интерфейс для сохранения результатов парсинга на сетевую шару.
    """

    @abc.abstractmethod
    def setup_directories(self, bulletin_num: str) -> str:
        """
        Создает структуру директорий на сетевом ресурсе для бюллетеня.

        Args:
            bulletin_num: Номер бюллетеня (например, "Б-123").

        Returns:
            Путь к целевой директории для выгрузки.
        """
        pass

    @abc.abstractmethod
    def export_report(self, report_data: ReportData, dest_dir: str) -> None:
        """
        Генерирует Excel-отчет и CSV-списки в целевой директории.

        Args:
            report_data: Структурированные данные о найденных IOC.
            dest_dir: Целевая папка.
        """
        pass

    @abc.abstractmethod
    def copy_bulletin_file(self, src_path: str, dest_dir: str) -> str:
        """
        Копирует оригинальный файл бюллетеня в целевую директорию.

        Args:
            src_path: Исходный путь к файлу.
            dest_dir: Целевая директория.

        Returns:
            Новый путь к скопированному файлу.
        """
        pass
