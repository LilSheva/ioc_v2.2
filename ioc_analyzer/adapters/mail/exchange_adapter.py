"""
Адаптер для работы с почтой через Exchange Web Services (exchangelib).
"""

import logging
import os
import random
import string
from datetime import datetime


from exchangelib import Account, Configuration, Credentials, DELEGATE, FileAttachment
from ioc_analyzer.core.models import EmailRecord
from ioc_analyzer.ports.mail_port import MailPort

logger = logging.getLogger("ioc_analyzer.mail_adapter")


class ExchangeAdapter(MailPort):
    """
    Реализация MailPort для работы с MS Exchange через EWS.
    """

    def __init__(
        self,
        email: str,
        username: str = "",
        server: str = "",
        password_env_var: str = "EWS_PASSWORD",
        outlook_folder: str = "",
        save_dir: str = "C:\\ioc\\outlook_attachments"
    ):
        """
        Инициализация почтового адаптера.
        """
        self.email = email
        self.username = username or email
        self.server = server
        self.password_env_var = password_env_var
        self.outlook_folder = outlook_folder
        self.save_dir = save_dir

    def _get_account(self) -> Account:
        """Инициализирует и возвращает объект Account из exchangelib."""
        password = os.environ.get(self.password_env_var, "")
        if not password:
            logger.warning(f"Переменная окружения '{self.password_env_var}' для пароля EWS пуста.")

        credentials = Credentials(username=self.username, password=password)
        
        if self.server:
            config = Configuration(server=self.server, credentials=credentials)
            return Account(
                primary_smtp_address=self.email,
                config=config,
                autodiscover=False,
                access_type=DELEGATE
            )
        else:
            return Account(
                primary_smtp_address=self.email,
                credentials=credentials,
                autodiscover=True,
                access_type=DELEGATE
            )

    def fetch_unread_emails(self) -> list[EmailRecord]:
        """
        Подключается к Exchange, ищет непрочитанные сообщения, скачивает вложения.
        """
        try:
            account = self._get_account()
        except Exception as e:
            logger.error(f"Не удалось подключиться к Exchange: {e}")
            return []

        # Поиск папки
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
                        found = True
                        break

        unread_items = folder.filter(is_read=False)
        records = []

        if not os.path.exists(self.save_dir):
            os.makedirs(self.save_dir, exist_ok=True)

        for item in unread_items:
            # Создаем уникальную директорию для вложений
            rand_suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))
            time_str = datetime.now().strftime('%Y%m%d_%H%M%S')
            email_temp_dir = os.path.join(self.save_dir, f"temp_{time_str}_{rand_suffix}")
            os.makedirs(email_temp_dir, exist_ok=True)

            attachments_paths = []
            for attachment in item.attachments:
                if isinstance(attachment, FileAttachment):
                    path = os.path.join(email_temp_dir, attachment.name)
                    with open(path, 'wb') as f:
                        f.write(attachment.content)
                    attachments_paths.append(path)

            # Сохраняем текстовое тело письма
            body_text = item.text_body or ""
            body_path = os.path.join(email_temp_dir, "body.txt")
            with open(body_path, "w", encoding="utf-8") as f:
                f.write(body_text)

            mail_id = f"{item.id}:{item.changekey}"
            records.append(
                EmailRecord(
                    mail_id=mail_id,
                    subject=item.subject or "Без темы",
                    received_time=item.datetime_received.replace(tzinfo=None) if item.datetime_received else datetime.now(),
                    temp_dir=email_temp_dir,
                    attachments=attachments_paths,
                    body_text=body_text
                )
            )

        return records

    def mark_as_read(self, mail_id: str) -> None:
        """
        Помечает письмо как прочитанное.
        """
        try:
            account = self._get_account()
            item_id, change_key = mail_id.split(':', 1)
            item = account.root.get(id=item_id, changekey=change_key)
            item.is_read = True
            item.save(update_fields=['is_read'])
        except Exception as e:
            logger.error(f"Не удалось пометить письмо {mail_id} как прочитанное: {e}")
