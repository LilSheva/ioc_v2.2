"""
Именование папок на сетевой шаре (legacy-правила серверного режима).
"""

import re
from datetime import datetime
from typing import Optional

from ioc_analyzer.core.report_naming import normalize_date_dd_mm_yyyy, parse_gossopka_filename

_FSTEC_NUM_PATTERN = re.compile(r"240[\s/-]*93[\s/-]*\d+")
_DATE_PATTERN = re.compile(r"\b(\d{2}\.\d{2}\.\d{4})\b")
_DATE_SHORT_PATTERN = re.compile(r"\b(\d{2}\.\d{2}\.\d{2})\b")
_INVALID_PATH_CHARS = re.compile(r'[\\/*?:"<>|]')

_MONTHS_RU = {
    1: "января", 2: "февраля", 3: "марта", 4: "апреля", 5: "мая", 6: "июня",
    7: "июля", 8: "августа", 9: "сентября", 10: "октября", 11: "ноября", 12: "декабря",
}


def sanitize_folder_name(name: str) -> str:
    """Убирает символы, недопустимые в имени папки Windows."""
    return _INVALID_PATH_CHARS.sub("_", name).strip()


def format_received_date_ru(dt: datetime) -> str:
    """Дата письма в формате «17 мая»."""
    try:
        return f"{dt.day} {_MONTHS_RU[dt.month]}"
    except (AttributeError, KeyError):
        now = datetime.now()
        return f"{now.day} {_MONTHS_RU[now.month]}"


def extract_date_from_doc(doc_text: str, filename: str) -> str:
    """Дата дд.мм.гггг из имени файла или текста документа."""
    parsed = parse_gossopka_filename(filename)
    if parsed:
        return parsed[0]
    match = _DATE_PATTERN.search(filename)
    if match:
        return match.group(1)
    short = _DATE_SHORT_PATTERN.search(filename)
    if short:
        return normalize_date_dd_mm_yyyy(short.group(1))
    match = _DATE_PATTERN.search(doc_text)
    if match:
        return match.group(1)
    return datetime.now().strftime("%d.%m.%Y")


def extract_bulletin_number(doc_text: str, filename: str, metadata_num: str = "") -> str:
    """Номер мер ФСТЭК (паттерн 240 93 …)."""
    if metadata_num:
        match = _FSTEC_NUM_PATTERN.search(metadata_num)
        if match:
            return match.group(0).strip()

    match = _FSTEC_NUM_PATTERN.search(filename)
    if match:
        return match.group(0).strip()

    match = _FSTEC_NUM_PATTERN.search(doc_text)
    if match:
        return match.group(0).strip()

    if metadata_num:
        return metadata_num.strip()
    return "240 93"


def build_mailbox_folder_name(
    mode: str,
    *,
    received_time: datetime,
    doc_text: str,
    first_docx_name: str,
    metadata_num: str = "",
) -> str:
    """
    Формирует имя корневой папки на шаре (с завершающим « -»).
    """
    if mode == "gossopka":
        doc_date = extract_date_from_doc(doc_text, first_docx_name)
        folder_name = f"ВЦ МЭ от {doc_date} -"
    else:
        bulletin_num = extract_bulletin_number(doc_text, first_docx_name, metadata_num)
        received_date_ru = format_received_date_ru(received_time)
        cve_part = " CVE" if "BDU:20" in doc_text else ""
        folder_name = f"Меры {bulletin_num} ({received_date_ru}){cve_part} -"

    return sanitize_folder_name(folder_name)
