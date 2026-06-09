"""
Мок-адаптер SIEM для тестирования.
"""


from ioc_analyzer.core.models import IOC
from ioc_analyzer.ports.siem_port import SiemPort


class MockSiemAdapter(SiemPort):
    """
    Мок-реализация SiemPort, сохраняющая отправленные индикаторы в памяти.
    """

    def __init__(self):
        self.pushed_indicators: list[IOC] = []

    def push_indicators(self, indicators: list[IOC]) -> bool:
        """
        Сохраняет переданные индикаторы компрометации в памяти.
        """
        self.pushed_indicators.extend(indicators)
        return True
