"""
Пакет парсинга бюллетеней и извлечения индикаторов компрометации.
"""

import re
from typing import Any, Tuple
from ioc_analyzer.core.parser.base_parser import BaseIOCParser
from ioc_analyzer.core.parser.cleaner import clean_ioc
from ioc_analyzer.core.constants import PARSER_MODE_AUTO
from ioc_analyzer.core.parser.gossopka_parser import (
    extract_sections_from_paragraphs,
    determine_sequential_statuses
)
from ioc_analyzer.core.parser.mode_detect import detect_parser_mode
from ioc_analyzer.ports.document_port import DocumentPort, ParagraphData


class IOCParser(BaseIOCParser):
    """
    Основной фасадный класс парсера индикаторов компрометации (IOC).
    Совместим с legacy-вызовами.
    """

    def __init__(self, ioc_config: list[dict[str, Any]], mode: str = "fstek", document_reader: DocumentPort = None):
        """
        Инициализация парсера.

        Args:
            ioc_config: Регулярные выражения и настройки типов IOC.
            mode: Режим разбора ("fstek" или "gossopka").
            document_reader: Адаптер чтения документов Word.
        """
        super().__init__(ioc_config, mode)
        self.document_reader = document_reader

    def extract_metadata_from_paragraphs(self, paragraphs: list[ParagraphData], filename: str) -> dict[str, str]:
        """
        Извлекает номер бюллетеня и тип события из первых 20 абзацев.
        """
        metadata = {
            "filename": filename,
            "bulletin_num": "",
            "event_type": ""
        }
        header_text = [p.text for p in paragraphs[:20]]
        full_header = '\n'.join(header_text)

        num_match = re.search(r'№\s*([^\n]+)', full_header)
        if num_match:
            metadata["bulletin_num"] = num_match.group(1).strip()

        event_match = re.search(r'Тип\s+события:\s*(.+?)(?=Источник\s+информации|$)', full_header, re.IGNORECASE | re.DOTALL)
        if event_match:
            event_type = event_match.group(1).strip()
            event_type = re.sub(r'\s+', ' ', event_type)
            metadata["event_type"] = event_type

        return metadata

    def find_all_raw_matches(self, text: str) -> dict[str, list[Tuple[str, str]]]:
        """
        Возвращает индикаторы в виде словаря списков кортежей (original, cleaned).
        Сохранено для обратной совместимости.
        """
        spans_res = self.find_all_raw_matches_with_spans(text)
        raw_res = {}
        for ioc_type, items in spans_res.items():
            raw_res[ioc_type] = [(original, cleaned) for original, cleaned, start, end in items]
        return raw_res

    def extract_bdu_identifiers(self, file_paths: list[str]) -> list[Tuple[str, str]]:
        """
        Извлекает идентификаторы BDU из указанных файлов.
        """
        if not self.document_reader:
            raise ValueError("Не задан document_reader для извлечения BDU.")

        bdu_list = []
        bdu_regex = re.compile(r'BDU:\d{4}-\d{4,6}')
        for fp in file_paths:
            text = self.document_reader.read_full_text(fp)
            matches = bdu_regex.findall(text)
            fname = filename = fp.split('/')[-1].split('\\')[-1]
            for m in set(matches):
                bdu_list.append((m, fname))
        return sorted(set(bdu_list))

    def parse(self, file_paths: list[str]) -> dict[str, list[Tuple[str, str, dict[str, Any]]]]:
        """
        Запускает парсинг файлов и возвращает результаты с метаданными.
        """
        if not self.document_reader:
            raise ValueError("Не задан document_reader для запуска парсинга.")

        ioc_results: dict[str, list[Tuple[str, str, dict[str, Any]]]] = {}
        for ioc in self.ioc_config:
            ioc_results[ioc['name']] = []

        for file_path in file_paths:
            paragraphs = self.document_reader.read_paragraphs(file_path)
            filename = file_path.split('/')[-1].split('\\')[-1]
            metadata = self.extract_metadata_from_paragraphs(paragraphs, filename)

            effective_mode = self.mode
            if self.mode == PARSER_MODE_AUTO:
                effective_mode = detect_parser_mode(filename, paragraphs)

            saved_mode = self.mode
            self.mode = effective_mode
            metadata["parser_mode"] = effective_mode

            try:
                if effective_mode == "gossopka":
                    sections = extract_sections_from_paragraphs(paragraphs)
                    for section_text in sections:
                        file_ioc_results = self.find_all_raw_matches_with_spans(section_text)
                        statuses = determine_sequential_statuses(section_text, file_ioc_results)

                        for ioc_type, original, cleaned, status in statuses:
                            meta = metadata.copy()
                            meta["status"] = status
                            ioc_results[ioc_type].append((original, cleaned, meta))
                else:
                    text = self.document_reader.read_full_text(file_path)
                    file_ioc_results = self.find_all_raw_matches_with_spans(text)
                    for ioc_type, ioc_list in file_ioc_results.items():
                        if ioc_type in ioc_results:
                            for original, cleaned, start, end in ioc_list:
                                meta = metadata.copy()
                                meta["status"] = "block"
                                ioc_results[ioc_type].append((original, cleaned, meta))
            finally:
                self.mode = saved_mode

        return ioc_results


__all__ = ["IOCParser", "clean_ioc"]
