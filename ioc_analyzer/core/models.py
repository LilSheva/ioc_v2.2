"""
Доменные модели данных для анализа индикаторов компрометации (IOC).
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional


@dataclass
class IOC:
    """
    Доменная модель индикатора компрометации.
    """
    ioc_type: str  # IP, DNS, URI, File, Email, MD5, SHA256, SHA1, Registry
    raw_value: str  # Значение в исходном виде из файла
    clean_value: str  # Очищенное значение для выгрузки/SIEM
    status: str = "block"  # block, search, unblock
    context: str = ""  # Текстовое окружение индикатора (для отчетов)
    source_file: str = ""  # Имя файла, из которого извлечен индикатор
    parser_mode: str = ""  # fstek / gossopka (при автоопределении на сервере)
    def __iter__(self) -> Any:
        meta = {
            "filename": self.source_file,
            "status": self.status,
            "event_type": self.context
        }
        return iter((self.raw_value, self.clean_value, meta))


@dataclass
class EmailRecord:
    """
    Модель метаданных полученного электронного письма.
    """
    mail_id: str
    subject: str
    received_time: datetime
    temp_dir: str
    attachments: list[str] = field(default_factory=list)
    body_text: str = ""


@dataclass
class ReportData:
    """
    Модель агрегированных данных парсинга для экспорта.
    """
    source_filename: str
    parser_mode: str  # fstek / gossopka
    parsed_at: datetime = field(default_factory=datetime.now)
    indicators: list[IOC] = field(default_factory=list)
    bdu_list: list[str] = field(default_factory=list)


@dataclass
class AppSettings:
    """
    Модель настроек приложения.
    """
    mode: str = "fstek"  # fstek / gossopka
    uri_clean_mode: str = "domain"  # domain / raw
    save_dir: str = "C:\\ioc\\outlook_attachments"
    network_share_path: str = "C:\\ioc\\network_share"
    event_type: str = "Фишинговая рассылка электронной почты. Вредоносные вложения"
    preserve_existing_files: bool = True
    verbose: bool = True
    password_env_var: str = "EWS_PASSWORD"
    password_file: str = ""  # путь к файлу с паролем; "-" = не использовать
    ews_email: str = ""
    ews_server: str = ""
    ews_username: str = ""
    api_url: str = ""  # URL сайта блокировки IP (POST, заголовок X-API-KEY)
    api_key: str = ""  # API-ключ сайта блокировки IP
    ioc_config: list[dict[str, Any]] = field(default_factory=list)
