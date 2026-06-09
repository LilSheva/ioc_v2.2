"""
Заглушка порта блокировки IP для режима без настроенного API.
"""

from ioc_analyzer.ports.ip_block_port import IpBlockPort


class MockIpBlockAdapter(IpBlockPort):
    """No-op реализация, когда сайт блокировок не настроен."""

    def block_ips(
        self, ip_comments: dict[str, str]
    ) -> tuple[bool, dict[str, dict[str, str]]]:
        return True, {}
