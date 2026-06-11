"""Контроллер-адаптер для связи GUI со службой ядра."""

import logging
import os
import re
from datetime import datetime
from typing import Any, Optional, Tuple

from ioc_analyzer.core.constants import DEFAULT_FSTEC_EVENT_TYPE
from ioc_analyzer.core.folder_naming import build_mailbox_folder_name
from ioc_analyzer.core.mailbox_layout import collect_docx_text_bundle
from ioc_analyzer.core.mailbox_types import MailboxLayout
from ioc_analyzer.core.models import IOC, ReportData
from ioc_analyzer.core.parser import IOCParser
from ioc_analyzer.core.parser.cleaner import deduplicate_iocs
from ioc_analyzer.core.parser.mode_detect import detect_mailbox_parser_mode
from ioc_analyzer.core.query_builder import build_query
from ioc_analyzer.core.report_naming import (
    filters_report_filename,
    ioc_report_filename,
    pick_bulletin_source_filename,
    vulnerabilities_report_filename,
)
from ioc_analyzer.adapters.gui.report_helper import (
    export_gui_reports,
    copy_selected_files_to_task,
    auto_fill_bulletin,
    build_ip_comments,
)
from ioc_analyzer.adapters.ip_block import api_adapter as ip_block_api

logger = logging.getLogger("ioc_analyzer.gui_controller")


