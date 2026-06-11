"""
Модуль для обработки писем с вложениями из почтового ящика Exchange.
"""

import logging
import os
from typing import Any, Callable, Optional

from ioc_analyzer.core.folder_naming import build_mailbox_folder_name
from ioc_analyzer.core.mailbox_layout import collect_docx_text_bundle, copy_attachments_to_task
from ioc_analyzer.core.parser.mode_detect import detect_mailbox_parser_mode

logger = logging.getLogger("ioc_analyzer.mailbox_processor")


class MailboxProcessor:
    """
    Класс для обработки папки входящих писем и извлечения вложений.
    """

    def __init__(self, service: Any):
        """
        Инициализация процессора со ссылкой на оркестратор AppService.
        """
        self.service = service

    def process_mailbox(self, log_callback: Optional[Callable[[str], None]] = None) -> int:
        """
        Скачивает новые бюллетени по почте, обрабатывает их и сохраняет на сетевую шару.

        Returns:
            Количество успешно обработанных писем с бюллетенями.
        """
        def log(msg: str):
            logger.info(msg)
            if log_callback:
                log_callback(msg)

        log("Checking Exchange mailbox for new bulletins...")
        emails = self.service.mail_reader.fetch_unread_emails()
        if not emails:
            log("No new unread messages.")
            return 0

        log(f"Found {len(emails)} unread emails.")
        processed_count = 0

        share_path = (self.service.settings.get("network_share_path") or "").strip()
        if not share_path:
            log("❌ В config.json не задан network_share_path.")
            return 0
        os.makedirs(share_path, exist_ok=True)

        for email in emails:
            log(f"Processing email: '{email.subject}' received at {email.received_time}")

            if not email.attachments:
                log("⚠ Письмо без вложений. Пропуск без пометки прочитанным.")
                continue

            names = ", ".join(os.path.basename(p) for p in email.attachments)
            log(f"   Вложения ({len(email.attachments)}): {names}")

            mode, mode_error = detect_mailbox_parser_mode(
                email.attachments, self.service.doc_reader
            )
            if mode_error or not mode:
                log(f"❌ {mode_error}")
                continue

            log(f"   Режим парсинга для письма: {mode}")

            docx_sources = [a for a in email.attachments if a.lower().endswith(".docx")]
            if not docx_sources:
                log("⚠ Нет .docx для парсинга. Пропуск без пометки прочитанным.")
                continue

            doc_text, metadata_num = collect_docx_text_bundle(
                docx_sources,
                self.service.doc_reader,
                self.service.settings.get("ioc_config", []),
            )
            first_docx_name = os.path.basename(docx_sources[0])
            folder_name = build_mailbox_folder_name(
                mode,
                received_time=email.received_time,
                doc_text=doc_text,
                first_docx_name=first_docx_name,
                metadata_num=metadata_num,
            )

            layout = self.service.exporter.setup_mailbox_layout(folder_name)
            log(f"   📁 {layout.root}")

            preserve = self.service.settings.get("preserve_existing_files", True)
            docx_in_task = copy_attachments_to_task(
                email.attachments, email.temp_dir, layout.task, preserve
            )
            if not docx_in_task:
                log("❌ Не удалось подготовить .docx в «Задача».")
                continue

            success, _, _ = self.service.process_local_files(
                file_paths=docx_in_task,
                dest_dir=layout.report,
                mode=mode,
                uri_clean_mode=self.service.settings.get("uri_clean_mode", "domain"),
                templates_dir=layout.templates,
                log_callback=log_callback,
            )

            if success:
                self.service.mail_reader.mark_as_read(email.mail_id)
                processed_count += 1
                log(f"✓ Письмо '{email.subject}' обработано.")
            else:
                log(f"❌ Ошибка обработки письма '{email.subject}'.")

        return processed_count
