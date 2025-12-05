"""Парсер IOC из документов Word (.docx) с поддержкой режимов ФСТЕК и ГосСОПКА."""

import os
import re
from typing import List, Dict, Any, Tuple
from docx import Document


class IOCParser:
    """Парсер для извлечения IOC из .docx файлов V2.3 FINAL."""

    def __init__(self, ioc_config: List[Dict[str, Any]], mode: str = "fstek"):
        """
        Инициализация парсера.

        Args:
            ioc_config: Конфигурация типов IOC
            mode: Режим работы - "fstek" или "gossopka"
        """
        self.ioc_config = ioc_config
        self.mode = mode
        self.file_blacklist = []
        self.filename_exclusions = []
        for ioc in self.ioc_config:
            if ioc['name'] == 'File':
                self.file_blacklist = ioc.get('file_blacklist', [])
                self.filename_exclusions = ioc.get('filename_exclusions', [])
                break

    def extract_metadata_from_docx(self, file_path: str) -> dict:
        """
        Извлекает метаданные из начала .docx файла.

        Ищет:
        - Номер после символа "№"
        - Тип события между "Тип события:" и "Источник информации"

        Returns:
            dict с ключами: filename, bulletin_num, event_type
        """
        metadata = {
            "filename": os.path.basename(file_path),
            "bulletin_num": "",
            "event_type": ""
        }

        try:
            doc = Document(file_path)
            # Собираем первые несколько параграфов для поиска метаданных
            header_text = []
            for i, paragraph in enumerate(doc.paragraphs):
                if i < 20:  # Берем первые 20 параграфов
                    header_text.append(paragraph.text)
                else:
                    break

            full_header = '\n'.join(header_text)

            # Извлекаем номер после символа №
            num_match = re.search(r'№\s*([^\n]+)', full_header)
            if num_match:
                metadata["bulletin_num"] = num_match.group(1).strip()

            # Извлекаем тип события между "Тип события:" и "Источник информации"
            event_match = re.search(r'Тип\s+события:\s*(.+?)(?=Источник\s+информации|$)', full_header, re.IGNORECASE | re.DOTALL)
            if event_match:
                event_type = event_match.group(1).strip()
                # Убираем переносы строк
                event_type = re.sub(r'\s+', ' ', event_type)
                metadata["event_type"] = event_type

        except Exception as e:
            # В случае ошибки возвращаем метаданные с пустыми полями
            pass

        return metadata

    def extract_text_from_docx(self, file_path: str) -> str:
        """Извлекает весь текст из .docx файла (параграфы и таблицы)."""
        try:
            doc = Document(file_path)
            text_parts = []

            # Извлечение текста из параграфов
            for paragraph in doc.paragraphs:
                if paragraph.text.strip():
                    text_parts.append(paragraph.text)

            # Извлечение текста из таблиц с разделением ячеек для предотвращения склеивания IOC
            for table in doc.tables:
                for row in table.rows:
                    for cell in row.cells:
                        if cell.text.strip():
                            text_parts.append(cell.text.strip() + '\n')

            return '\n'.join(text_parts)
        except Exception as e:
            raise Exception(f"Ошибка при чтении файла {file_path}: {str(e)}")

    def extract_from_files(self, file_paths: List[str]) -> str:
        """Извлекает и объединяет текст из нескольких файлов."""
        combined_text = [self.extract_text_from_docx(fp) for fp in file_paths]
        return '\n\n'.join(combined_text)

    @staticmethod
    def clean_ioc(ioc: str, ioc_type: str) -> str:
        """Очищает IOC от обфускации."""
        cleaned = ioc.strip()

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
        Извлекает IOC из текста в порядке: Email -> URI -> IP -> Files -> DNS -> Hashes.
        Хеши обрабатываются последними чтобы не извлекать их из URI/путей.
        """
        raw_matches = {}
        working_text = text

        # Email - обрабатываем первыми
        email_pairs = []
        for ioc in self.ioc_config:
            if ioc['name'] == 'Email' and ioc.get('enabled', False):
                if self.mode == "gossopka":
                    # В ГосСОПКА поддерживаем смешанную обфускацию (. и [.])
                    email_regex_mixed = r'\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9-]+(?:(?:\.|\[\.\])[a-zA-Z0-9-]+)+\b'
                    matches_mixed = re.findall(email_regex_mixed, working_text)
                    for match in set(matches_mixed):
                        if '[.]' in match:
                            email_pairs.append((match, self.clean_ioc(match, 'Email')))
                            working_text = working_text.replace(match, ' ' * len(match))

                    # Затем ищем необфусцированные email
                    email_regex_plain = r'\b[a-zA-Z0-9._%+-]+@(?:[a-zA-Z0-9-]+\.)+[a-zA-Z]{2,}\b'
                    matches_plain = re.findall(email_regex_plain, working_text)
                    for match in set(matches_plain):
                        email_pairs.append((match, match))
                        working_text = working_text.replace(match, ' ' * len(match))
                else:
                    # В ФСТЕК только обфусцированные
                    email_regex = r'\b[a-zA-Z0-9._%+-]+@(?:[a-zA-Z0-9-]+\.)*[a-zA-Z0-9-]+\[\.\][a-zA-Z]{2,}\b'
                    matches = re.findall(email_regex, working_text)
                    for match in set(matches):
                        email_pairs.append((match, self.clean_ioc(match, 'Email')))
                        working_text = working_text.replace(match, ' ' * len(match))
                break
        raw_matches['Email'] = email_pairs

        # URI - склейка разорванных переносом строки и извлечение
        stitching_pattern = re.compile(r'([/\]:.)])[ \t]*\n[ \t]*(?=[a-z0-9/\[(])')
        working_text = stitching_pattern.sub(r'\1', working_text)

        uri_pairs = []
        if self.mode == "gossopka":
            # В ГосСОПКА ищем и [:]// и ://
            uri_pattern = re.compile(r'\b[a-zA-Z0-9][^\s<>"\n\r]*?(?:\[:\]|:)//(?:[^\s<>"\n\r]|[\[].{1,2}[\]])+(?<![.,;])')
        else:
            # В ФСТЕК только обфусцированный [:]//
            uri_pattern = re.compile(r'\b[a-zA-Z0-9][^\s<>"\n\r]*?\[:\]//(?:[^.,;\s<>\[\]\n\r]|[\[].{1,2}[\]])+')

        uri_matches = sorted([m for m in uri_pattern.finditer(working_text)], key=lambda m: m.start(), reverse=True)

        for match in uri_matches:
            original = match.group(0)
            cleaned = self.clean_ioc(original, 'URI')
            uri_pairs.append((original, cleaned))
            start, end = match.span()
            working_text = working_text[:start] + ' ' * (end - start) + working_text[end:]

        raw_matches['URI'] = sorted(uri_pairs, key=lambda x: x[0])

        # IP
        ip_pairs = []
        for ioc in self.ioc_config:
            if ioc['name'] == 'IP' and ioc.get('enabled', False):
                matches = re.findall(ioc['regex'], working_text)
                for match in set(matches):
                    ip_pairs.append((match, self.clean_ioc(match, 'IP')))
                    working_text = working_text.replace(match, ' ' * len(match))
                break
        raw_matches['IP'] = ip_pairs

        # Files - извлекаем из «...» с проверкой контекста и валидности
        file_pairs = []
        for match_obj in re.finditer(r'«([^»]+)»', working_text):
            filename = match_obj.group(1)

            # Проверка на слова-исключения перед файлом
            start_pos = match_obj.start()
            text_before = working_text[max(0, start_pos - 20):start_pos].lower().rstrip()
            if any(text_before.endswith(word) for word in self.file_blacklist):
                continue

            # Проверка на исключенные имена файлов
            if filename.strip() in self.filename_exclusions:
                continue

            # Валидация: имя + расширение из букв
            parts = filename.rsplit('.', 1)
            if len(parts) == 2 and parts[0].strip() and re.match(r'^[a-zA-Z]+$', parts[1].strip()):
                cleaned = self.clean_ioc(filename, 'File')
                file_pairs.append((filename, cleaned))

        for original, _ in file_pairs:
            working_text = working_text.replace(f'«{original}»', ' ' * (len(original) + 2))

        raw_matches['File'] = file_pairs

        # DNS
        dns_pairs = []
        for ioc in self.ioc_config:
            if ioc['name'] == 'DNS' and ioc.get('enabled', False):
                dns_regex = r'\b[a-zA-Z0-9-]+(?:\[\.\][a-zA-Z0-9-]+)+\b'
                matches = re.findall(dns_regex, working_text)
                for match in set(matches):
                    if '@' not in match:
                        dns_pairs.append((match, self.clean_ioc(match, 'DNS')))
                        working_text = working_text.replace(match, ' ' * len(match))
                break
        raw_matches['DNS'] = dns_pairs

        # Hashes - обрабатываем последними (не извлекаем хеши из URI/путей)
        hash_order = ['SHA256', 'SHA1', 'MD5']
        for hash_name in hash_order:
            for ioc in self.ioc_config:
                if ioc['name'] == hash_name and ioc.get('enabled', False):
                    hash_pairs = []
                    matches = re.findall(ioc['regex'], working_text)
                    for match in set(matches):
                        hash_pairs.append((match, self.clean_ioc(match, hash_name)))
                        working_text = working_text.replace(match, ' ' * len(match))

                    if hash_name not in raw_matches:
                        raw_matches[hash_name] = []
                    raw_matches[hash_name].extend(hash_pairs)
                    break

        return raw_matches

    def parse(self, file_paths: List[str]) -> Dict[str, List[Tuple[str, str, dict]]]:
        """
        Основной метод парсинга IOC из файлов.
        Возвращает Dict[str, List[Tuple[original, cleaned, metadata]]].

        metadata = {
            "filename": str,
            "bulletin_num": str,  # Номер после № (для ГосСОПКА)
            "event_type": str     # Тип события из начала файла
        }
        """
        # Инициализация результатов
        ioc_results = {}
        for ioc in self.ioc_config:
            ioc_results[ioc['name']] = []

        # Обработка каждого файла отдельно для привязки IOC к файлам
        for file_path in file_paths:
            # Извлекаем метаданные из файла
            metadata = self.extract_metadata_from_docx(file_path)

            # Извлекаем текст и парсим IOC
            text = self.extract_text_from_docx(file_path)
            file_ioc_results = self.find_all_raw_matches(text)

            # Добавляем метаданные к каждому IOC
            for ioc_type, ioc_list in file_ioc_results.items():
                # Проверяем что тип IOC существует в результатах
                if ioc_type in ioc_results:
                    for original, cleaned in ioc_list:
                        ioc_results[ioc_type].append((original, cleaned, metadata.copy()))

        return ioc_results