"""
Модуль для управления конфигурацией (config.json) в ядре.
"""

import copy
import json
import logging
import os
from typing import Any

logger = logging.getLogger("ioc_analyzer.config_manager")

DEFAULT_IOC_CONFIG = [
    {
        "enabled": True,
        "name": "IP",
        "report_type": "IP-адрес",
        "nta_status": "",
        "siem_tools_status": "---------------",
        "siem_status": "",
        "mp10_templates": ["src.ip = \"{ioc}\"", "dst.ip = \"{ioc}\""],
        "nad_templates": ["src.ip == \"{ioc}\"", "dst.ip == \"{ioc}\"", "host.ip == \"{ioc}\""],
        "blacklist": [],
        "exclusions": []
    },
    {
        "enabled": True,
        "name": "DNS",
        "report_type": "Домен",
        "nta_status": "",
        "siem_tools_status": "---------------",
        "siem_status": "---------------",
        "mp10_templates": [
            "event_src.fqdn = \"{ioc}\"", "object.fullpath = \"{ioc}\"",
            "object.name = \"{ioc}\"", "subject.account.domain = \"{ioc}\""
        ],
        "nad_templates": [
            "src.dns ~ \"{ioc}\"", "dst.dns ~ \"{ioc}\"",
            "http.rqs.url ~ \"{ioc}\"", "dns.query.rrname ~ \"{ioc}\""
        ],
        "blacklist": [],
        "exclusions": []
    },
    {
        "enabled": True,
        "name": "URI",
        "report_type": "URI",
        "nta_status": "",
        "siem_tools_status": "---------------",
        "siem_status": "---------------",
        "mp10_templates": [],
        "nad_templates": [],
        "blacklist": [],
        "exclusions": []
    },
    {
        "enabled": True,
        "name": "File",
        "report_type": "File",
        "nta_status": "",
        "siem_tools_status": "---------------",
        "siem_status": "",
        "file_blacklist": ["тематикой", "домена"],
        "filename_exclusions": ["1.docx"],
        "mp10_templates": ["object.name CONTAINS \"{ioc}\"", "object.path CONTAINS \"{ioc}\"", "object.fullpath = \"{ioc}\""],
        "nad_templates": ["files.filename ~ \"{ioc}\"", "files.mime ~ \"{ioc}\""]
    },
    {
        "enabled": True,
        "name": "Email",
        "report_type": "Email",
        "nta_status": "",
        "siem_tools_status": "---------------",
        "siem_status": "",
        "mp10_templates": ["subject.account.contact CONTAINS \"{ioc}\"", "object.fullpath = \"{ioc}\""],
        "nad_templates": ["mail.from == \"{ioc}\"", "mail.recipient == \"{ioc}\""],
        "blacklist": [],
        "exclusions": []
    },
    {
        "enabled": True,
        "name": "SHA256",
        "report_type": "SHA256",
        "nta_status": "---------------",
        "siem_tools_status": "---------------",
        "siem_status": "",
        "mp10_templates": ["object.hash.sha256 = \"{ioc}\""],
        "nad_templates": [],
        "blacklist": [],
        "exclusions": []
    },
    {
        "enabled": True,
        "name": "MD5",
        "report_type": "MD5",
        "nta_status": "",
        "siem_tools_status": "---------------",
        "siem_status": "",
        "mp10_templates": ["object.hash.md5 = \"{ioc}\""],
        "nad_templates": [],
        "blacklist": [],
        "exclusions": []
    },
    {
        "enabled": True,
        "name": "SHA1",
        "report_type": "SHA1",
        "nta_status": "---------------",
        "siem_tools_status": "---------------",
        "siem_status": "",
        "mp10_templates": ["object.hash.sha1 = \"{ioc}\""],
        "nad_templates": [],
        "blacklist": [],
        "exclusions": []
    },
    {
        "enabled": True,
        "name": "Registry",
        "report_type": "Registry",
        "nta_status": "",
        "siem_tools_status": "---------------",
        "siem_status": "",
        "mp10_templates": [],
        "nad_templates": [],
        "blacklist": [],
        "exclusions": []
    }
]


class ConfigManager:
    """Менеджер конфигурации config.json."""

    def __init__(self, config_path: str):
        self.config_path = config_path
        self.config_data: dict[str, Any] = {}
        self.load()

    def load(self) -> None:
        """Загружает файл конфигурации."""
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    self.config_data = json.load(f)
            except (json.JSONDecodeError, OSError) as e:
                logger.error("Ошибка при чтении файла конфигурации %s: %s", self.config_path, e)
                self.config_data = {}
        
        if "ioc_config" not in self.config_data:
            self.config_data["ioc_config"] = copy.deepcopy(DEFAULT_IOC_CONFIG)

    def save(self) -> bool:
        """Сохраняет настройки в файл."""
        try:
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(self.config_data, f, indent=4, ensure_ascii=False)
            return True
        except OSError as e:
            logger.error("Ошибка при записи файла конфигурации %s: %s", self.config_path, e)
            return False

    def get_ioc_config(self) -> list[dict[str, Any]]:
        return self.config_data.get("ioc_config", [])

    def set_ioc_config(self, ioc_config: list[dict[str, Any]]) -> bool:
        self.config_data["ioc_config"] = ioc_config
        return self.save()

    def reset_single(self, index: int) -> bool:
        """Сбросить конфигурацию конкретного IOC к дефолтной."""
        ioc_config = self.get_ioc_config()
        if not (0 <= index < len(ioc_config)):
            return False
        
        name = ioc_config[index]["name"]
        default_item = next((item for item in DEFAULT_IOC_CONFIG if item["name"] == name), None)
        if default_item:
            ioc_config[index] = copy.deepcopy(default_item)
            return self.save()
        return False

    def reset_all(self) -> bool:
        """Сбросить всю конфигурацию IOC к дефолтной."""
        self.config_data["ioc_config"] = copy.deepcopy(DEFAULT_IOC_CONFIG)
        return self.save()

    def move_ioc(self, index: int, direction: int) -> bool:
        """Смещает приоритет IOC вверх (-1) или вниз (1)."""
        ioc_config = self.get_ioc_config()
        new_index = index + direction
        if not (0 <= new_index < len(ioc_config)):
            return False

        ioc_config[index], ioc_config[new_index] = ioc_config[new_index], ioc_config[index]
        return self.save()