class GuiController:
    def __init__(self, service: Any, config_manager: Any):
        self.service = service
        self.config_manager = config_manager
        self.selected_files: list[str] = []
        self.last_ioc_data: Optional[dict[str, list[IOC]]] = None
        self.last_bdu_data: list[Tuple[str, str]] = []
        self._last_unblock_data: dict[str, list[IOC]] = {}
        self._last_query_data: list[dict[str, Any]] = []
        self._last_output_path: str = ""
        self._last_layout: Optional[MailboxLayout] = None
        self.bulletin = ""
        self.mode = "fstek"
        self.uri_clean_mode = "domain"

    def get_state_file_path(self) -> str: return self.config_manager.config_path
    def get_config_data(self) -> list[dict[str, Any]]: return self.config_manager.get_ioc_config()
    def save_config(self, updated: list[dict[str, Any]]) -> bool: return self.config_manager.set_ioc_config(updated)
    def reset_ioc_to_default(self, idx: int) -> bool: return self.config_manager.reset_single(idx)
    def reset_all_to_defaults(self) -> bool: return self.config_manager.reset_all()
    def move_ioc_priority(self, idx: int, direction: int) -> bool: return self.config_manager.move_ioc(idx, direction)
    def get_mode(self) -> str: return self.mode
    def set_mode(self, mode: str) -> None: self.mode = mode
    def get_uri_clean_mode(self) -> str: return self.uri_clean_mode
    def set_uri_clean_mode(self, mode: str) -> None: self.uri_clean_mode = mode
    def get_bulletin(self) -> str: return self.bulletin
    def set_bulletin(self, bulletin: str) -> None: self.bulletin = bulletin
    def add_files(self, paths: list[str]) -> int:
        added = 0
        for fp in paths:
            if fp not in self.selected_files and fp.lower().endswith('.docx'):
                self.selected_files.append(fp)
                added += 1
        return added

    def clear_files(self) -> None: self.selected_files.clear()
    def get_selected_files(self) -> list[str]: return self.selected_files.copy()

    def suggest_mode_from_files(self, log_callback=None) -> Optional[str]:
        files = self.get_selected_files()
        if not files:
            return None
        mode, err = detect_mailbox_parser_mode(files, self.service.doc_reader)
        if err or not mode:
            if log_callback and err:
                log_callback(f"⚠ Режим не определён автоматически: {err}")
            return None
        self.set_mode(mode)
        if log_callback:
            log_callback(f"Режим определён автоматически: {mode.upper()}")
        return mode

    def _create_mailbox_layout(self, parent_dir: str) -> MailboxLayout:
        docx_paths = [f for f in self.selected_files if f.lower().endswith(".docx")]
        doc_text, metadata_num = collect_docx_text_bundle(docx_paths, self.service.doc_reader, self.get_config_data())
        folder_name = build_mailbox_folder_name(
            self.mode,
            received_time=datetime.now(),
            doc_text=doc_text,
            first_docx_name=self._report_source_filename(docx_paths),
            metadata_num=metadata_num,
        )
        exporter = self.service.exporter
        prev_share = exporter.share_path
        exporter.share_path = parent_dir
        try:
            layout = exporter.setup_mailbox_layout(folder_name)
        finally:
            exporter.share_path = prev_share
        return layout

    def _copy_sources_to_task(self, task_dir: str) -> None:
        preserve = self.config_manager.config_data.get("preserve_existing_files", True)
        copy_selected_files_to_task(self.selected_files, task_dir, preserve)

    def auto_fill_bulletin(self) -> Optional[str]:
        return auto_fill_bulletin(self.selected_files)

    def _report_source_filename(self, file_paths: list[str] | None = None) -> str:
        files = file_paths or self.get_selected_files()
        ioc_sources = []
        if self.last_ioc_data:
            for iocs in self.last_ioc_data.values():
                for ioc in iocs:
                    if ioc.source_file:
                        ioc_sources.append(ioc.source_file)
        return pick_bulletin_source_filename(files, self.mode, ioc_sources)

    def _fstek_bulletin_value(self) -> str:
        return self.bulletin or self.auto_fill_bulletin() or ""

    def generate_report_filename(self) -> str:
        return ioc_report_filename(self.mode, self._report_source_filename(), self._fstek_bulletin_value())

    def generate_filters_filename(self) -> str:
        return filters_report_filename(self.mode, self._report_source_filename(), self._fstek_bulletin_value())

    def generate_cve_filename(self) -> str:
        return vulnerabilities_report_filename(self.mode, self._report_source_filename(), self._fstek_bulletin_value())

    def process_files(self, log_callback=None) -> Tuple[bool, Optional[dict]]:
        try:
            self.service.settings["ioc_config"] = self.get_config_data()
            parser = self.service.doc_reader
            p = IOCParser(self.get_config_data(), mode=self.mode, document_reader=parser)
            parsed_raw = p.parse(self.selected_files)
            ioc_data: dict[str, list[IOC]] = {}
            unblocked: dict[str, list[IOC]] = {}
            for ioc_type, items in parsed_raw.items():
                ioc_data[ioc_type] = []
                unblocked[ioc_type] = []
                for orig, clean, meta in items:
                    file_mode = meta.get("parser_mode", self.mode)
                    context = meta.get("event_type") or ("" if file_mode == "gossopka" else DEFAULT_FSTEC_EVENT_TYPE)
                    ioc_obj = IOC(
                        ioc_type=ioc_type, raw_value=orig, clean_value=clean,
                        status=meta.get("status", "block"), context=context,
                        source_file=meta.get("filename", ""), parser_mode=file_mode,
                    )
                    if meta.get("status") == "unblock" and self.mode == "gossopka":
                        unblocked[ioc_type].append(ioc_obj)
                    else:
                        ioc_data[ioc_type].append(ioc_obj)
            for ioc_type in ioc_data:
                ioc_data[ioc_type] = deduplicate_iocs(ioc_data[ioc_type])
            for ioc_type in unblocked:
                unblocked[ioc_type] = deduplicate_iocs(unblocked[ioc_type])
            self.last_ioc_data = ioc_data
            self._last_unblock_data = unblocked
            self.last_bdu_data = p.extract_bdu_identifiers(self.selected_files)
            if log_callback:
                log_callback("Найдено уникальных индикаторов:")
                for k, v in ioc_data.items():
                    if v: log_callback(f"  • {k}: {len(v)}")
            return True, ioc_data
        except Exception as e:
            if log_callback: log_callback(f"Ошибка парсинга: {e}")
            return False, None

    def _build_report_data(self, ioc_data: dict) -> ReportData:
        ioc_data = ioc_data or {}
        flat_iocs = [ioc for iocs in ioc_data.values() for ioc in iocs]
        ioc_sources = [ioc.source_file for ioc in flat_iocs if ioc.source_file]
        return ReportData(
            source_filename=pick_bulletin_source_filename(self.get_selected_files(), self.mode, ioc_sources),
            parser_mode=self.mode, parsed_at=datetime.now(), indicators=flat_iocs,
            bdu_list=[b for b, _ in self.last_bdu_data], fstek_bulletin=self._fstek_bulletin_value(),
        )

    def _export_report_data(self, report_data: ReportData, report_dir: str, templates_dir: str, log_callback=None) -> bool:
        try:
            ok, out_path, q_data = export_gui_reports(
                self.service, report_data, report_dir, templates_dir, self.get_config_data(), self.uri_clean_mode
            )
            self._last_query_data = q_data
            self._last_output_path = out_path
            if log_callback and ok: log_callback("Отчеты успешно сохранены.")
            return ok
        except Exception as e:
            if log_callback: log_callback(f"Ошибка сохранения отчетов: {e}")
            return False

    def generate_reports_mailbox(self, ioc_data: dict, parent_dir: str, log_callback=None) -> Tuple[bool, Optional[MailboxLayout]]:
        try:
            layout = self._create_mailbox_layout(parent_dir)
            self._copy_sources_to_task(layout.task)
            if log_callback: log_callback(f"Создана папка: {layout.root}")
            report_data = self._build_report_data(ioc_data)
            ok = self._export_report_data(report_data, layout.report, layout.templates, log_callback)
            if ok:
                self._last_layout = layout
                if not self._last_output_path: self._last_output_path = layout.root
            return ok, layout if ok else None
        except OSError as e:
            if log_callback: log_callback(f"Ошибка создания структуры папок: {e}")
            return False, None

    def send_ips_to_api(self, block_ips: list[Tuple[str, str]]) -> dict[str, dict]:
        ip_comments = self._build_ip_comments(block_ips)
        if not ip_comments: return {}
        api_url = (self.config_manager.config_data.get("api_url") or "").strip()
        api_key = (self.config_manager.config_data.get("api_key") or "").strip()
        if not api_url or not api_key:
            return {ip: {"status": "NO_CONFIG", "text": "API не настроен"} for ip in ip_comments}
        _ok, per_ip = ip_block_api.send_to_api(ip_comments, api_url, api_key)
        return per_ip

    def _build_ip_comments(self, ip_sources: list[Tuple[str, str]]) -> dict[str, str]:
        return build_ip_comments(self.mode, self.bulletin, self.selected_files, ip_sources)

    def build_query(self, template: str, chunk: list[str], join_op: str) -> str:
        return build_query(template, chunk, join_op)

    def get_last_query_data(self) -> list[dict[str, Any]]: return self._last_query_data
    def get_last_unblock_data(self) -> dict[str, list[IOC]]: return self._last_unblock_data

    @property
    def last_unblock_data(self) -> dict[str, list[IOC]]: return self._last_unblock_data
