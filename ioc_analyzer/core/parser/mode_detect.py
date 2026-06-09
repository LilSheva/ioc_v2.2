"""
Определение режима парсинга (ФСТЭК / ГосСОПКА) для всего письма.
"""

import os
import re

from ioc_analyzer.ports.document_port import DocumentPort, ParagraphData

_FSTEC_NUM_IN_NAME = re.compile(r"240\s*93", re.IGNORECASE)


def _level1_from_filenames(filenames: list[str]) -> str | None:
    """Уровень 1: только имена вложений. ``gossopka`` / ``fstek`` / ``None``."""
    lowered = [os.path.basename(name).lower() for name in filenames]

    if any("бюллетень" in name or "вц мэ" in name for name in lowered):
        return "gossopka"

    if any(_FSTEC_NUM_IN_NAME.search(name) for name in lowered):
        return "fstek"

    return None


def _level2_from_content(
    docx_paths: list[str],
    document_reader: DocumentPort,
) -> str | None:
    """Уровень 2: анализ содержимого .docx."""
    gossopka_hit = False
    fstec_hit = False

    for path in docx_paths:
        paragraphs = document_reader.read_paragraphs(path)
        header = "\n".join(p.text for p in paragraphs[:25])

        if re.search(r"тип\s+события\s*:", header, re.IGNORECASE):
            gossopka_hit = True
        if any(p.has_border for p in paragraphs[:80]):
            gossopka_hit = True
        header_lower = header.lower()
        if "госсопка" in header_lower or "нкцки" in header_lower:
            gossopka_hit = True

        sample = document_reader.read_full_text(path)[:1000]
        if re.search(r"фстэк\s+россии", sample, re.IGNORECASE):
            fstec_hit = True

    if gossopka_hit:
        return "gossopka"
    if fstec_hit:
        return "fstek"
    return None


def detect_mailbox_parser_mode(
    attachment_paths: list[str],
    document_reader: DocumentPort,
) -> tuple[str | None, str | None]:
    """
    Определяет единый режим для всех вложений письма.

    Returns:
        ``(mode, error)`` — при ошибке ``mode`` is ``None``.
    """
    if not attachment_paths:
        return None, "Письмо без вложений: невозможно определить тип бюллетеня."

    level1 = _level1_from_filenames(attachment_paths)
    if level1:
        return level1, None

    docx_paths = [p for p in attachment_paths if p.lower().endswith(".docx")]
    if not docx_paths:
        return None, (
            "Не удалось определить тип бюллетеня: нет .docx для анализа содержимого."
        )

    level2 = _level2_from_content(docx_paths, document_reader)
    if level2:
        return level2, None

    names = ", ".join(os.path.basename(p) for p in attachment_paths[:5])
    return None, (
        f"Не удалось определить тип бюллетеня (ФСТЭК/ГосСОПКА) для вложений: {names}"
    )


def detect_parser_mode(filename: str, paragraphs: list[ParagraphData]) -> str:
    """Per-file детект для GUI (режим auto). На сервере — ``detect_mailbox_parser_mode``."""
    level1 = _level1_from_filenames([filename])
    if level1:
        return level1

    header = "\n".join(p.text for p in paragraphs[:25])
    body_sample = "\n".join(p.text for p in paragraphs[:200])

    if re.search(r"тип\s+события\s*:", header, re.IGNORECASE):
        return "gossopka"
    if any(p.has_border for p in paragraphs[:80]):
        return "gossopka"
    if "госсопка" in header.lower() or "нкцки" in header.lower():
        return "gossopka"
    if re.search(r"фстэк\s+россии", body_sample[:1000], re.IGNORECASE):
        return "fstek"
    if "[.]" in body_sample:
        return "fstek"
    if _FSTEC_NUM_IN_NAME.search(filename):
        return "fstek"
    return "fstek"
