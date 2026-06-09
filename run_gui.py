"""
Графический интерфейс пользователя (GUI) - Точка входа.
"""

import os
from datetime import datetime
from typing import Any, Optional, Tuple

from ioc_analyzer.adapters.document.docx_adapter import DocxAdapter
from ioc_analyzer.adapters.mail.exchange_adapter import ExchangeAdapter
from ioc_analyzer.adapters.export.local_fs_adapter import LocalFSAdapter
from ioc_analyzer.adapters.ip_block import api_adapter as ip_block_api
from ioc_analyzer.adapters.ip_block.api_adapter import IpBlockApiAdapter
from ioc_analyzer.adapters.ip_block.mock_ip_block import MockIpBlockAdapter
from ioc_analyzer.adapters.gui.tkinter_gui import MainView

from ioc_analyzer.core.constants import DEFAULT_FSTEC_EVENT_TYPE
from ioc_analyzer.core.report_naming import (
    filters_report_filename,
    ioc_report_filename,
    vulnerabilities_report_filename,
)
from ioc_analyzer.core.config_manager import ConfigManager
from ioc_analyzer.core.service import AppService
from ioc_analyzer.core.query_builder import generate_query_data, build_query
from ioc_analyzer.core.models import IOC, ReportData


class GuiController:
    """Контроллер-адаптер для связи GUI со службой ядра."""

    def __init__(self, service: AppService, config_manager: ConfigManager):
        self.service = service
        self.config_manager = config_manager
        
        self.selected_files: list[str] = []
        self.last_ioc_data: Optional[dict[str, list[IOC]]] = None
        self.last_bdu_data: list[Tuple[str, str]] = []
        self._last_unblock_data: dict[str, list[IOC]] = {}
        self._last_query_data: list[dict[str, Any]] = []
        self._last_output_path: str = ""

        self.bulletin = ""
        self.mode = "fstek"
        self.uri_clean_mode = "domain"

    def get_state_file_path(self) -> str:
        return self.config_manager.config_path

    def get_config_data(self) -> list[dict[str, Any]]:
        return self.config_manager.get_ioc_config()

    def save_config(self, updated_config: list[dict[str, Any]]) -> bool:
        return self.config_manager.set_ioc_config(updated_config)

    def reset_ioc_to_default(self, index: int) -> bool:
        return self.config_manager.reset_single(index)

    def reset_all_to_defaults(self) -> bool:
        return self.config_manager.reset_all()

    def move_ioc_priority(self, index: int, direction: int) -> bool:
        return self.config_manager.move_ioc(index, direction)

    def get_mode(self) -> str: return self.mode
    def set_mode(self, mode: str) -> None: self.mode = mode
    def get_uri_clean_mode(self) -> str: return self.uri_clean_mode
    def set_uri_clean_mode(self, mode: str) -> None: self.uri_clean_mode = mode
    def get_bulletin(self) -> str: return self.bulletin
    def set_bulletin(self, bulletin: str) -> None: self.bulletin = bulletin

    def add_files(self, file_paths: list[str]) -> int:
        added = 0
        for fp in file_paths:
            if fp not in self.selected_files and fp.lower().endswith('.docx'):
                self.selected_files.append(fp)
                added += 1
        return added

    def clear_files(self) -> None: self.selected_files.clear()
    def get_selected_files(self) -> list[str]: return self.selected_files.copy()

    def auto_fill_bulletin(self) -> Optional[str]:
        if not self.selected_files:
            return None
        import re
        pattern = r'\b(\d+)\s+(\d+)\s+(\d+)\b'
        for fp in self.selected_files:
            m = re.search(pattern, os.path.basename(fp))
            if m:
                return f"FSTEC {m.group(1)}/{m.group(2)}/{m.group(3)}"
        return None

    def _report_source_filename(self) -> str:
        files = self.get_selected_files()
        return os.path.basename(files[0]) if files else "bulletin.docx"

    def _fstek_bulletin_value(self) -> str:
        return self.bulletin or self.auto_fill_bulletin() or ""

    def generate_report_filename(self) -> str:
        return ioc_report_filename(
            self.mode, self._report_source_filename(), self._fstek_bulletin_value()
        )

    def generate_filters_filename(self) -> str:
        return filters_report_filename(
            self.mode, self._report_source_filename(), self._fstek_bulletin_value()
        )

    def generate_cve_filename(self) -> str:
        return vulnerabilities_report_filename(
            self.mode, self._report_source_filename(), self._fstek_bulletin_value()
        )

    def process_files(self, log_callback=None) -> Tuple[bool, Optional[dict]]:
        # Запускает локальный парсинг через AppService без выгрузки на шару
        try:
            self.service.settings["ioc_config"] = self.get_config_data()
            parser = self.service.doc_reader
            
            # Собираем сырой парсинг
            raw_parsed = self.service.settings.get("ioc_config", [])
            from ioc_analyzer.core.parser import IOCParser
            p = IOCParser(raw_parsed, mode=self.mode, document_reader=parser)
            parsed_raw = p.parse(self.selected_files)

            ioc_data: dict[str, list[IOC]] = {}
            unblocked = {}
            
            for ioc_type, items in parsed_raw.items():
                ioc_data[ioc_type] = []
                unblocked[ioc_type] = []
                for orig, clean, meta in items:
                    file_mode = meta.get("parser_mode", self.mode)
                    if file_mode == "gossopka":
                        context = meta.get("event_type") or ""
                    else:
                        context = meta.get("event_type") or DEFAULT_FSTEC_EVENT_TYPE
                    ioc_obj = IOC(
                        ioc_type=ioc_type, raw_value=orig, clean_value=clean,
                        status=meta.get("status", "block"), context=context,
                        source_file=meta.get("filename", ""), parser_mode=file_mode,
                    )
                    if meta.get("status") == "unblock" and self.mode == "gossopka":
                        unblocked[ioc_type].append(ioc_obj)
                    else:
                        ioc_data[ioc_type].append(ioc_obj)

            self.last_ioc_data = ioc_data
            self._last_unblock_data = unblocked
            self.last_bdu_data = p.extract_bdu_identifiers(self.selected_files)
            
            # Логируем результаты
            if log_callback:
                log_callback(f"Найдено уникальных индикаторов:")
                for k, v in ioc_data.items():
                    if v: log_callback(f"  • {k}: {len(v)}")
            return True, ioc_data
        except Exception as e:
            if log_callback: log_callback(f"Ошибка парсинга: {e}")
            return False, None

    def generate_reports(self, ioc_data: dict, output_path: str, log_callback=None) -> Tuple[bool, None]:
        try:
            ioc_data = ioc_data or {}
            flat_iocs = []
            for iocs in ioc_data.values():
                flat_iocs.extend(iocs)

            main_filename = self._report_source_filename()
            fstek_bulletin = self._fstek_bulletin_value()
            report_data = ReportData(
                source_filename=main_filename,
                parser_mode=self.mode,
                parsed_at=datetime.now(),
                indicators=flat_iocs,
                bdu_list=[b for b, _ in self.last_bdu_data],
                fstek_bulletin=fstek_bulletin,
            )

            self.service.exporter.ioc_config = self.get_config_data()
            dest_dir = os.path.dirname(output_path) or "."
            has_iocs = bool(flat_iocs)
            has_bdu = bool(report_data.bdu_list)

            report_path = output_path if has_iocs else None
            filters_path = (
                os.path.join(dest_dir, self.generate_filters_filename()) if has_iocs else None
            )
            cve_path = None
            if has_bdu:
                cve_path = (
                    output_path if not has_iocs
                    else os.path.join(dest_dir, self.generate_cve_filename())
                )

            self.service.exporter.export_report(
                report_data,
                dest_dir,
                report_path=report_path,
                filters_path=filters_path,
                cve_path=cve_path,
            )
            self._last_output_path = output_path if has_iocs else (cve_path or output_path)
            
            # Заполняем query data
            self._last_query_data = generate_query_data(flat_iocs, self.get_config_data(), self.uri_clean_mode)
            
            if log_callback: log_callback("Отчеты успешно сохранены.")
            return True, None
        except Exception as e:
            if log_callback: log_callback(f"Ошибка сохранения отчетов: {e}")
            return False, None

    def send_ips_to_api(self, block_ips: list[Tuple[str, str]]) -> dict[str, dict]:
        ip_comments = self._build_ip_comments(block_ips)

        if not ip_comments:
            return {}

        api_url = (self.config_manager.config_data.get("api_url") or "").strip()
        api_key = (self.config_manager.config_data.get("api_key") or "").strip()
        if not api_url or not api_key:
            return {ip: {"status": "NO_CONFIG", "text": "API не настроен"} for ip in ip_comments}

        _ok, per_ip = ip_block_api.send_to_api(ip_comments, api_url, api_key)
        return per_ip

    def _build_ip_comments(self, ip_sources: list[Tuple[str, str]]) -> dict[str, str]:
        """Строит dict[ip, comment] из пар (ip, filename) согласно режиму."""
        ip_comments = {}

        if self.mode == "fstek":
            fstec_comment = self.bulletin or self.auto_fill_bulletin() or ""
            for ip, _filename in ip_sources:
                ip_comments.setdefault(ip, fstec_comment)
            return ip_comments

        # ГосСОПКА — per-file парсинг
        for ip, filename in ip_sources:
            if ip in ip_comments:
                continue
            ip_comments[ip] = self._gossopka_comment_for_file(filename)
        return ip_comments

    def _gossopka_comment_for_file(self, filename: str) -> str:
        """Формирует коммент ГосСОПКА из имени файла. Fallback — имя без .docx."""
        if not filename:
            return ""
        base = os.path.basename(filename)
        info = self.extract_gossopka_info_from_filename(base)
        if info:
            return f"{info['org']} от {info['date']} ({info['number']})"
        stem, _ext = os.path.splitext(base)
        return stem

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

    def build_query(self, template: str, chunk: list[str], join_op: str) -> str:
        return build_query(template, chunk, join_op)

    def get_last_query_data(self) -> list[dict[str, Any]]: return self._last_query_data
    def get_last_unblock_data(self) -> dict[str, list[IOC]]: return self._last_unblock_data

    @property
    def last_unblock_data(self) -> dict[str, list[IOC]]:
        return self._last_unblock_data


