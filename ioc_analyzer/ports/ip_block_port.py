"""
Порт для отправки IP-адресов на внешний сайт блокировок.
"""

import abc


class IpBlockPort(abc.ABC):
    """
    Интерфейс HTTP API сайта блокировки IP-адресов.
    """

    @abc.abstractmethod
    def block_ips(
        self, ip_comments: dict[str, str]
    ) -> tuple[bool, dict[str, dict[str, str]]]:
        """
        Отправляет IP-адреса с per-IP комментариями на API блокировок.

        Args:
            ip_comments: Словарь {ip: comment}.

        Returns:
            Кортеж (ok, per_ip). per_ip[ip] = {"status": <code>, "text": <RU>}.
        """
        pass
