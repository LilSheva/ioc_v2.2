"""
Базовый модуль регулярных выражений и поиска индикаторов компрометации (IOC).
"""

import re
from typing import Any, Tuple
from ioc_analyzer.core.parser.cleaner import clean_ioc
from ioc_analyzer.core.parser.fstek_parser import pre_parse_fstek_lists


class BaseIOCParser:
    """
    Класс для базового RegExp-парсинга IOC из текстов бюллетеней.
    """

    def __init__(self, ioc_config: list[dict[str, Any]], mode: str = "fstek"):
        """
        Инициализация парсера конфигурацией регулярных выражений.
        """
        self.ioc_config = ioc_config
        self.mode = mode
        self.file_blacklist: list[str] = []
        self.filename_exclusions: list[str] = []
        for ioc in self.ioc_config:
            if ioc['name'] == 'File':
                self.file_blacklist = ioc.get('file_blacklist', [])
                self.filename_exclusions = ioc.get('filename_exclusions', [])
                break

    def _get_ioc_filters(self, ioc_name: str) -> Tuple[list[str], list[str]]:
        """Возвращает списки (blacklist, exclusions) для типа IOC в нижнем регистре."""
        for ioc in self.ioc_config:
            if ioc['name'] == ioc_name:
                bl = [v.lower() for v in ioc.get('blacklist', [])]
                excl = [v.lower() for v in ioc.get('exclusions', [])]
                return bl, excl
        return [], []

    def _passes_filters(self, cleaned: str, match_start: int, working_text: str,
                        blacklist: list[str], exclusions: list[str]) -> bool:
        """Проверяет прохождение индикатора через фильтры исключений."""
        if blacklist and cleaned.lower() in blacklist:
            return False
        if exclusions:
            text_before = working_text[max(0, match_start - 30):match_start].lower().rstrip()
            if any(text_before.endswith(exc) for exc in exclusions):
                return False
        return True

    def _extract_with_finditer(self, working_text: str, pattern: str, ioc_name: str) -> Tuple[list[Tuple[str, str, int, int]], str]:
        """
        Экстрактор с заменой справа налево.
        """
        blacklist, exclusions = self._get_ioc_filters(ioc_name)
        seen: set[str] = set()
        collected: list[Tuple[str, str, int, int]] = []

        matches = list(re.finditer(pattern, working_text))
        for m in reversed(matches):
            original = m.group(0)
            cleaned = clean_ioc(original, ioc_name)
            start, end = m.span()

            should_include = (
                cleaned not in seen
                and self._passes_filters(cleaned, start, working_text, blacklist, exclusions)
            )

            # Заменяем на пробелы, чтобы не задеть другими RegExp
            working_text = working_text[:start] + ' ' * (end - start) + working_text[end:]

            if should_include:
                seen.add(cleaned)
                collected.append((original, cleaned, start, end))

        collected.reverse()
        return collected, working_text

    def find_all_raw_matches_with_spans(self, text: str) -> dict[str, list[Tuple[str, str, int, int]]]:
        """
        Выполняет поиск IOC всех типов, возвращая координаты spans.
        Порядок поиска: Email -> URI -> IP -> Files -> DNS -> Hashes.
        """
        raw_matches: dict[str, list[Tuple[str, str, int, int]]] = {}
        working_text = text

        # 1. Списки ФСТЭК (только в режиме fstek)
        if self.mode == "fstek":
            fstek_matches, working_text = pre_parse_fstek_lists(working_text)
            for k, v in fstek_matches.items():
                raw_matches[k] = v

        # 2. Email
        email_pairs: list[Tuple[str, str, int, int]] = []
        email_regex_mixed = (
            r'(?<![A-Za-z0-9._%+\-\[\]])'
            r'(?:[a-zA-Z0-9_%+\-]+(?:\[\.\]|\.))*'
            r'[a-zA-Z0-9_%+\-]+'
            r'@[a-zA-Z0-9-]+(?:(?:\.|\[\.\])[a-zA-Z0-9-]+)+'
            r'(?![a-zA-Z0-9\-])'
        )
        email_regex_plain = r'\b[a-zA-Z0-9._%+-]+@(?:[a-zA-Z0-9-]+\.)+[a-zA-Z]{2,}\b'

        for ioc in self.ioc_config:
            if ioc['name'] == 'Email' and ioc.get('enabled', False):
                bl, excl = self._get_ioc_filters('Email')
                matches = list(re.finditer(email_regex_mixed, working_text))
                for m in reversed(matches):
                    original = m.group(0)
                    cleaned = clean_ioc(original, 'Email')
                    start, end = m.span()
                    if self.mode != "gossopka" and '[.]' not in original:
                        continue
                    if cleaned not in [x[1] for x in email_pairs] and self._passes_filters(cleaned, start, working_text, bl, excl):
                        email_pairs.append((original, cleaned, start, end))
                    working_text = working_text[:start] + ' ' * (end - start) + working_text[end:]

                if self.mode == "gossopka":
                    matches = list(re.finditer(email_regex_plain, working_text))
                    for m in reversed(matches):
                        original = m.group(0)
                        cleaned = clean_ioc(original, 'Email')
                        start, end = m.span()
                        if cleaned not in [x[1] for x in email_pairs] and self._passes_filters(cleaned, start, working_text, bl, excl):
                            email_pairs.append((original, cleaned, start, end))
                        working_text = working_text[:start] + ' ' * (end - start) + working_text[end:]
                break
        email_pairs.reverse()
        raw_matches['Email'] = email_pairs

        # 3. URI (сшивание переносов)
        stitching_pattern = re.compile(r'([/\]:.)])[ \t]*\n[ \t]*(?=[a-z0-9/\[(])')
        working_text = stitching_pattern.sub(r'\1', working_text)

        uri_pairs: list[Tuple[str, str, int, int]] = []
        if self.mode == "gossopka":
            uri_pattern = re.compile(r'\b[a-zA-Z0-9][^\s<>"\n\r]*?(?:\[:\]|:)//(?:[^\s<>"\n\r]|[\[].{1,2}[\]])+(?<![.,;])')
        else:
            uri_pattern = re.compile(r'\b[a-zA-Z0-9][^\s<>"\n\r]*?\[:\]//(?:[^.,;\s<>\[\]\n\r]|[\[].{1,2}[\]])+')

        bl_uri, excl_uri = self._get_ioc_filters('URI')
        uri_matches = sorted(uri_pattern.finditer(working_text), key=lambda m: m.start(), reverse=True)
        for m in uri_matches:
            original = m.group(0)
            cleaned = clean_ioc(original, 'URI')
            start, end = m.span()
            if self._passes_filters(cleaned, start, working_text, bl_uri, excl_uri):
                uri_pairs.append((original, cleaned, start, end))
            working_text = working_text[:start] + ' ' * (end - start) + working_text[end:]
        raw_matches['URI'] = sorted(uri_pairs, key=lambda x: x[0])

        # 4. IP
        ip_pairs: list[Tuple[str, str, int, int]] = []
        for ioc in self.ioc_config:
            if ioc['name'] == 'IP' and ioc.get('enabled', False):
                pairs, working_text = self._extract_with_finditer(working_text, ioc['regex'], 'IP')
                ip_pairs.extend(pairs)
                break
        raw_matches['IP'] = ip_pairs

        # 5. Files
        file_pairs: list[Tuple[str, str, int, int]] = []
        file_matches = list(re.finditer(r'«([^»]+)»', working_text))
        for m_obj in reversed(file_matches):
            filename = m_obj.group(1)
            start_pos = m_obj.start()
            end_pos = m_obj.end()

            text_before = working_text[max(0, start_pos - 20):start_pos].lower().rstrip()
            if any(text_before.endswith(word) for word in self.file_blacklist):
                continue
            if filename.strip() in self.filename_exclusions:
                continue

            parts = filename.rsplit('.', 1)
            if len(parts) == 2 and parts[0].strip() and re.match(r'^[a-zA-Z]+$', parts[1].strip()):
                cleaned = clean_ioc(filename, 'File')
                start = start_pos + 1
                end = start_pos + 1 + len(filename)
                file_pairs.append((filename, cleaned, start, end))
                working_text = working_text[:start_pos] + ' ' * (end_pos - start_pos) + working_text[end_pos:]
        file_pairs.reverse()
        raw_matches['File'] = file_pairs

        # 6. DNS
        dns_pairs: list[Tuple[str, str, int, int]] = []
        for ioc in self.ioc_config:
            if ioc['name'] == 'DNS' and ioc.get('enabled', False):
                dns_regex = (
                    r'\b(?=[^\s]*\[\.\])[a-zA-Z0-9-]+(?:(?:\.|\[\.\])[a-zA-Z0-9-]+)+\b'
                    if self.mode == "gossopka" else
                    r'\b[a-zA-Z0-9-]+(?:\[\.\][a-zA-Z0-9-]+)+\b'
                )
                bl_dns, excl_dns = self._get_ioc_filters('DNS')
                matches_dns = list(re.finditer(dns_regex, working_text))
                for m in reversed(matches_dns):
                    original = m.group(0)
                    if '@' in original:
                        continue
                    cleaned = clean_ioc(original, 'DNS')
                    start, end = m.span()
                    if self._passes_filters(cleaned, start, working_text, bl_dns, excl_dns):
                        dns_pairs.append((original, cleaned, start, end))
                    working_text = working_text[:start] + ' ' * (end - start) + working_text[end:]
                dns_pairs.reverse()
                break
        raw_matches['DNS'] = dns_pairs

        # 7. Hashes & Registry
        hash_order = ['SHA256', 'SHA1', 'MD5', 'Registry']
        for name in hash_order:
            for ioc in self.ioc_config:
                if ioc['name'] == name and ioc.get('enabled', False):
                    pairs, working_text = self._extract_with_finditer(working_text, ioc['regex'], name)
                    raw_matches.setdefault(name, [])
                    existing_spans = {(x[2], x[3]) for x in raw_matches[name]}
                    for original, cleaned, start, end in pairs:
                        if (start, end) not in existing_spans:
                            raw_matches[name].append((original, cleaned, start, end))
                    break

        return raw_matches
