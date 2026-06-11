"""
Адаптер для генерации CSV отчетов ("Для Саши").
"""

import csv
import logging
import os
from typing import Optional

from ioc_analyzer.core.models import ReportData
from ioc_analyzer.core.report_naming import bulletin_column_value

logger = logging.getLogger("ioc_analyzer.csv_report")


def generate_csv_for_sasha(
    report_data: ReportData,
    output_dir: str,
    k_value: Optional[int] = None,
    delimiter: str = ";",
    use_bom: bool = True,
) -> bool:
    """
    Генерирует Value.csv и IOC_hash_manually.csv с хэш-индикаторами.
    """
    try:
        sha256_list: list[tuple[str, str]] = []
        sha1_list: list[tuple[str, str]] = []
        md5_list: list[tuple[str, str]] = []

        for ioc in report_data.indicators:
            src = ioc.source_file or report_data.source_filename
            desc = bulletin_column_value(
                ioc.parser_mode or report_data.parser_mode,
                src,
                report_data.fstek_bulletin,
            )
            if ioc.ioc_type == "SHA256":
                sha256_list.append((ioc.clean_value, desc))
            elif ioc.ioc_type == "SHA1":
                sha1_list.append((ioc.clean_value, desc))
            elif ioc.ioc_type == "MD5":
                md5_list.append((ioc.clean_value, desc))

        if not sha256_list and not sha1_list and not md5_list:
            return True

        encoding = "utf-8-sig" if use_bom else "utf-8"

        value_path = os.path.join(output_dir, "Value.csv")
        with open(value_path, "w", newline="", encoding=encoding) as f:
            writer = csv.writer(f, delimiter=delimiter)
            writer.writerow(["value", "category", "description"])
            for items in (sha256_list, sha1_list, md5_list):
                for value, desc in items:
                    writer.writerow([value, "hash", desc])

        manual_path = os.path.join(output_dir, "IOC_hash_manually.csv")
        max_len = max(len(sha256_list), len(md5_list), 1)
        with open(manual_path, "w", newline="", encoding=encoding) as f:
            writer = csv.writer(f, delimiter=delimiter)
            writer.writerow(["Number", "hash_sha256", "hash_md5", "description"])
            for i in range(max_len):
                number = k_value + i if k_value is not None else ""
                sha256_val, sha256_desc = (
                    sha256_list[i] if i < len(sha256_list) else ("", "")
                )
                md5_val, md5_desc = md5_list[i] if i < len(md5_list) else ("", "")
                desc = sha256_desc or md5_desc
                writer.writerow([number, sha256_val, md5_val, desc])

        return True
    except OSError as e:
        logger.error("Ошибка при создании CSV: %s", e, exc_info=True)
        return False
