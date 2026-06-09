"""
Имена файлов отчётов и подписи столбца «Бюллетень» / description в CSV.
"""

import re

_GOSSOPKA_FILE = re.compile(
    r"бюллетень\s+от\s+(\d{2}\.\d{2}\.\d{4})_(\d+)\s+(.+?)\.docx",
    re.IGNORECASE,
)
_FSTEC_TRIPLET = re.compile(r"240[\s/-]*93[\s/-]*(\d+)", re.IGNORECASE)
_FSTEC_SLASH = re.compile(r"(\d+)\s*/\s*(\d+)\s*/\s*(\d+)")


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
    if not filename:
        return "GosSOPKA"
    base = filename.split("/")[-1].split("\\")[-1]
    match = _GOSSOPKA_FILE.search(base)
    if match:
        date, number, org = match.group(1), match.group(2), match.group(3).strip()
        return f"GosSOPKA {date}-{number} {org}"
    return f"GosSOPKA {base.rsplit('.', 1)[0]}"


def gossopka_report_date(filename: str) -> str:
    """Дата ``дд.мм.гггг`` для имени отчёта ГосСОПКА."""
    if not filename:
        return ""
    base = filename.split("/")[-1].split("\\")[-1]
    match = _GOSSOPKA_FILE.search(base)
    if match:
        return match.group(1)
    date_match = re.search(r"\b(\d{2}\.\d{2}\.\d{4})\b", base)
    return date_match.group(1) if date_match else ""


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
    label = format_fstek_label(fstek_bulletin, source_filename)
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
    label = format_fstek_label(fstek_bulletin, source_filename)
    return f"Уязвимости ({label}).xlsx"
