"""
Графический интерфейс пользователя (GUI) - Точка входа.
"""

import os
from ioc_analyzer.adapters.document.docx_adapter import DocxAdapter
from ioc_analyzer.adapters.mail.exchange_adapter import ExchangeAdapter
from ioc_analyzer.adapters.export.local_fs_adapter import LocalFSAdapter
from ioc_analyzer.adapters.ip_block.api_adapter import IpBlockApiAdapter
from ioc_analyzer.adapters.ip_block.mock_ip_block import MockIpBlockAdapter
from ioc_analyzer.adapters.gui.tkinter_gui import MainView
from ioc_analyzer.adapters.gui.gui_controller import GuiController
from ioc_analyzer.core.config_manager import ConfigManager
from ioc_analyzer.core.service import AppService


def main():
    config_manager = ConfigManager(os.path.join(".data", "config.json"))
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
        save_dir=config.get("save_dir", "C:\\ioc\\outlook_attachments"),
        ews_port=config.get("ews_port", 443),
        verify_ssl=config.get("ews_verify_ssl", True),
        enable_smime_test_mode=config.get("enable_smime_test_mode", False),
        save_msg_file=config.get("save_msg_file", False),
        preserve_existing_files=config.get("preserve_existing_files", True),
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
