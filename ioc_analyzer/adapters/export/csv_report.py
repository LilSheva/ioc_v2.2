"""
Адаптер для генерации CSV отчетов ("Для Саши").
"""

import csv
import os
from typing import Optional
from ioc_analyzer.core.models import ReportData


def generate_csv_for_sasha(
    report_data: ReportData,
    output_dir: str,
    k_value: Optional[int] = None,
    delimiter: str = ';',
    use_bom: bool = True
) -> bool:
    """
    Генерирует Value.csv и IOC_hash_manually.csv с хэш-индикаторами.
    """
    try:
        # Формируем описание бюллетеня
        description = ""
        if report_data.parser_mode == "fstek":
            description = report_data.source_filename
        else:
            # Пытаемся распарсить из имени ГосСОПКА
            import re
            pattern = r'Бюллетень\s+от\s+(\d{2}\.\d{2}\.\d{4})_(\d+)\s+(.+?)\.docx'
            match = re.search(pattern, report_data.source_filename, re.IGNORECASE)
            if match:
                description = f"{match.group(3).strip()} от {match.group(1)} ({match.group(2)})"
            else:
                description = os.path.splitext(report_data.source_filename)[0]

        # Извлекаем хэши из списка индикаторов
        sha256_list = []
        sha1_list = []
        md5_list = []

        for ioc in report_data.indicators:
            if ioc.ioc_type == "SHA256":
                sha256_list.append(ioc.clean_value)
            elif ioc.ioc_type == "SHA1":
                sha1_list.append(ioc.clean_value)
            elif ioc.ioc_type == "MD5":
                md5_list.append(ioc.clean_value)

        encoding = 'utf-8-sig' if use_bom else 'utf-8'

        # 1. Запись Value.csv
        value_path = os.path.join(output_dir, "Value.csv")
        with open(value_path, 'w', newline='', encoding=encoding) as f:
            writer = csv.writer(f, delimiter=delimiter)
            writer.writerow(["value", "category", "description"])
            for h in sha256_list:
                writer.writerow([h, "hash", description])
            for h in sha1_list:
                writer.writerow([h, "hash", description])
            for h in md5_list:
                writer.writerow([h, "hash", description])

        # 2. Запись IOC_hash_manually.csv
        manual_path = os.path.join(output_dir, "IOC_hash_manually.csv")
        max_len = max(len(sha256_list), len(md5_list), 1)

        with open(manual_path, 'w', newline='', encoding=encoding) as f:
            writer = csv.writer(f, delimiter=delimiter)
            writer.writerow(["Number", "hash_sha256", "hash_md5", "description"])
            for i in range(max_len):
                number = k_value + i if k_value is not None else ""
                sha256_val = sha256_list[i] if i < len(sha256_list) else ""
                md5_val = md5_list[i] if i < len(md5_list) else ""
                writer.writerow([number, sha256_val, md5_val, description])

        return True
    except Exception as e:
        print(f"Ошибка при создании CSV: {e}")
        return False
