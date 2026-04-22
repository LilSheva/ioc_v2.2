"""Модуль отправки IP-адресов в API системы блокировок."""

import requests


def send_to_api(ip_list: list, source_name: str, api_url: str, api_key: str) -> bool:
    """
    Отправляет список IP-адресов в API системы блокировок.

    Args:
        ip_list:     Список IP-строк для блокировки.
        source_name: Название источника (используется в комментарии).
        api_url:     URL эндпоинта API.
        api_key:     API-ключ (заголовок X-API-KEY).

    Returns:
        True если запрос выполнен (независимо от статусов отдельных IP),
        False при ошибке соединения или других исключениях.
    """
    if not ip_list:
        print("[i] Список IP пуст — нечего отправлять.")
        return True

    payload = [{"ip": ip, "comment": source_name} for ip in ip_list]

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
        print("[-] Ошибка: сервер блокировок недоступен.")
        return False
    except requests.Timeout:
        print("[-] Ошибка: превышено время ожидания ответа от сервера.")
        return False
    except requests.HTTPError as e:
        print(f"[-] HTTP-ошибка: {e}")
        return False
    except Exception as e:
        print(f"[-] Неожиданная ошибка при отправке: {e}")
        return False

    _print_results(results)
    return True


def _print_results(results: list) -> None:
    """Выводит читаемый лог по результатам API."""
    if not isinstance(results, list):
        print(f"[!] Неожиданный формат ответа сервера: {results}")
        return

    ok_count = 0
    for item in results:
        ip = item.get("id", "?")
        status = item.get("status", "")
        text = item.get("text", "")

        if status == "OK":
            print(f"[+] Добавлено: {ip}")
            ok_count += 1
        elif status == "ERROR_DUPLICATE":
            print(f"[i] Уже в базе: {ip}")
        elif status == "ERROR_DENY_NET":
            print(f"[!] Отклонён (внутренняя/защищённая сеть): {ip}")
        else:
            print(f"[-] Ошибка для {ip}: {text or status}")

    print(f"\n[=] Итого добавлено: {ok_count} из {len(results)}")
