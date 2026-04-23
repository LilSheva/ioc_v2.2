"""Модуль отправки IP-адресов в API системы блокировок.

Важно: приложение собирается в безконсольный .exe — модуль НЕ пишет в stdout.
Все результаты возвращаются наверх в структурированном виде для показа в UI.
"""

import requests


# Человеко-читаемые тексты для известных статусов API.
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


def send_to_api(
    ip_comments: dict,
    api_url: str,
    api_key: str,
) -> tuple:
    """
    Отправляет IP-адреса в API системы блокировок с per-IP комментариями.

    Args:
        ip_comments: dict {ip: comment} — у каждого IP свой источник/коммент.
        api_url:     URL эндпоинта API.
        api_key:     API-ключ (заголовок X-API-KEY).

    Returns:
        Кортеж (ok: bool, per_ip: dict[str, dict]).
        per_ip[ip] = {"status": <code>, "text": <human-readable RU>}.
        ok=True если HTTP-запрос выполнен успешно (отдельные IP могут иметь ошибки);
        ok=False при сетевой ошибке/таймауте/HTTP-ошибке — тогда у всех IP общий статус ошибки.
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
        return False, {ip: {"status": "NETWORK_ERROR", "text": "Ошибка соединения"} for ip in ip_list}
    except requests.Timeout:
        return False, {ip: {"status": "TIMEOUT", "text": "Таймаут"} for ip in ip_list}
    except requests.HTTPError as e:
        code = getattr(getattr(e, "response", None), "status_code", "?")
        return False, {ip: {"status": "HTTP_ERROR", "text": f"HTTP {code}"} for ip in ip_list}
    except Exception as e:
        return False, {ip: {"status": "UNEXPECTED", "text": f"Ошибка: {e.__class__.__name__}"} for ip in ip_list}

    per_ip = _build_per_ip(ip_list, results)
    return True, per_ip


def _build_per_ip(ip_list: list, results) -> dict:
    """Маппит ответ API в per-IP словарь с человеко-читаемыми статусами.

    API возвращает список элементов вида {"id": <ip>, "status": <code>, "text": <msg>}.
    Если формат неожиданный — все IP получают статус 'BAD_RESPONSE'.
    """
    if not isinstance(results, list):
        return {ip: {"status": "BAD_RESPONSE", "text": "Неожиданный ответ сервера"} for ip in ip_list}

    by_ip = {}
    for item in results:
        if not isinstance(item, dict):
            continue
        ip = item.get("id") or item.get("ip")
        if not ip:
            continue
        status = item.get("status", "")
        text = item.get("text", "")
        by_ip[ip] = {"status": status, "text": _humanize(status, text)}

    # IP, по которым сервер не вернул ничего — помечаем явно.
    for ip in ip_list:
        if ip not in by_ip:
            by_ip[ip] = {"status": "NO_RESPONSE", "text": "Нет ответа от сервера"}

    return by_ip
