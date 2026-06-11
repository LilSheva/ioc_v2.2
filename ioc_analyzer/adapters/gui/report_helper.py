"""
Вспомогательный модуль для координации создания отчетов в GUI.
"""

import os
import re
import shutil
from datetime import datetime
from typing import Any, Optional, Tuple

from ioc_analyzer.core.folder_naming import build_mailbox_folder_name
from ioc_analyzer.core.mailbox_layout import collect_docx_text_bundle
from ioc_analyzer.core.mailbox_types import MailboxLayout
from ioc_analyzer.core.models import IOC, ReportData
from ioc_analyzer.core.parser import IOCParser
from ioc_analyzer.core.parser.cleaner import deduplicate_iocs
from ioc_analyzer.core.query_builder import generate_query_data
from ioc_analyzer.core.report_naming import (
    bulletin_column_value,
    ioc_report_filename,
    filters_report_filename,
    vulnerabilities_report_filename,
    pick_bulletin_source_filename,
)


def export_gui_reports(
    service: Any,
    report_data: ReportData,
    report_dir: str,
    templates_dir: str,
    ioc_config: list[dict[str, Any]],
    uri_clean_mode: str,
) -> Tuple[bool, str, list[dict[str, Any]]]:
    """
    Экспортирует XLSX/CSV отчеты и генерирует данные для SIEM/NAD запросов в GUI.
    """
    service.exporter.ioc_config = ioc_config
    has_iocs = bool(report_data.indicators)
    has_bdu = bool(report_data.bdu_list)
    source = report_data.source_filename
    bulletin = report_data.fstek_bulletin
    mode = report_data.parser_mode

    report_path = (
        os.path.join(report_dir, ioc_report_filename(mode, source, bulletin))
        if has_iocs else None
    )
    filters_path = (
        os.path.join(report_dir, filters_report_filename(mode, source, bulletin))
        if has_iocs else None
    )
    cve_path = None
    if has_bdu:
        cve_path = os.path.join(
            report_dir,
            vulnerabilities_report_filename(mode, source, bulletin),
        )

    service.exporter.export_report(
        report_data,
        report_dir,
        templates_dir=templates_dir,
        report_path=report_path,
        filters_path=filters_path,
        cve_path=cve_path,
    )

    query_data = generate_query_data(
        report_data.indicators, ioc_config, uri_clean_mode
    )

    output_path = ""
    if report_path and os.path.isfile(report_path):
        output_path = report_path
    elif cve_path and os.path.isfile(cve_path):
        output_path = cve_path

    return True, output_path, query_data


def copy_selected_files_to_task(selected_files: list[str], task_dir: str, preserve: bool = True) -> None:
    """
    Копирует выбранные файлы в директорию «Задача».
    """
    os.makedirs(task_dir, exist_ok=True)
    for file_path in selected_files:
        if os.path.isfile(file_path):
            dest = os.path.join(task_dir, os.path.basename(file_path))
            if not (preserve and os.path.exists(dest)):
                shutil.copy2(file_path, dest)


def auto_fill_bulletin(selected_files: list[str]) -> Optional[str]:
    """Автоопределение номера бюллетеня из имен файлов ФСТЭК."""
    if not selected_files:
        return None
    pattern = r'\b(\d+)\s+(\d+)\s+(\d+)\b'
    for fp in selected_files:
        m = re.search(pattern, os.path.basename(fp))
        if m:
            return f"FSTEC {m.group(1)}/{m.group(2)}/{m.group(3)}"
    return None


def build_ip_comments(
    mode: str,
    bulletin: str,
    selected_files: list[str],
    ip_sources: list[Tuple[str, str]],
) -> dict[str, str]:
    """Строит комментарии для блокировки IP по режимам."""
    ip_comments = {}
    if mode == "fstek":
        fstec_comment = bulletin or auto_fill_bulletin(selected_files) or ""
        for ip, _filename in ip_sources:
            ip_comments.setdefault(ip, fstec_comment)
        return ip_comments
    for ip, filename in ip_sources:
        if ip in ip_comments:
            continue
        if not filename:
            ip_comments[ip] = ""
        else:
            ip_comments[ip] = bulletin_column_value("gossopka", filename)
    return ip_comments
