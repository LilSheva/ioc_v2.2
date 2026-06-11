"""Адаптер для работы с почтой через Exchange Web Services (exchangelib)."""

import logging
import os
import random
import string
from datetime import datetime

from exchangelib import Account, Credentials, DELEGATE

from ioc_analyzer.adapters.mail.exchange_helpers import (
    normalize_ews_server,
    configure_ssl_verification,
    build_configuration,
    harvest_attachments,
)
from ioc_analyzer.core.credentials import resolve_secret
from ioc_analyzer.core.models import EmailRecord
from ioc_analyzer.ports.mail_port import MailPort

logger = logging.getLogger("ioc_analyzer.mail_adapter")


class ExchangeAdapter(MailPort):
    def __init__(
        self,
        email: str,
        username: str = "",
        server: str = "",
        password_env_var: str = "EWS_PASSWORD",
        password_file: str = "",
        outlook_folder: str = "",
        save_dir: str = "C:\\ioc\\outlook_attachments",
        ews_port: int = 443,
        verify_ssl: bool = True,
        enable_smime_test_mode: bool = False,
        save_msg_file: bool = False,
        preserve_existing_files: bool = True,
    ):
        self.email = email
        self.username = username or email
        self.server, port_in_host = normalize_ews_server(server)
        self.ews_port = port_in_host or int(ews_port or 443)
        self.verify_ssl = verify_ssl
        self.password_env_var = password_env_var
        self.password_file = password_file
        self.outlook_folder = outlook_folder
        self.save_dir = save_dir
        self.enable_smime_test_mode = bool(enable_smime_test_mode)
        self.save_msg_file = save_msg_file
        self.preserve_existing_files = preserve_existing_files
        configure_ssl_verification(self.verify_ssl)

    def _get_account(self) -> Account:
        password = resolve_secret(self.password_file, self.password_env_var)
        credentials = Credentials(username=self.username, password=password)
        if self.server:
            config = build_configuration(self.server, self.ews_port, credentials)
            return Account(
                primary_smtp_address=self.email,
                config=config,
                autodiscover=False,
                access_type=DELEGATE,
            )
        return Account(
            primary_smtp_address=self.email,
            credentials=credentials,
            autodiscover=True,
            access_type=DELEGATE,
        )

    def fetch_unread_emails(self) -> list[EmailRecord]:
        try:
            account = self._get_account()
        except Exception as e:
            logger.error("Не удалось подключиться к Exchange: %s", e)
            return []
        folder = account.inbox
        if self.outlook_folder:
            found = False
            for f in account.inbox.walk():
                if f.name.lower() == self.outlook_folder.lower():
                    folder = f
                    found = True
                    break
            if not found:
                for f in account.root.walk():
                    if f.name.lower() == self.outlook_folder.lower():
                        folder = f
                        break
        unread_items = folder.filter(is_read=False)
        records: list[EmailRecord] = []
        os.makedirs(self.save_dir, exist_ok=True)
        for item in unread_items:
            rand_suffix = "".join(random.choices(string.ascii_lowercase + string.digits, k=6))
            time_str = datetime.now().strftime("%Y%m%d_%H%M%S")
            email_temp_dir = os.path.join(self.save_dir, f"temp_{time_str}_{rand_suffix}")
            os.makedirs(email_temp_dir, exist_ok=True)
            attachments_paths: list[str] = []
            harvest_attachments(
                item,
                email_temp_dir,
                attachments_paths,
                self.enable_smime_test_mode,
                self.preserve_existing_files
            )
            if not attachments_paths:
                logger.warning(
                    "Письмо '%s': вложения не скачаны (возможно, неподдерживаемый тип).",
                    item.subject or "",
                )
            body_text = item.text_body or ""
            with open(os.path.join(email_temp_dir, "body.txt"), "w", encoding="utf-8") as f:
                f.write(body_text)

            # Сохранение оригинального сообщения в формате .eml (MIME RFC 822)
            if self.save_msg_file:
                try:
                    mime = item.mime_content
                    if mime:
                        with open(os.path.join(email_temp_dir, "message.eml"), "wb") as f:
                            f.write(mime)
                        logger.info("Сохранено оригинальное письмо в формате .eml для '%s'", item.subject or "")
                except Exception as e:
                    logger.warning("Не удалось сохранить оригинальное письмо в формате .eml: %s", e)

            mail_id = f"{item.id}:{item.changekey}"
            records.append(
                EmailRecord(
                    mail_id=mail_id,
                    subject=item.subject or "Без темы",
                    received_time=item.datetime_received.replace(tzinfo=None) if item.datetime_received else datetime.now(),
                    temp_dir=email_temp_dir,
                    attachments=attachments_paths,
                    body_text=body_text,
                )
            )
        return records

    def mark_as_read(self, mail_id: str) -> None:
        try:
            account = self._get_account()
            item_id, change_key = mail_id.split(":", 1)
            item = account.root.get(id=item_id, changekey=change_key)
            item.is_read = True
            item.save(update_fields=["is_read"])
        except Exception as e:
            logger.error("Не удалось пометить письмо %s как прочитанное: %s", mail_id, e)
