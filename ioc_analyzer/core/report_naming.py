"""
Имена файлов отчётов и подписи столбца «Бюллетень» / description в CSV.
"""

import os
import re

_FSTEC_TRIPLET = re.compile(r"240[\s/-]*93[\s/-]*(\d+)", re.IGNORECASE)
_FSTEC_SLASH = re.compile(r"(\d+)\s*/\s*(\d+)\s*/\s*(\d+)")
_WIN_INVALID_FILENAME = re.compile(r'[\\/*?:"<>|]')

# Ищем «Бюллетень от» + дату; всё остальное парсим вручную
_GOSSOPKA_PREFIX = re.compile(r"бюллетень\s+от\s+", re.IGNORECASE)
_DATE_PATTERN = re.compile(r"\d{2}\.\d{2}\.(?:\d{4}|\d{2})")
_DIGITS = re.compile(r"\d+")


def _normalize_basename(filename: str) -> str:
    """Имя файла без пути, с нормализованными пробелами."""
    name = filename.split("/")[-1].split("\\")[-1]
    return re.sub(r"\s+", " ", name.replace("\u00a0", " ")).strip()


def normalize_date_dd_mm_yyyy(date_part: str) -> str:
    """``05.06.26`` → ``05.06.2026``."""
    parts = date_part.split(".")
    if len(parts) != 3:
        return date_part
    day, month, year = parts
    if len(year) == 2:
        year = f"20{year}"
    return f"{day}.{month}.{year}"


def parse_gossopka_filename(filename: str) -> tuple[str, str, str] | None:
    """
    Разбор имени типа ``Бюллетень от 05.06.2026_ 2 ВЦ МЭ.docx``.

    Алгоритм:
    1. Найти «Бюллетень от».
    2. Извлечь дату (dd.mm.yyyy или dd.mm.yy) и удалить её из хвоста.
    3. В оставшемся найти первое число — это номер документа.
    4. Остаток (без подчёрков, пробелов и расширения) — организация.

    Returns:
        ``(дата дд.мм.гггг, номер, организация)`` или ``None``.
    """
    if not filename:
        return None
    base = _normalize_basename(filename)
    # Убираем расширение
    stem = re.sub(r"\.docx$", "", base, flags=re.IGNORECASE).strip()

    m_prefix = _GOSSOPKA_PREFIX.search(stem)
    if not m_prefix:
        return None

    after_ot = stem[m_prefix.end():]  # всё после «Бюллетень от »

    m_date = _DATE_PATTERN.search(after_ot)
    if not m_date:
        return None
    date_raw = m_date.group(0)
    date = normalize_date_dd_mm_yyyy(date_raw)

    # Удаляем дату из хвоста, убираем лишние разделители _ и пробелы
    rest = after_ot[m_date.end():]
    rest_clean = re.sub(r"[_\s]+", " ", rest).strip()

    m_num = _DIGITS.search(rest_clean)
    if not m_num:
        return None
    doc_number = m_num.group(0)

    # Организация — всё после номера, без ведущих разделителей
    org_raw = rest_clean[m_num.end():].strip(" _-")
    org = org_raw if org_raw else "ВЦ МЭ"

    return date, doc_number, org


def pick_bulletin_source_filename(
    file_paths: list[str],
    mode: str,
    ioc_source_files: list[str] | None = None,
) -> str:
    """
    Выбирает имя файла для заголовков отчётов.

    Для ГосСОПКА ищет среди всех файлов/IOC тот, чьё имя разбирается как бюллетень,
    а не слепо берёт первый элемент списка.
    """
    candidates: list[str] = []
    for name in ioc_source_files or []:
        if name:
            candidates.append(_normalize_basename(name))
    for path in file_paths:
        candidates.append(_normalize_basename(path))

    if mode == "gossopka":
        for name in candidates:
            if parse_gossopka_filename(name):
                return name
        for name in candidates:
            if gossopka_report_date(name):
                return name

    if file_paths:
        return _normalize_basename(file_paths[0])
    return candidates[0] if candidates else "bulletin.docx"


def _filename_safe(text: str) -> str:
    """Убирает символы, недопустимые в имени файла Windows."""
    return _WIN_INVALID_FILENAME.sub("-", text).strip()


def format_fstek_label(*texts: str) -> str:
    """``FSTEK 240/93/1234`` из имени файла, поля бюллетеня или метаданных."""
    for text in texts:
        if not text:
            continue
        match = _FSTEC_TRIPLET.search(text)
        if match:
            return f"FSTEK 240/93/{match.group(1)}"
        slash = _FSTEC_SLASH.search(text.replace("FSTEC", "").replace("FSTEK", ""))
        if slash:
            return f"FSTEK {slash.group(1)}/{slash.group(2)}/{slash.group(3)}"
    return "FSTEK 240/93/unknown"


def format_gossopka_label(filename: str) -> str:
    """``GosSOPKA 21.05.2026-42 ВЦ МЭ`` из имени файла."""
    parsed = parse_gossopka_filename(filename)
    if parsed:
        date, number, org = parsed
        return f"GosSOPKA {date}-{number} {org}"
    return "GosSOPKA"


def gossopka_report_date(filename: str) -> str:
    """Дата ``дд.мм.гггг`` для имени отчёта ГосСОПКА."""
    parsed = parse_gossopka_filename(filename)
    if parsed:
        return parsed[0]
    base = _normalize_basename(filename)
    date_match = re.search(r"\b(\d{2}\.\d{2}\.\d{4})\b", base)
    if date_match:
        return date_match.group(1)
    short = re.search(r"\b(\d{2}\.\d{2}\.\d{2})\b", base)
    if short:
        return normalize_date_dd_mm_yyyy(short.group(1))
    return ""


def bulletin_column_value(
    mode: str,
    source_filename: str,
    fstek_bulletin: str = "",
) -> str:
    """Значение для столбца «Бюллетень» и description в CSV."""
    if mode == "gossopka":
        return format_gossopka_label(source_filename)
    return format_fstek_label(fstek_bulletin, source_filename)


def ioc_report_filename(
    mode: str,
    source_filename: str,
    fstek_bulletin: str = "",
) -> str:
    if mode == "gossopka":
        date = gossopka_report_date(source_filename) or "дата"
        return f"Отчет IOC (ВЦ МЭ от {date}).xlsx"
    label = _filename_safe(format_fstek_label(fstek_bulletin, source_filename))
    return f"Отчет IOC ({label}).xlsx"


def filters_report_filename(
    mode: str,
    source_filename: str,
    fstek_bulletin: str = "",
) -> str:
    base = ioc_report_filename(mode, source_filename, fstek_bulletin)
    return base.replace("Отчет IOC", "Фильтры IOC", 1)


def vulnerabilities_report_filename(
    mode: str,
    source_filename: str,
    fstek_bulletin: str = "",
) -> str:
    if mode == "gossopka":
        date = gossopka_report_date(source_filename) or "дата"
        return f"Уязвимости (ВЦ МЭ от {date}).xlsx"
    label = _filename_safe(format_fstek_label(fstek_bulletin, source_filename))
    return f"Уязвимости ({label}).xlsx"
