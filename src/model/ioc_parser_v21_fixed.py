"""
Модуль для извлечения IOC из документов V2.3 FINAL.
ИСПРАВЛЕНИЯ:
- URI: Внедрена новая, надежная логика обработки URI с переносами.
- File: Исправлена очистка от переносов строк (`\n`) в `clean_ioc`.
- Email/DNS: Восстановлена оригинальная логика парсинга, но с улучшенными,
  более точными регулярными выражениями, чтобы исправить ошибки с "спискам:" и извлечением доменов из почты.
"""

import re
from typing import List, Dict, Any, Tuple
from docx import Document


class IOCParser:
    """Парсер для извлечения IOC из .docx файлов V2.3 FINAL."""

    def __init__(self, ioc_config: List[Dict[str, Any]]):
        """Инициализация парсера."""
        self.ioc_config = ioc_config

    def extract_text_from_docx(self, file_path: str) -> str:
        """Извлекает весь текст из .docx файла (параграфы и таблицы)."""
        try:
            doc = Document(file_path)
            text_parts = []
            for paragraph in doc.paragraphs:
                if paragraph.text.strip():
                    text_parts.append(paragraph.text)
            for table in doc.tables:
                for row in table.rows:
                    for cell in row.cells:
                        if cell.text.strip():
                            text_parts.append(cell.text)
            return '\n'.join(text_parts)
        except Exception as e:
            raise Exception(f"Ошибка при чтении файла {file_path}: {str(e)}")

    def extract_from_files(self, file_paths: List[str]) -> str:
        """Извлекает и объединяет текст из нескольких файлов."""
        combined_text = [self.extract_text_from_docx(fp) for fp in file_paths]
        return '\n\n'.join(combined_text)

    @staticmethod
    def clean_ioc(ioc: str, ioc_type: str) -> str:
        """
        Очищает IOC от обфускации.
        """
        cleaned = ioc.strip()

        # ИСПРАВЛЕНИЕ ДЛЯ ФАЙЛОВ: Заменяем любые пробельные символы (включая \n) на один пробел.
        if ioc_type == 'File':
            cleaned = re.sub(r'\s+', ' ', cleaned)

        cleaned = cleaned.replace('[.]', '.')
        cleaned = cleaned.replace('[:]', ':')
        cleaned = cleaned.replace('[', '').replace(']', '')

        if ioc_type == 'URI':
            if '://' in cleaned:
                cleaned = 'http' + cleaned[cleaned.find('://'):]
            port_pattern = r'^(https?://)([a-zA-Z0-9.-]+)(:\d+)(/.*)?$'
            match = re.match(port_pattern, cleaned)
            if match:
                protocol, host, _, path = match.groups()
                cleaned = f"{protocol}{host}{path or ''}"

        return cleaned

    def find_all_raw_matches(self, text: str) -> Dict[str, List[Tuple[str, str]]]:
        """
        Финальная логика извлечения IOC по порядку с удалением из текста.
        """
        raw_matches = {}
        
        # ШАГ 1: Предварительная "склейка" URI, разорванных переносом строки.
        stitching_pattern = re.compile(r'([a-zA-Z0-9/\]:.)])\s*\n\s*(?=[a-zA-Z0-9/\[(])')
        working_text = stitching_pattern.sub(r'\1', text)

        # ШАГ 2: Извлечение полных URI с помощью одного regex.
        uri_pairs = []
        uri_pattern = re.compile(r'\b[a-zA-Z0-9][^\s<>"]*?\[:\]//(?:[^.,;\s<>\[\]]|[\[].{1,2}[\]])+')
        
        uri_matches = sorted([m for m in uri_pattern.finditer(working_text)], key=lambda m: m.start(), reverse=True)

        for match in uri_matches:
            original = match.group(0)
            cleaned = self.clean_ioc(original, 'URI')
            uri_pairs.append((original, cleaned))
            start, end = match.span()
            working_text = working_text[:start] + ' ' * (end - start) + working_text[end:]
            
        raw_matches['URI'] = sorted(uri_pairs, key=lambda x: x[0])

        # --- Далее следует ВАША ОРИГИНАЛЬНАЯ ЛОГИКА С УЛУЧШЕННЫМИ REGEX ---
        
        # ШАГ 3: IP - ищем и удаляем
        ip_pairs = []
        for ioc in self.ioc_config:
            if ioc['name'] == 'IP' and ioc.get('enabled', False):
                matches = re.findall(ioc['regex'], working_text)
                for match in set(matches):
                    ip_pairs.append((match, self.clean_ioc(match, 'IP')))
                    working_text = working_text.replace(match, '', 1)
                break
        raw_matches['IP'] = ip_pairs

        # ШАГ 4: Email - ищем и удаляем (ВАЖНО: ПЕРЕД DNS)
        email_pairs = []
        for ioc in self.ioc_config:
            if ioc['name'] == 'Email' and ioc.get('enabled', False):
                # УЛУЧШЕННЫЙ REGEX: ищет email сразу с обфускацией `[.]`
                email_regex = r'\b[a-zA-Z0-9._%+-]+@(?:[a-zA-Z0-9-]+\.)*[a-zA-Z0-9-]+\[\.\][a-zA-Z]{2,}\b'
                matches = re.findall(email_regex, working_text)
                for match in set(matches):
                    email_pairs.append((match, self.clean_ioc(match, 'Email')))
                    working_text = working_text.replace(match, '', 1)
                break
        raw_matches['Email'] = email_pairs

        # ШАГ 5: Files - ищем в угловых скобках «»
        file_pairs = []
        file_matches = re.findall(r'«([^»]+)»', working_text)
        for match in set(file_matches):
            working_text = working_text.replace(f'«{match}»', '', 1)
            # Ваша оригинальная, правильная логика валидации
            if ('.' in match and
                len(match.split('.')[0].strip()) > 0 and
                len(match.split('.')[-1].strip()) >= 1):
                cleaned = self.clean_ioc(match, 'File')
                file_pairs.append((match, cleaned))
        raw_matches['File'] = file_pairs

        # ШАГ 6: DNS - в оставшемся тексте
        dns_pairs = []
        for ioc in self.ioc_config:
            if ioc['name'] == 'DNS' and ioc.get('enabled', False):
                # УЛУЧШЕННЫЙ REGEX: более строгий, не захватывает "спискам:"
                dns_regex = r'\b(?:[a-zA-Z0-9-]+\.)*(?:[a-zA-Z0-9-]+\[\.\][a-zA-Z]{2,})\b'
                matches = re.findall(dns_regex, working_text)
                for match in set(matches):
                    dns_pairs.append((match, self.clean_ioc(match, 'DNS')))
                    working_text = working_text.replace(match, '', 1)
                break
        raw_matches['DNS'] = dns_pairs

        # ШАГ 7: Hashes - в правильном порядке
        hash_order = ['SHA256', 'SHA1', 'MD5']
        found_hash_strings = set()
        for hash_name in hash_order:
            for ioc in self.ioc_config:
                if ioc['name'] == hash_name and ioc.get('enabled', False):
                    matches = re.findall(ioc['regex'], working_text)
                    hash_pairs = []
                    for match in set(matches):
                        if not any(match in found for found in found_hash_strings):
                            hash_pairs.append((match, self.clean_ioc(match, hash_name)))
                            found_hash_strings.add(match)
                            working_text = working_text.replace(match, '', 1)
                    if hash_name not in raw_matches:
                        raw_matches[hash_name] = []
                    raw_matches[hash_name].extend(hash_pairs)
                    break

        return raw_matches

    def parse(self, file_paths: List[str]) -> Dict[str, List[Tuple[str, str]]]:
        """
        Основной метод парсинга IOC из файлов.
        """
        combined_text = self.extract_from_files(file_paths)
        ioc_results = self.find_all_raw_matches(combined_text)
        
        for ioc in self.ioc_config:
            name = ioc['name']
            if name not in ioc_results:
                ioc_results[name] = []
        
        return ioc_results