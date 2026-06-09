"""
Адаптер отправки IP-адресов на внешний сайт блокировок (requests).

Логика перенесена из legacy api_sender.py: без stdout, per-IP статусы для GUI.
"""

import logging

import requests

from ioc_analyzer.ports.ip_block_port import IpBlockPort

logger = logging.getLogger("ioc_analyzer.ip_block_api")

_STATUS_TEXT_RU = {
    "OK": "Успешно",
    "ERROR_DUPLICATE": "Уже заблокировано",
    "ERROR_DENY_NET": "Запрещённая сеть",
    "ERROR_FORMAT": "Ошибка формата",
    "ERROR_INVALID": "Ошибка формата",
}


def _humanize(status: str, text: str) -> str:
    if status in _STATUS_TEXT_RU:
        return _STATUS_TEXT_RU[status]
    if text:
        return f"Ошибка: {text}"
    if status:
        return f"Ошибка: {status}"
    return "Ошибка"


def _build_per_ip(ip_list: list[str], results) -> dict[str, dict[str, str]]:
    if not isinstance(results, list):
        return {
            ip: {"status": "BAD_RESPONSE", "text": "Неожиданный ответ сервера"}
            for ip in ip_list
        }

    by_ip: dict[str, dict[str, str]] = {}
    for item in results:
        if not isinstance(item, dict):
            continue
        ip = item.get("id") or item.get("ip")
        if not ip:
            continue
        status = item.get("status", "")
        text = item.get("text", "")
        by_ip[ip] = {"status": status, "text": _humanize(status, text)}

    for ip in ip_list:
        if ip not in by_ip:
            by_ip[ip] = {"status": "NO_RESPONSE", "text": "Нет ответа от сервера"}
    return by_ip


def send_to_api(
    ip_comments: dict[str, str],
    api_url: str,
    api_key: str,
) -> tuple[bool, dict[str, dict[str, str]]]:
    """
    Отправляет IP-адреса в API сайта блокировок с per-IP комментариями.
    """
    if not ip_comments:
        return True, {}

    ip_list = list(ip_comments.keys())
    payload = [{"ip": ip, "comment": comment} for ip, comment in ip_comments.items()]

    try:
        response = requests.post(
            api_url,
            json=payload,
            headers={"X-API-KEY": api_key},
            timeout=30,
        )
        response.raise_for_status()
        results = response.json()
    except requests.ConnectionError:
        return False, {
            ip: {"status": "NETWORK_ERROR", "text": "Ошибка соединения"} for ip in ip_list
        }
    except requests.Timeout:
        return False, {ip: {"status": "TIMEOUT", "text": "Таймаут"} for ip in ip_list}
    except requests.HTTPError as e:
        code = getattr(getattr(e, "response", None), "status_code", "?")
        return False, {ip: {"status": "HTTP_ERROR", "text": f"HTTP {code}"} for ip in ip_list}
    except Exception as e:
        return False, {
            ip: {"status": "UNEXPECTED", "text": f"Ошибка: {e.__class__.__name__}"}
            for ip in ip_list
        }

    return True, _build_per_ip(ip_list, results)


class IpBlockApiAdapter(IpBlockPort):
    """Реализация IpBlockPort для HTTP API сайта блокировки IP."""

    def __init__(self, api_url: str, api_key: str = ""):
        self.api_url = api_url
        self.api_key = api_key

    def block_ips(
        self, ip_comments: dict[str, str]
    ) -> tuple[bool, dict[str, dict[str, str]]]:
        if not ip_comments:
            return True, {}
        if not self.api_url:
            logger.warning("URL API блокировки IP не задан. Отправка отменена.")
            return False, {}
        return send_to_api(ip_comments, self.api_url, self.api_key)
