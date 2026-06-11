"""
Модуль для очистки и нормализации индикаторов компрометации (IOC).
"""

import ipaddress
import re
import socket
from typing import Any
from urllib.parse import urlparse


def clean_ioc(ioc: str, ioc_type: str) -> str:
    """
    Очищает IOC от маскирующих символов и лишних пробелов.

    Args:
        ioc: Исходный индикатор.
        ioc_type: Тип индикатора (IP, DNS, URI, File, и т.д.).

    Returns:
        Очищенная строка индикатора.
    """
    cleaned = ioc.strip()

    if ioc_type == 'File':
        cleaned = re.sub(r'\s+', ' ', cleaned)

    if ioc_type in ('SHA256', 'SHA1', 'MD5'):
        cleaned = re.sub(r'\s+', '', cleaned)

    cleaned = cleaned.replace('[.]', '.')
    cleaned = cleaned.replace('[:]', ':')
    
    if ioc_type != 'File':
        cleaned = cleaned.replace('[', '').replace(']', '')

    if ioc_type == 'URI':
        if '://' in cleaned:
            prefix = 'https' if 's' in cleaned[:cleaned.find('://')].lower() else 'http'
            cleaned = prefix + cleaned[cleaned.find('://'):]

    return cleaned


def is_ip_address(value: str) -> bool:
    """
    Проверяет, является ли строка корректным IP-адресом.

    Args:
        value: Строка для проверки.

    Returns:
        True, если строка является IP, иначе False.
    """
    try:
        ipaddress.ip_address(value)
        return True
    except ValueError:
        return False


def smart_clean_uri(uris: list[Any], uri_clean_mode: str = "domain") -> dict[str, str]:
    """
    Сокращает URI до домена или уникального префикса.

    Args:
        uris: Список объектов URI (могут быть кортежами (orig, clean, meta) или объектами IOC).
        uri_clean_mode: Режим сокращения ("domain" или "unique").

    Returns:
        Словарь соответствия: очищенный_URI -> отображаемое_значение.
    """
    cleaned_uris = []
    for item in uris:
        if isinstance(item, tuple) and len(item) >= 2:
            cleaned_uris.append(item[1])
        elif hasattr(item, 'clean_value'):
            cleaned_uris.append(item.clean_value)
        elif isinstance(item, str):
            cleaned_uris.append(item)

    domain_groups: dict[str, list[str]] = {}
    for uri in cleaned_uris:
        try:
            parsed = urlparse(uri if uri.startswith('http') else 'http://' + uri)
            domain = parsed.netloc
            if not domain:
                domain = parsed.path.strip('/').split('/')[0]
            if not domain:
                domain = uri
            domain_groups.setdefault(domain, []).append(uri)
        except Exception:
            domain_groups.setdefault(uri, []).append(uri)

    cleaned_map: dict[str, str] = {}

    if uri_clean_mode == "domain":
        for domain, uri_list in domain_groups.items():
            for uri in uri_list:
                cleaned_map[uri] = domain
        return cleaned_map

    # Режим "unique" - до уникального префикса пути
    for domain, uri_list in domain_groups.items():
        if is_ip_address(domain):
            for uri in uri_list:
                cleaned_map[uri] = domain
            continue

        if len(uri_list) == 1:
            cleaned_map[uri_list[0]] = domain
        else:
            path_segments = {}
            for uri in uri_list:
                try:
                    parsed = urlparse(uri if uri.startswith('http') else 'http://' + uri)
                    segments = [s for s in parsed.path.strip('/').split('/') if s]
                    path_segments[uri] = segments
                except Exception:
                    path_segments[uri] = []

            for uri in uri_list:
                segments = path_segments[uri]
                if not segments:
                    cleaned_map[uri] = domain
                    continue

                cleaned_val = domain
                for depth in range(1, len(segments) + 1):
                    prefix = '/'.join(segments[:depth])
                    is_unique = all(
                        other_uri == uri or
                        '/'.join(path_segments[other_uri][:depth]) != prefix
                        for other_uri in uri_list
                    )
                    if is_unique:
                        cleaned_val = domain + '/' + prefix
                        break
                cleaned_map[uri] = cleaned_val

    return cleaned_map


def deduplicate_iocs(iocs: list[Any]) -> list[Any]:
    """
    Дедуплицирует список IOC, сохраняя уникальные комбинации значения,
    статуса и источника (файла).

    Args:
        iocs: Список доменных моделей IOC.

    Returns:
        Дедуплицированный список IOC.
    """
    seen = set()
    deduped = []
    for ioc in iocs:
        key = (ioc.clean_value, ioc.status, ioc.source_file)
        if key not in seen:
            seen.add(key)
            deduped.append(ioc)
    return deduped
