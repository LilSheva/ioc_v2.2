"""
Автоопределение режима парсинга (ФСТЭК / ГосСОПКА) по документу.
"""

import re

from ioc_analyzer.ports.document_port import ParagraphData

_GOSSOPKA_FILENAME = re.compile(
    r"бюллетень\s+от\s+\d{2}\.\d{2}\.\d{4}_\d+",
    re.IGNORECASE,
)
_FSTEC_FILENAME = re.compile(r"\b\d+\s+\d+\s+\d+\b")


def detect_parser_mode(filename: str, paragraphs: list[ParagraphData]) -> str:
    """
    Определяет режим парсинга по имени файла и структуре документа.

    Returns:
        ``"gossopka"`` или ``"fstek"``.
    """
    name = filename or ""
    header = "\n".join(p.text for p in paragraphs[:25])

    if _GOSSOPKA_FILENAME.search(name):
        return "gossopka"
    if re.search(r"тип\s+события\s*:", header, re.IGNORECASE):
        return "gossopka"
    if any(p.has_border for p in paragraphs[:80]):
        return "gossopka"
    if "госсопка" in header.lower() or "нкцки" in header.lower():
        return "gossopka"

    body_sample = "\n".join(p.text for p in paragraphs[:200])
    if "[.]" in body_sample:
        return "fstek"
    if _FSTEC_FILENAME.search(name):
        return "fstek"
    if re.search(r"фстэк|fstec", header, re.IGNORECASE):
        return "fstek"

    return "fstek"
