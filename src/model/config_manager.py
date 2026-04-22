"""
Модуль для управления конфигурацией IOC парсера V2.
Поддержка множественных шаблонов и расширенных статусов.

DEFAULT_CONFIG — единственный источник правды.
Файл на диске (ioc_parser_settings.json) создаётся ТОЛЬКО при явном сохранении.
Автоматическая миграция с config.txt.
"""

import copy
import json
import os
from typing import List, Dict, Any

from ..utils import get_application_base_path


class ConfigManager:
    """Менеджер конфигурации приложения V2."""

    STATE_FILENAME = "ioc_parser_settings.json"

    DEFAULT_API_URL = "http://localhost:8099/api/ipaddress"

    DEFAULT_CONFIG = [
        {
            "enabled": True,
            "name": "IP",
            "regex": r"(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)(?:\[\.\]|\.)){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)",
            "report_type": "IP-адрес",
            "nta_status": "",
            "siem_tools_status": "---------------",
            "siem_status": "",
            "blacklist": [],
            "exclusions": [],
            "mp10_templates": [
                "src.ip = \"{ioc}\"",
                "dst.ip = \"{ioc}\""
            ],
            "nad_templates": [
                "src.ip == \"{ioc}\"",
                "dst.ip == \"{ioc}\"",
                "host.ip == \"{ioc}\""
            ]
        },
        {
            "enabled": True,
            "name": "DNS",
            "regex": r"(?:[a-zA-Z0-9](?:[a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?(?:\[\.\]|\.)){1,}[a-zA-Z]{2,}",
            "report_type": "Домен",
            "nta_status": "",
            "siem_tools_status": "---------------",
            "siem_status": "---------------",
            "blacklist": [],
            "exclusions": [],
            "mp10_templates": [
                "event_src.fqdn = \"{ioc}\"",
                "object.fullpath = \"{ioc}\"",
                "object.name = \"{ioc}\"",
                "subject.account.domain = \"{ioc}\""
            ],
            "nad_templates": [
                "src.dns == \"{ioc}\"",
                "dst.dns == \"{ioc}\"",
                "http.rqs.url == \"{ioc}\"",
                "dns.query.rrname == \"{ioc}\""
            ]
        },
        {
            "enabled": True,
            "name": "URI",
            "regex": r"(?:\[:\]|:)//[^\s<>\"]+",
            "report_type": "URI",
            "nta_status": "",
            "siem_tools_status": "---------------",
            "siem_status": "---------------",
            "blacklist": [],
            "exclusions": [],
            "mp10_templates": [],
            "nad_templates": []
        },
        {
            "enabled": True,
            "name": "File",
            "regex": r"(?:\«)([^\«\»]+?)(?:\»)",
            "report_type": "File",
            "nta_status": "",
            "siem_tools_status": "---------------",
            "siem_status": "",
            "file_blacklist": [
                "тематикой",
                "домена"
            ],
            "filename_exclusions": [
                "1.docx"
            ],
            "mp10_templates": [
                "object.name = \"{ioc}\"",
                "object.path = \"{ioc}\"",
                "object.fullpath = \"{ioc}\""
            ],
            "nad_templates": [
                "files.filename == \"{ioc}\"",
                "files.mime == \"{ioc}\""
            ]
        },
        {
            "enabled": True,
            "name": "Email",
            "regex": r"\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b",
            "report_type": "Email",
            "nta_status": "",
            "siem_tools_status": "---------------",
            "siem_status": "",
            "blacklist": [],
            "exclusions": [],
            "mp10_templates": [
                "subject.account.contact = \"{ioc}\"",
                "object.fullpath = \"{ioc}\""
            ],
            "nad_templates": [
                "mail.from == \"{ioc}\"",
                "mail.recipient == \"{ioc}\""
            ]
        },
        {
            "enabled": True,
            "name": "SHA256",
            "regex": r"\b[a-fA-F0-9]{64}\b",
            "report_type": "SHA256",
            "nta_status": "---------------",
            "siem_tools_status": "---------------",
            "siem_status": "",
            "blacklist": [],
            "exclusions": [],
            "mp10_templates": [
                "object.hash.sha256 = \"{ioc}\""
            ],
            "nad_templates": []
        },
        {
            "enabled": True,
            "name": "MD5",
            "regex": r"\b[a-fA-F0-9]{32}\b",
            "report_type": "MD5",
            "nta_status": "",
            "siem_tools_status": "---------------",
            "siem_status": "",
            "blacklist": [],
            "exclusions": [],
            "mp10_templates": [
                "object.hash.md5 = \"{ioc}\""
            ],
            "nad_templates": []
        },
        {
            "enabled": True,
            "name": "SHA1",
            "regex": r"\b[a-fA-F0-9]{40}\b",
            "report_type": "SHA1",
            "nta_status": "---------------",
            "siem_tools_status": "---------------",
            "siem_status": "",
            "blacklist": [],
            "exclusions": [],
            "mp10_templates": [
                "object.hash.sha1 = \"{ioc}\""
            ],
            "nad_templates": []
        },
        {
            "enabled": True,
            "name": "Registry",
            "regex": r"(?:HKEY_[A-Z_]+|HKLM|HKCU|HKCR|HKU|HKCC)(?:\\[^\s\\]+)+?(?=[\s,;.!?)\]'\"`]|$)",
            "report_type": "Registry",
            "nta_status": "",
            "siem_tools_status": "---------------",
            "siem_status": "",
            "blacklist": [],
            "exclusions": [],
            "mp10_templates": [],
            "nad_templates": []
        }
    ]

    def __init__(self, state_dir: str = None):
        self.config_data: List[Dict[str, Any]] = []
        self.api_url: str = self.DEFAULT_API_URL
        self.api_key: str = ""
        self._state_path = self._resolve_state_path(state_dir)
        self._load_config()

    @staticmethod
    def _resolve_state_path(state_dir: str = None) -> str:
        if state_dir is None:
            base = get_application_base_path()
        else:
            base = state_dir
        return os.path.join(base, ConfigManager.STATE_FILENAME)

    def _load_config(self) -> None:
        """Загружает конфигурацию по fallback-цепочке:
        1. state file (ioc_parser_settings.json)
        2. config.txt рядом (миграция)
        3. DEFAULT_CONFIG (в память, без записи на диск)
        """
        if os.path.exists(self._state_path):
            try:
                with open(self._state_path, 'r', encoding='utf-8') as f:
                    raw = json.load(f)
                if isinstance(raw, dict) and 'ioc_config' in raw:
                    self.config_data = raw['ioc_config']
                    self.api_url = raw.get('api_url', self.DEFAULT_API_URL)
                    self.api_key = raw.get('api_key', '')
                elif isinstance(raw, list):
                    self.config_data = raw
                else:
                    raise ValueError("Неизвестный формат state file")
                self._migrate_ioc_fields()
                if self._validate_config():
                    return
                print("Ошибка валидации state file. Загрузка умолчаний...")
            except Exception as e:
                print(f"Ошибка загрузки state file: {e}. Загрузка умолчаний...")

        state_dir = os.path.dirname(self._state_path)
        legacy_path = os.path.join(state_dir, "config.txt")
        if os.path.exists(legacy_path):
            try:
                with open(legacy_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                if isinstance(data, list):
                    self.config_data = data
                    self._migrate_ioc_fields()
                    if self._validate_config():
                        self.save_config()
                        print(f"Миграция config.txt -> {self.STATE_FILENAME} выполнена.")
                        return
                print("config.txt не прошёл валидацию. Загрузка умолчаний...")
            except Exception as e:
                print(f"Ошибка миграции config.txt: {e}. Загрузка умолчаний...")

        self._load_defaults()

    def _migrate_ioc_fields(self) -> None:
        """Добавляет отсутствующие поля blacklist/exclusions в загруженный конфиг."""
        for item in self.config_data:
            if not isinstance(item, dict):
                continue
            if item.get('name') != 'File':
                item.setdefault('blacklist', [])
                item.setdefault('exclusions', [])

    def _load_defaults(self) -> None:
        self.config_data = copy.deepcopy(self.DEFAULT_CONFIG)
        self.api_url = self.DEFAULT_API_URL
        self.api_key = ""

    def _validate_config(self) -> bool:
        if not isinstance(self.config_data, list):
            return False

        required_fields = ['enabled', 'name', 'regex', 'report_type',
                          'nta_status', 'siem_tools_status', 'siem_status',
                          'mp10_templates', 'nad_templates']

        for item in self.config_data:
            if not isinstance(item, dict):
                return False
            for field in required_fields:
                if field not in item:
                    return False

        return True

    def save_config(self) -> bool:
        try:
            with open(self._state_path, 'w', encoding='utf-8') as f:
                json.dump(
                    {
                        "version": 1,
                        "api_url": self.api_url,
                        "api_key": self.api_key,
                        "ioc_config": self.config_data,
                    },
                    f, ensure_ascii=False, indent=4
                )
            return True
        except Exception as e:
            print(f"Ошибка сохранения конфига: {e}")
            return False

    def get_config(self) -> List[Dict[str, Any]]:
        return self.config_data

    def get_enabled_iocs(self) -> List[Dict[str, Any]]:
        return [ioc for ioc in self.config_data if ioc.get('enabled', False)]

    def update_ioc(self, index: int, updated_data: Dict[str, Any]) -> bool:
        if 0 <= index < len(self.config_data):
            self.config_data[index].update(updated_data)
            return True
        return False

    def move_ioc(self, index: int, direction: int) -> bool:
        new_index = index + direction
        if 0 <= new_index < len(self.config_data):
            self.config_data[index], self.config_data[new_index] = \
                self.config_data[new_index], self.config_data[index]
            return True
        return False

    def reset_ioc_to_default(self, index: int) -> bool:
        if not (0 <= index < len(self.config_data)):
            return False
        current_name = self.config_data[index].get('name')
        for default_item in self.DEFAULT_CONFIG:
            if default_item['name'] == current_name:
                self.config_data[index] = copy.deepcopy(default_item)
                return True
        return False

    def reset_all_to_defaults(self) -> None:
        self._load_defaults()

    @property
    def state_file_path(self) -> str:
        return self._state_path
