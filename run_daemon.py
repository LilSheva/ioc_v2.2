"""
Фоновый демон автоматической обработки бюллетеней из почты.
"""

import argparse
import json
import logging
import os
import sys
import time
from datetime import datetime

from ioc_analyzer.adapters.document.docx_adapter import DocxAdapter
from ioc_analyzer.adapters.mail.exchange_adapter import ExchangeAdapter
from ioc_analyzer.adapters.export.local_fs_adapter import LocalFSAdapter
from ioc_analyzer.adapters.ip_block.api_adapter import IpBlockApiAdapter
from ioc_analyzer.adapters.ip_block.mock_ip_block import MockIpBlockAdapter
from ioc_analyzer.core.service import AppService

# Настройка логирования в stdout и файл app.log
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("app.log", mode="a", encoding="utf-8")
    ]
)
logger = logging.getLogger("ioc_analyzer.daemon")


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="IOC Parser daemon")
    parser.add_argument(
        "-tst",
        action="store_true",
        help=(
            "Тестовый режим рабочего хоста: включить расшифровку S/MIME "
            "через Windows Certificate Store."
        ),
    )
    parser.add_argument(
        "--config",
        default="config.json",
        help="Путь к config.json (по умолчанию: ./config.json)",
    )
    return parser.parse_args()


def main():
    args = _parse_args()
    logger.info("Initializing IOC Parser Daemon...")
    config_path = args.config
    
    if not os.path.exists(config_path):
        logger.error(f"Configuration file {config_path} not found. Exiting.")
        sys.exit(1)

    try:
        with open(config_path, "r", encoding="utf-8") as f:
            config = json.load(f)
    except Exception as e:
        logger.error(f"Failed to parse configuration: {e}")
        sys.exit(1)

    if args.tst:
        logger.warning(
            "Запуск в режиме -tst: включена расшифровка S/MIME "
            "через Windows Certificate Store текущего пользователя."
        )
    else:
        logger.info(
            "Запуск без -tst: S/MIME-расшифровка отключена. "
            "Зашифрованные письма будут пропущены с ошибкой в логе."
        )

    # Инициализация адаптеров
    doc_adapter = DocxAdapter()
    
    # EWS Exchange почта
    mail_adapter = ExchangeAdapter(
        email=config.get("ews_email", ""),
        username=config.get("ews_username", ""),
        server=config.get("ews_server", ""),
        password_env_var=config.get("password_env_var", "EWS_PASSWORD"),
        password_file=config.get("password_file", ""),
        outlook_folder=config.get("outlook_folder", ""),
        save_dir=config.get("save_dir", "C:\\ioc\\outlook_attachments"),
        ews_port=config.get("ews_port", 443),
        verify_ssl=config.get("ews_verify_ssl", True),
        enable_smime_test_mode=args.tst,
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
        logger.info("API сайта блокировки IP не настроен. Автоотправка отключена.")
        ip_block_adapter = MockIpBlockAdapter()

    app_service = AppService(
        doc_reader=doc_adapter,
        mail_reader=mail_adapter,
        exporter=export_adapter,
        ip_block_client=ip_block_adapter,
        settings=config
    )

    interval = config.get("daemon_interval_seconds", 300)
    logger.info(f"Daemon started. Checking mailbox every {interval} seconds. Press Ctrl+C to stop.")

    try:
        while True:
            try:
                processed = app_service.process_mailbox(logger.info)
                if processed > 0:
                    logger.info(f"Successfully processed {processed} email bulletins.")
            except Exception as e:
                logger.error(f"Error during mailbox processing cycle: {e}")
            
            time.sleep(interval)
    except KeyboardInterrupt:
        logger.info("Daemon stopped by user.")


if __name__ == "__main__":
    main()
