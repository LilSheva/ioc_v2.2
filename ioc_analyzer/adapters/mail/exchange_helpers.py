"""
EWS helper functions to reduce exchange_adapter.py line count.
"""

import logging
import os
from exchangelib import Credentials, Configuration, FileAttachment, ItemAttachment
from exchangelib.protocol import BaseProtocol, NoVerifyHTTPAdapter
from ioc_analyzer.adapters.mail.smime_tst import extract_smime_attachments, is_smime_filename

logger = logging.getLogger("ioc_analyzer.mail_adapter")

def normalize_ews_server(server: str) -> tuple[str, int | None]:
    host = (server or "").strip()
    if host.lower().startswith("https://"):
        host = host[8:]
    elif host.lower().startswith("http://"):
        host = host[7:]
    host = host.strip("/")
    explicit_port: int | None = None
    if ":" in host:
        hostname, _, port_part = host.rpartition(":")
        if port_part.isdigit():
            host = hostname
            explicit_port = int(port_part)
    return host, explicit_port


def configure_ssl_verification(verify_ssl: bool) -> None:
    if verify_ssl:
        return
    BaseProtocol.HTTP_ADAPTER_CLS = NoVerifyHTTPAdapter
    try:
        import urllib3
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    except Exception as e:
        logger.debug("Не удалось отключить предупреждения urllib3: %s", e)
    logger.warning(
        "Проверка SSL-сертификата EWS отключена (ews_verify_ssl=false). "
        "Используйте только в доверенной корпоративной сети."
    )


def build_configuration(host: str, port: int, credentials: Credentials) -> Configuration:
    if port != 443:
        endpoint = f"https://{host}:{port}/EWS/Exchange.asmx"
        return Configuration(service_endpoint=endpoint, credentials=credentials)
    return Configuration(server=host, credentials=credentials)


def save_file_attachment(
    attachment: FileAttachment, dest_dir: str, preserve_existing_files: bool = True
) -> str | None:
    name = (attachment.name or "attachment.bin").strip() or "attachment.bin"
    path = os.path.join(dest_dir, name)
    if preserve_existing_files and os.path.exists(path):
        logger.warning("Пропуск сохранения вложения (файл уже существует): %s", path)
        return path

    try:
        if attachment.content is None:
            attachment.load()
    except Exception as e:
        logger.warning("Не удалось загрузить вложение %s: %s", attachment.name, e)
        return None
    try:
        with open(path, "wb") as f:
            f.write(attachment.content or b"")
    except OSError as e:
        logger.warning("Не удалось сохранить вложение %s: %s", name, e)
        return None
    return path


def harvest_attachments(
    item,
    dest_dir: str,
    paths: list[str],
    enable_smime_test_mode: bool,
    preserve_existing_files: bool = True,
    saved_names: set[str] = None,
) -> None:
    attachments = getattr(item, "attachments", None)
    if not attachments:
        return
    if saved_names is None:
        saved_names = set()

    for attachment in attachments:
        if isinstance(attachment, FileAttachment):
            name = (attachment.name or "").strip()
            if not name:
                name = "attachment.bin"
            if name in saved_names:
                logger.error(
                    "КОЛЛИЗИЯ: В письме с темой '%s' найдено дублирующееся вложение с именем '%s'.",
                    getattr(item, "subject", "Без темы"), name
                )
            saved_names.add(name)

            saved = save_file_attachment(attachment, dest_dir, preserve_existing_files)
            if not saved:
                continue
            if is_smime_filename(name):
                try:
                    if not enable_smime_test_mode:
                        logger.error(
                            "Получено зашифрованное письмо (%s), но режим -tst выключен. "
                            "В production расшифровка отключена, письмо пропускается.",
                            name or "smime.p7m",
                        )
                        continue
                    logger.info("smime.p7m обнаружен — расшифровываем через Windows Certificate Store...")
                    with open(saved, "rb") as f:
                        raw = f.read()
                    extracted = extract_smime_attachments(raw, dest_dir, logger)
                    if extracted:
                        paths.extend(extracted)
                        logger.info("smime.p7m успешно расшифрован, вложения извлечены.")
                    else:
                        logger.warning("smime.p7m расшифрован, но вложений не найдено.")
                except Exception as e:
                    logger.warning("Ошибка обработки smime.p7m: %s", e)
                finally:
                    try:
                        os.unlink(saved)
                    except OSError as e:
                        logger.debug("Не удалось удалить временный smime-файл: %s", e)
                continue
            paths.append(saved)
            continue
        if isinstance(attachment, ItemAttachment):
            sub_item = attachment.item
            if sub_item is None:
                try:
                    attachment.load()
                    sub_item = attachment.item
                except Exception as e:
                    logger.warning("Не удалось разобрать вложенное письмо: %s", e)
                    continue
            if sub_item is not None:
                harvest_attachments(
                    sub_item,
                    dest_dir,
                    paths,
                    enable_smime_test_mode,
                    preserve_existing_files,
                    saved_names
                )
