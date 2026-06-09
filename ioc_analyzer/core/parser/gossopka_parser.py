"""
Модуль для парсинга индикаторов и контекста в режиме ГосСОПКА.
"""

from typing import Any, Tuple
from ioc_analyzer.ports.document_port import ParagraphData


def extract_sections_from_paragraphs(paragraphs: list[ParagraphData]) -> list[str]:
    """
    Разбивает абзацы на логические секции по горизонтальным границам.

    Args:
        paragraphs: Список данных абзацев.

    Returns:
        Список строк, каждая из которых представляет собой секцию.
    """
    sections = []
    current_paragraphs = []
    for p in paragraphs:
        if p.has_border:
            if current_paragraphs:
                sections.append("\n".join(current_paragraphs))
                current_paragraphs = []
            if p.text.strip():
                current_paragraphs.append(p.text)
        else:
            current_paragraphs.append(p.text)
    if current_paragraphs:
        sections.append("\n".join(current_paragraphs))
    return [s for s in sections if s.strip()]


def determine_sequential_statuses(
    section_text: str, 
    file_ioc_results: dict[str, list[Tuple[str, str, int, int]]]
) -> list[Tuple[str, str, str, str]]:
    """
    Последовательно определяет статус для каждого индикатора в секции.

    Ищет ключевые слова блокировки/разблокировки/поиска в непосредственном
    текстовом окружении каждого индикатора в порядке появления.

    Args:
        section_text: Полный текст секции.
        file_ioc_results: Матчи индикаторов с координатами в тексте секции.

    Returns:
        Список кортежей (ioc_type, original, cleaned, status).
    """
    all_matches = []
    for ioc_type, ioc_list in file_ioc_results.items():
        for original, cleaned, start, end in ioc_list:
            all_matches.append((ioc_type, original, cleaned, start, end))
            
    # Сортируем индикаторы по позиции их появления в секции
    all_matches.sort(key=lambda x: x[3])
    
    results = []
    n = len(all_matches)
    for i in range(n):
        ioc_type, original, cleaned, start, end = all_matches[i]
        
        prev_end = all_matches[i-1][4] if i > 0 else 0
        next_start = all_matches[i+1][3] if i < n - 1 else len(section_text)
        
        before_context = section_text[prev_end:start].lower()
        after_context = section_text[end:next_start].lower()
        
        status = None
        # 1. Проверяем контекст перед индикатором
        if 'разблокиров' in before_context or 'разблокира' in before_context or 'легитимный' in before_context:
            status = "unblock"
        elif 'для поиска и блокировки' in before_context:
            status = "block"
        elif 'для поиска' in before_context:
            status = "search"
        elif 'блокиров' in before_context:
            status = "block"
            
        # 2. Если не найдено, проверяем контекст после индикатора
        if status is None:
            if 'разблокиров' in after_context or 'разблокира' in after_context or 'легитимный' in after_context:
                status = "unblock"
            elif 'для поиска и блокировки' in after_context:
                status = "block"
            elif 'для поиска' in after_context:
                status = "search"
            elif 'блокиров' in after_context:
                status = "block"
                
        if status is None:
            status = "block"
            
        results.append((ioc_type, original, cleaned, status))
    return results
