"""
Порт для экспорта отчетов и работы с файловой системой.
"""

import abc
from ioc_analyzer.core.mailbox_types import MailboxLayout
from ioc_analyzer.core.models import ReportData


class ExportPort(abc.ABC):
    """
    Интерфейс для сохранения результатов парсинга на сетевую шару.
    """

    @abc.abstractmethod
    def setup_mailbox_layout(self, folder_name: str) -> MailboxLayout:
        """
        Создаёт legacy-структуру: корень / Задача / Отчет / Шаблоны IOC.
        """
        pass

    @abc.abstractmethod
    def export_report(
        self,
        report_data: ReportData,
        report_dir: str,
        templates_dir: str | None = None,
        report_path: str | None = None,
        filters_path: str | None = None,
        cve_path: str | None = None,
    ) -> None:
        """
        Генерирует Excel в report_dir и CSV в templates_dir (или report_dir).
        """
        pass

    @abc.abstractmethod
    def copy_bulletin_file(self, src_path: str, dest_dir: str) -> str:
        """
        Копирует файл в целевую директорию (для GUI / совместимости).
        """
        pass
