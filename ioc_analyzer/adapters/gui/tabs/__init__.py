"""
Пакет вкладок графического интерфейса пользователя.
"""

from ioc_analyzer.adapters.gui.tabs.main_tab import MainTab
from ioc_analyzer.adapters.gui.tabs.results_tab import ResultsTab
from ioc_analyzer.adapters.gui.tabs.ip_tab import IPTab
from ioc_analyzer.adapters.gui.tabs.settings_tab import SettingsTab
from ioc_analyzer.adapters.gui.tabs.info_tab import InfoTab

__all__ = [
    "MainTab",
    "ResultsTab",
    "IPTab",
    "SettingsTab",
    "InfoTab",
]
