"""
Структура каталогов и сбор текста из вложений письма.
"""

import os
import shutil
from typing import Any

from ioc_analyzer.ports.document_port import DocumentPort


def collect_docx_text_bundle(
    docx_paths: list[str],
    document_reader: DocumentPort,
    ioc_config: list[dict[str, Any]],
) -> tuple[str, str]:
    """
    Считывает объединённый текст .docx и номер бюллетеня из метаданных.

    Returns:
        ``(doc_text, metadata_num)``
    """
    from ioc_analyzer.core.parser import IOCParser

    doc_text_parts: list[str] = []
    metadata_num = ""
    parser = IOCParser(ioc_config, mode="fstek", document_reader=document_reader)

    for path in docx_paths:
        try:
            paragraphs = document_reader.read_paragraphs(path)
            doc_text_parts.append(document_reader.read_full_text(path))
            meta = parser.extract_metadata_from_paragraphs(
                paragraphs, os.path.basename(path)
            )
            if meta.get("bulletin_num"):
                metadata_num = meta["bulletin_num"]
        except OSError:
            continue

    return "\n".join(doc_text_parts), metadata_num


def copy_attachments_to_task(
    attachment_paths: list[str],
    temp_dir: str,
    task_dir: str,
) -> list[str]:
    """
    Копирует вложения и body.txt в «Задача». Возвращает пути .docx в task_dir.
    """
    os.makedirs(task_dir, exist_ok=True)
    docx_in_task: list[str] = []

    for src in attachment_paths:
        if os.path.isfile(src):
            dest = os.path.join(task_dir, os.path.basename(src))
            shutil.copy2(src, dest)
            if dest.lower().endswith(".docx"):
                docx_in_task.append(dest)

    body_src = os.path.join(temp_dir, "body.txt")
    if os.path.isfile(body_src):
        shutil.copy2(body_src, os.path.join(task_dir, "body.txt"))

    return docx_in_task
