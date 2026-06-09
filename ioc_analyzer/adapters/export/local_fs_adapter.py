"""
Адаптер для работы с локальной файловой системой и сетевой шарой.
"""

import functools
import logging
import os
import shutil
import time
from datetime import datetime

from ioc_analyzer.core.models import ReportData
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
    """
    Адаптер выгрузки отчетов на сетевую шару / локальный диск.
    """

    def __init__(
        self,
        share_path: str,
        preserve_files: bool = True,
        ioc_config: list[dict] | None = None,
        uri_clean_mode: str = "domain",
    ):
        """
        Инициализация файлового адаптера.
        """
        self.share_path = share_path
        self.preserve_files = preserve_files
        self.ioc_config = ioc_config or []
        self.uri_clean_mode = uri_clean_mode

    def setup_directories(self, bulletin_num: str) -> str:
        """
        Создает структуру папок: share_path/bulletin_num и share_path/bulletin_num/original.
        """
        # Очищаем имя от символов пути
        safe_num = bulletin_num.replace('/', '-').replace('\\', '-').replace(':', '_')
        bulletin_dir = os.path.join(self.share_path, safe_num)
        original_dir = os.path.join(bulletin_dir, "original")

        os.makedirs(original_dir, exist_ok=True)
        return bulletin_dir

    @retry_on_permission_error()
    def copy_bulletin_file(self, src_path: str, dest_dir: str) -> str:
        """
        Копирует исходный файл во вложенную папку original.
        """
        filename = os.path.basename(src_path)
        dest_path = os.path.join(dest_dir, "original", filename)
        shutil.copy2(src_path, dest_path)
        return dest_path

    def export_report(self, report_data: ReportData, dest_dir: str) -> None:
        """
        Генерирует Excel отчеты, фильтры, CVE и CSV списки.
        """
        current_time = datetime.now().strftime('%d.%m.%Y %H-%M')
        bulletin_name = os.path.splitext(report_data.source_filename)[0].replace('/', '-')

        # 1. Основной xlsx-отчет (IOC Report)
        report_filename = f"Отчет ({bulletin_name}) {current_time}.xlsx"
        report_path = os.path.join(dest_dir, report_filename)
        generate_xlsx_report(
            report_data=report_data,
            output_path=report_path,
            ioc_config=self.ioc_config,
            uri_clean_mode=self.uri_clean_mode,
        )

        # 2. Файл фильтров
        filters_filename = f"Фильтры ({bulletin_name}) {current_time}.xlsx"
        filters_path = os.path.join(dest_dir, filters_filename)
        generate_filters_xlsx(
            report_data=report_data,
            output_path=filters_path,
            ioc_config=self.ioc_config
        )

        # 3. Отчет CVE (если добавлены BDU в ReportData или найдены в индикаторах)
        # В нашей модели BDU-идентификаторы можно вытащить или передать.
        # Для простоты вытащим их из списка индикаторов (если есть тип SHA256/SHA1/MD5/File,
        # но BDU не являются IOC по умолчанию, поэтому передадим их через атрибут, если он есть)
        bdu_list = getattr(report_data, "bdu_list", [])
        if bdu_list:
            cve_filename = f"CVE ({bulletin_name}) {current_time}.xlsx"
            cve_path = os.path.join(dest_dir, cve_filename)
            generate_cve_xlsx_report(bdu_list, cve_path)

        # 4. CSV для Саши
        generate_csv_for_sasha(
            report_data=report_data,
            output_dir=dest_dir,
            k_value=None,
            delimiter=';',
            use_bom=True
        )
