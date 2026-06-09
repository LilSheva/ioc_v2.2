"""
Порт для интеграции с системами SIEM/NAD.
"""

import abc

from ioc_analyzer.core.models import IOC


class SiemPort(abc.ABC):
    """
    Интерфейс для отправки индикаторов в систему мониторинга.
    """

    @abc.abstractmethod
    def push_indicators(self, indicators: list[IOC]) -> bool:
        """
        Отправляет список найденных индикаторов в API SIEM/NAD.

        Args:
            indicators: Список моделей IOC для блокировки/поиска.

        Returns:
            True в случае успешной отправки, иначе False.
        """
        pass
