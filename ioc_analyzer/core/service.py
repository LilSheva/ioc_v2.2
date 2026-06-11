"""
Сервис координации бизнес-логики (Оркестратор).
"""

import logging
from datetime import datetime
from typing import Any, Callable, Optional, Tuple

from ioc_analyzer.core.constants import DEFAULT_FSTEC_EVENT_TYPE, PARSER_MODE_AUTO
from ioc_analyzer.core.models import IOC, ReportData
from ioc_analyzer.core.parser import IOCParser
from ioc_analyzer.core.parser.cleaner import deduplicate_iocs
from ioc_analyzer.ports.document_port import DocumentPort
from ioc_analyzer.ports.mail_port import MailPort
from ioc_analyzer.ports.export_port import ExportPort
from ioc_analyzer.ports.ip_block_port import IpBlockPort

logger = logging.getLogger("ioc_analyzer.service")


class AppService:
    """
    Класс сервиса для запуска процессов обработки бюллетеней.
    """

    def __init__(
        self,
        doc_reader: DocumentPort,
        mail_reader: MailPort,
        exporter: ExportPort,
        ip_block_client: IpBlockPort,
        settings: dict[str, Any]
    ):
        """
        Инициализация сервиса с внедрением зависимостей портов.
        """
        self.doc_reader = doc_reader
        self.mail_reader = mail_reader
        self.exporter = exporter
        self.ip_block_client = ip_block_client
        self.settings = settings

    def process_local_files(
        self,
        file_paths: list[str],
        dest_dir: str,
        mode: str = PARSER_MODE_AUTO,
        uri_clean_mode: str = "domain",
        templates_dir: str | None = None,
        log_callback: Optional[Callable[[str], None]] = None,
    ) -> Tuple[bool, dict[str, list[IOC]], list[Tuple[str, str]]]:
        """
        Выполняет ручную обработку локальных документов и сохраняет результаты.

        Returns:
            Кортеж (успех, словарь_найденных_IOC_по_типам, список_найденных_BDU)
        """
        def log(msg: str):
            logger.info(msg)
            if log_callback:
                log_callback(msg)

        log(f"Starting processing of {len(file_paths)} files in mode '{mode}'")
        parser = IOCParser(
            self.settings.get("ioc_config", []),
            mode=mode,
            document_reader=self.doc_reader
        )

        # Парсим IOC
        raw_parsed = parser.parse(file_paths)
        
        # Преобразуем во внутренние модели IOC
        ioc_by_type: dict[str, list[IOC]] = {}
        unblock_ips: list[tuple[str, str]] = []

        for ioc_type, items in raw_parsed.items():
            ioc_by_type[ioc_type] = []
            for original, cleaned, meta in items:
                status = meta.get("status", "block")
                file_mode = meta.get("parser_mode", mode)
                if status == "unblock" and file_mode == "gossopka":
                    unblock_ips.append((cleaned, meta.get("filename", "")))
                    log(f"   🔓 [РАЗБЛОКИРОВКА] {cleaned} (файл: {meta['filename']})")
                    continue

                if file_mode == "gossopka":
                    context = meta.get("event_type") or ""
                else:
                    context = meta.get("event_type") or DEFAULT_FSTEC_EVENT_TYPE

                ioc = IOC(
                    ioc_type=ioc_type,
                    raw_value=original,
                    clean_value=cleaned,
                    status=status,
                    context=context,
                    source_file=meta.get("filename", ""),
                    parser_mode=file_mode,
                )
                ioc_by_type[ioc_type].append(ioc)

        # Дедупликация в пределах типа по ключу (clean_value, status, source_file)
        for ioc_type in ioc_by_type:
            ioc_by_type[ioc_type] = deduplicate_iocs(ioc_by_type[ioc_type])

        # Поиск BDU
        bdu_list = parser.extract_bdu_identifiers(file_paths)
        
        # Подготовка данных для экспорта
        flat_iocs = []
        for iocs in ioc_by_type.values():
            flat_iocs.extend(iocs)

        from ioc_analyzer.core.report_naming import pick_bulletin_source_filename

        ioc_sources = [ioc.source_file for iocs in ioc_by_type.values() for ioc in iocs]
        main_filename = pick_bulletin_source_filename(file_paths, mode, ioc_sources)
        report_mode = mode
        if mode == PARSER_MODE_AUTO and flat_iocs:
            report_mode = flat_iocs[0].parser_mode or "fstek"
        elif mode == PARSER_MODE_AUTO:
            report_mode = "fstek"

        report_data = ReportData(
            source_filename=main_filename,
            parser_mode=report_mode,
            parsed_at=datetime.now(),
            indicators=flat_iocs,
            bdu_list=[b for b, _ in bdu_list]
        )

        if hasattr(self.exporter, "uri_clean_mode"):
            self.exporter.uri_clean_mode = uri_clean_mode

        log(f"Exporting reports to {dest_dir}...")
        self.exporter.export_report(report_data, dest_dir, templates_dir)
        log("Report generation finished.")

        if unblock_ips and report_mode == "gossopka":
            log(f"⚠ ВНИМАНИЕ: найдено {len(unblock_ips)} IP на РАЗБЛОКИРОВКУ — требуется ручная разблокировка на портале:")
            for ip, fname in unblock_ips:
                log(f"      • {ip} (из файла {fname})")

        # Унификация комментариев блокировки IP под legacy-правила
        from ioc_analyzer.core.report_naming import bulletin_column_value
        ip_comments: dict[str, str] = {}
        for ioc in flat_iocs:
            if ioc.ioc_type != "IP":
                continue
            if report_mode == "gossopka" and ioc.status != "block":
                continue
            
            desc = bulletin_column_value(
                report_mode,
                ioc.source_file or main_filename,
                self.settings.get("fstek_bulletin", "")
            )
            ip_comments[ioc.clean_value] = desc

        if ip_comments:
            log(f"Sending {len(ip_comments)} IP addresses to block API...")
            ok, _ = self.ip_block_client.block_ips(ip_comments)
            if ok:
                log("✓ IP block API request completed.")
            else:
                log("⚠ IP block API request failed.")

        return True, ioc_by_type, bdu_list

    def process_mailbox(self, log_callback: Optional[Callable[[str], None]] = None) -> int:
        """
        Скачивает новые бюллетени по почте, обрабатывает их и сохраняет на сетевую шару.
        """
        from ioc_analyzer.core.mailbox_processor import MailboxProcessor
        processor = MailboxProcessor(self)
        return processor.process_mailbox(log_callback)
