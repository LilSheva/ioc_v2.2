"""
Модуль предварительного парсинга списков индикаторов ФСТЭК.
"""

import re
from typing import Dict, Tuple
from ioc_analyzer.core.parser.cleaner import clean_ioc


def pre_parse_fstek_lists(working_text: str) -> Tuple[Dict[str, list[Tuple[str, str, int, int]]], str]:
    """
    Ищет списки хэшей через точку с запятой, извлекает их и маскирует текст в буфере.

    Args:
        working_text: Исходный текст для разбора.

    Returns:
        Кортеж (найденные_матчи_по_типам, измененный_текст).
    """
    raw_matches: Dict[str, list[Tuple[str, str, int, int]]] = {}
    list_pattern = re.compile(r'(?i)(?:спискам:|\(md5\):|\(sha256\):|\(sha-256\):)\s*([a-fA-F0-9\s;\n\r]+?)\.')
    list_matches = list(list_pattern.finditer(working_text))

    for m in reversed(list_matches):
        list_content = m.group(1)
        start, end = m.span()
        
        parts = [p.strip() for p in list_content.split(';') if p.strip()]
        for part in parts:
            part_cleaned = re.sub(r'\s+', '', part)
            if re.match(r'^[a-fA-F0-9]{32}$', part_cleaned):
                cleaned = clean_ioc(part, 'MD5')
                part_start = start + m.group(0).find(part)
                part_end = part_start + len(part)
                raw_matches.setdefault('MD5', []).append((part, cleaned, part_start, part_end))
            elif re.match(r'^[a-fA-F0-9]{64}$', part_cleaned):
                cleaned = clean_ioc(part, 'SHA256')
                part_start = start + m.group(0).find(part)
                part_end = part_start + len(part)
                raw_matches.setdefault('SHA256', []).append((part, cleaned, part_start, part_end))
            elif re.match(r'^[a-fA-F0-9]{40}$', part_cleaned):
                cleaned = clean_ioc(part, 'SHA1')
                part_start = start + m.group(0).find(part)
                part_end = part_start + len(part)
                raw_matches.setdefault('SHA1', []).append((part, cleaned, part_start, part_end))
        
        # Заменяем текст списка пробелами, чтобы предотвратить повторное извлечение
        working_text = working_text[:start] + ' ' * (end - start) + working_text[end:]

    return raw_matches, working_text
