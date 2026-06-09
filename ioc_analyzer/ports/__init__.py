"""
Пакет портов (интерфейсов) приложения.
"""

from ioc_analyzer.ports.document_port import DocumentPort, ParagraphData
from ioc_analyzer.ports.mail_port import MailPort
from ioc_analyzer.ports.export_port import ExportPort
from ioc_analyzer.ports.ip_block_port import IpBlockPort
from ioc_analyzer.ports.siem_port import SiemPort

__all__ = [
    "DocumentPort",
    "ParagraphData",
    "MailPort",
    "ExportPort",
    "IpBlockPort",
    "SiemPort",
]
