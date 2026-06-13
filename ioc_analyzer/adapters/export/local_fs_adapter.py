"""
Адаптер для работы с локальной файловой системой и сетевой шарой.
"""

import functools
import logging
import os
import shutil
import time

from ioc_analyzer.core.mailbox_types import MailboxLayout
from ioc_analyzer.core.models import ReportData
from ioc_analyzer.core.report_naming import (
    filters_report_filename,
    ioc_report_filename,
    vulnerabilities_report_filename,
)
from ioc_analyzer.ports.export_port import ExportPort
from ioc_analyzer.adapters.export.excel_report import generate_xlsx_report, generate_cve_xlsx_report
from ioc_analyzer.adapters.export.excel_filters import generate_filters_xlsx
from ioc_analyzer.adapters.export.csv_report import generate_csv_for_sasha

logger = logging.getLogger("ioc_analyzer.local_fs_adapter")


def retry_on_permission_error(max_attempts=5, initial_delay=0.1, backoff=2.0):
    """Декоратор для повторных попыток при PermissionError (блокировки Windows)."""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            delay = initial_delay
            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except PermissionError as e:
                    if attempt == max_attempts:
                        raise e
                    time.sleep(delay)
                    delay *= backoff
            return None
        return wrapper
    return decorator


class LocalFSAdapter(ExportPort):
    """Адаптер выгрузки отчетов на сетевую шару / локальный диск."""

    def __init__(
        self,
        share_path: str,
        preserve_files: bool = True,
        ioc_config: list[dict] | None = None,
        uri_clean_mode: str = "domain",
    ):
        self.share_path = share_path
        self.preserve_files = preserve_files
        self.ioc_config = ioc_config or []
        self.uri_clean_mode = uri_clean_mode

    def setup_mailbox_layout(self, folder_name: str) -> MailboxLayout:
        root = os.path.join(self.share_path, folder_name)
        layout = MailboxLayout(
            root=root,
            task=os.path.join(root, "Задача"),
            report=os.path.join(root, "Отчет"),
            templates=os.path.join(root, "Шаблоны IOC"),
        )
        os.makedirs(layout.task, exist_ok=True)
        os.makedirs(layout.report, exist_ok=True)
        os.makedirs(layout.templates, exist_ok=True)
        return layout

    def setup_directories(self, bulletin_num: str) -> str:
        safe_num = bulletin_num.replace("/", "-").replace("\\", "-").replace(":", "_")
        bulletin_dir = os.path.join(self.share_path, safe_num)
        os.makedirs(bulletin_dir, exist_ok=True)
        return bulletin_dir

    @retry_on_permission_error()
    def copy_bulletin_file(self, src_path: str, dest_dir: str) -> str:
        filename = os.path.basename(src_path)
        dest_path = os.path.join(dest_dir, filename)
        shutil.copy2(src_path, dest_path)
        return dest_path

    def export_report(
        self,
        report_data: ReportData,
        report_dir: str,
        templates_dir: str | None = None,
        report_path: str | None = None,
        filters_path: str | None = None,
        cve_path: str | None = None,
    ) -> None:
        import copy
        
        # Фильтруем индикаторы: исключаем только IP-адреса на разблокировку из отчетов и шаблонов
        report_data_for_export = copy.copy(report_data)
        report_data_for_export.indicators = [
            ioc for ioc in report_data.indicators 
            if not (ioc.ioc_type == "IP" and ioc.status == "unblock")
        ]

        os.makedirs(report_dir, exist_ok=True)
        csv_dir = templates_dir or report_dir
        os.makedirs(csv_dir, exist_ok=True)

        mode = report_data_for_export.parser_mode
        source = report_data_for_export.source_filename
        bulletin = report_data_for_export.fstek_bulletin
        has_iocs = bool(report_data_for_export.indicators)
        has_bdu = bool(report_data_for_export.bdu_list)

        if has_iocs:
            report_file = report_path or os.path.join(
                report_dir,
                ioc_report_filename(mode, source, bulletin),
            )
            if not generate_xlsx_report(
                report_data=report_data_for_export,
                output_path=report_file,
                ioc_config=self.ioc_config,
                uri_clean_mode=self.uri_clean_mode,
            ):
                raise OSError(f"Не удалось сохранить отчёт: {report_file}")

            filters_file = filters_path or os.path.join(
                report_dir,
                filters_report_filename(mode, source, bulletin),
            )
            if not generate_filters_xlsx(
                report_data=report_data_for_export,
                output_path=filters_file,
                ioc_config=self.ioc_config,
            ):
                raise OSError(f"Не удалось сохранить фильтры: {filters_file}")

            generate_csv_for_sasha(
                report_data=report_data_for_export,
                output_dir=csv_dir,
                k_value=None,
                delimiter=";",
                use_bom=True,
            )

        if has_bdu:
            cve_file = cve_path or os.path.join(
                report_dir,
                vulnerabilities_report_filename(mode, source, bulletin),
            )
            generate_cve_xlsx_report(report_data_for_export.bdu_list, cve_file)