def main():
    config_manager = ConfigManager("config.json")
    config = config_manager.config_data

    # Сборка DI контейнера
    doc_adapter = DocxAdapter()
    mail_adapter = ExchangeAdapter(
        email=config.get("ews_email", ""),
        username=config.get("ews_username", ""),
        server=config.get("ews_server", ""),
        password_env_var=config.get("password_env_var", "EWS_PASSWORD"),
        password_file=config.get("password_file", ""),
        outlook_folder=config.get("outlook_folder", ""),
        save_dir=config.get("save_dir", "C:\\ioc\\outlook_attachments")
    )
    export_adapter = LocalFSAdapter(
        share_path=config.get("network_share_path", "C:\\ioc\\network_share"),
        preserve_files=config.get("preserve_existing_files", True),
        ioc_config=config.get("ioc_config", []),
        uri_clean_mode=config.get("uri_clean_mode", "domain"),
    )
    
    api_url = (config.get("api_url") or "").strip()
    api_key = (config.get("api_key") or "").strip()
    if api_url and api_key:
        ip_block_adapter = IpBlockApiAdapter(api_url=api_url, api_key=api_key)
    else:
        ip_block_adapter = MockIpBlockAdapter()

    app_service = AppService(
        doc_reader=doc_adapter,
        mail_reader=mail_adapter,
        exporter=export_adapter,
        ip_block_client=ip_block_adapter,
        settings=config
    )

    controller = GuiController(app_service, config_manager)
    view = MainView(controller)
    view.run()


if __name__ == "__main__":
    main()
