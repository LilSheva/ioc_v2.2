"""
Порт для работы с почтой.
"""

import abc

from ioc_analyzer.core.models import EmailRecord


class MailPort(abc.ABC):
    """
    Интерфейс для подключения к почтовому серверу Exchange (EWS).
    """

    @abc.abstractmethod
    def fetch_unread_emails(self) -> list[EmailRecord]:
        """
        Извлекает новые (непрочитанные) сообщения.
        Скачивает вложения во временную директорию и сохраняет метаданные.

        Returns:
            Список доменных моделей EmailRecord с путями к вложениям.
        """
        pass

    @abc.abstractmethod
    def mark_as_read(self, mail_id: str) -> None:
        """
        Помечает указанное сообщение как прочитанное.

        Args:
            mail_id: Уникальный идентификатор письма на сервере.
        """
        pass
