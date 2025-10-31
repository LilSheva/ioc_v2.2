"""
Модуль для управления конфигурацией IOC парсера V2.
Поддержка множественных шаблонов и расширенных статусов.
"""

import json
import os
from typing import List, Dict, Any


class ConfigManager:
    """Менеджер конфигурации приложения V2."""
    
    DEFAULT_CONFIG = [
        {
            "enabled": True,
            "name": "IP",
            "regex": r"(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)(?:\[\.\]|\.)){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)",
            "report_type": "IP-адрес",
            "nta_status": "",
            "siem_tools_status": "---------------",
            "siem_status": "",
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
            "mp10_templates": [
                "event_src.fqdn = \"{ioc}.\"",
                "object.fullpath = \"{ioc}.\"",
                "object.name = \"{ioc}.\"",
                "subject.account.domain = \"{ioc}.\""
            ],
            "nad_templates": [
                "src.dns ~ \"{ioc}.\"",
                "dst.dns ~ \"{ioc}.\"",
                "http.rqs.url ~ \"{ioc}.\"",
                "dns.query.rrname ~ \"{ioc}.\""
            ]
        },
        {
            "enabled": True,
            "name": "URI",
            "regex": r"(?:https?|hxxps?|ftps?|mtls?)(?:\[:\]|:)//[^\s<>\"]+",
            "report_type": "URI",
            "nta_status": "",
            "siem_tools_status": "---------------",
            "siem_status": "---------------",
            "mp10_templates": [],
            "nad_templates": []
        },
        {
            "enabled": True,
            "name": "SHA256",
            "regex": r"\b[a-fA-F0-9]{64}\b",
            "report_type": "SHA256",
            "nta_status": "---------------",
            "siem_tools_status": "---------------",
            "siem_status": "",
            "mp10_templates": [
                "object.hash.sha256 = \"{ioc}\""
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
            "mp10_templates": [
                "object.hash.sha1 = \"{ioc}\""
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
            "mp10_templates": [
                "object.hash.md5 = \"{ioc}\""
            ],
            "nad_templates": []
        },
        {
            "enabled": True,
            "name": "File",
            "regex": r'(?:\"|\«|файл с наименованием \")([^\"\«\»]+?)(?:\"|\»)',
            "report_type": "File",
            "nta_status": "",
            "siem_tools_status": "---------------",
            "siem_status": "",
            "mp10_templates": [
                "object.name CONTAINS \"{ioc}\"",
                "object.path CONTAINS \"{ioc}\"",
                "object.fullpath = \"{ioc}\""
            ],
            "nad_templates": [
                "files.filename ~ \"{ioc}\"",
                "files.mime ~ \"{ioc}\""
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
            "mp10_templates": [],
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
            "mp10_templates": [],
            "nad_templates": []
        }
    ]
    
    def __init__(self, config_path: str = "config.txt"):
        """Инициализация менеджера конфигурации."""
        self.config_path = config_path
        self.config_data: List[Dict[str, Any]] = []
        self._load_or_create_config()
    
    def _load_or_create_config(self) -> None:
        """Загружает конфигурацию из файла или создает новую."""
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    self.config_data = json.load(f)
                if not self._validate_config():
                    print(f"Ошибка валидации конфига. Создание нового...")
                    self._create_default_config()
            except Exception as e:
                print(f"Ошибка загрузки конфига: {e}. Создание нового...")
                self._create_default_config()
        else:
            self._create_default_config()
    
    def _validate_config(self) -> bool:
        """Валидация структуры конфигурации."""
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
    
    def _create_default_config(self) -> None:
        """Создает конфигурацию по умолчанию."""
        self.config_data = [item.copy() for item in self.DEFAULT_CONFIG]
        self.save_config()
    
    def save_config(self) -> bool:
        """Сохраняет текущую конфигурацию в файл."""
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self.config_data, f, ensure_ascii=False, indent=4)
            return True
        except Exception as e:
            print(f"Ошибка сохранения конфига: {e}")
            return False
    
    def get_config(self) -> List[Dict[str, Any]]:
        """Возвращает текущую конфигурацию."""
        return self.config_data
    
    def get_enabled_iocs(self) -> List[Dict[str, Any]]:
        """Возвращает только включенные IOC."""
        return [ioc for ioc in self.config_data if ioc.get('enabled', False)]
    
    def update_ioc(self, index: int, updated_data: Dict[str, Any]) -> bool:
        """Обновляет настройки IOC по индексу."""
        if 0 <= index < len(self.config_data):
            self.config_data[index].update(updated_data)
            return True
        return False
    
    def move_ioc(self, index: int, direction: int) -> bool:
        """Перемещает IOC вверх или вниз."""
        new_index = index + direction
        if 0 <= new_index < len(self.config_data):
            self.config_data[index], self.config_data[new_index] = \
                self.config_data[new_index], self.config_data[index]
            return True
        return False
