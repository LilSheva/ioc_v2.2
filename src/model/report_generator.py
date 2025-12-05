"""Модуль для генерации отчетов IOC с поддержкой режимов ФСТЕК и ГосСОПКА."""

import re
import os
from typing import Dict, List, Any, Tuple
from urllib.parse import urlparse
from datetime import datetime
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side


class ReportGenerator:
    """Генератор отчетов IOC."""

    def __init__(self, ioc_config: List[Dict[str, Any]], uri_clean_mode: str = "unique"):
        """
        Инициализация генератора отчетов.

        Args:
            ioc_config: Конфигурация типов IOC
            uri_clean_mode: Режим очистки URI - "unique" (до уникального префикса) или "domain" (до домена)
        """
        self.ioc_config = ioc_config
        self.uri_clean_mode = uri_clean_mode
    
    def _smart_clean_uri(self, uris: List[Tuple[str, str, dict]]) -> Dict[str, str]:
        """
        Очистка URI: сокращает до уникального префикса или до домена (зависит от режима).

        Returns: cleaned_uri -> display_uri
        """
        domain_groups = {}
        for original, cleaned, metadata in uris:
            try:
                parsed = urlparse(cleaned if cleaned.startswith('http') else 'http://' + cleaned)
                domain = parsed.netloc or parsed.path.split('/')[0]
                if domain not in domain_groups:
                    domain_groups[domain] = []
                domain_groups[domain].append(cleaned)
            except:
                domain_groups[cleaned] = [cleaned]

        if self.uri_clean_mode == "domain":
            cleaned_map = {}
            for domain, uri_list in domain_groups.items():
                for uri in uri_list:
                    cleaned_map[uri] = domain
            return cleaned_map

        # Режим "unique" - сокращаем до уникального префикса
        cleaned_map = {}
        for domain, uri_list in domain_groups.items():
            if len(uri_list) == 1:
                cleaned_map[uri_list[0]] = domain
            else:
                for uri in uri_list:
                    try:
                        parsed = urlparse(uri if uri.startswith('http') else 'http://' + uri)
                        path_parts = parsed.path.strip('/').split('/')
                        cleaned = domain
                        for i, part in enumerate(path_parts):
                            if part:
                                cleaned = domain + '/' + '/'.join(path_parts[:i+1])
                                is_unique = True
                                for other_uri in uri_list:
                                    if other_uri != uri and other_uri.startswith(cleaned):
                                        is_unique = False
                                        break
                                if is_unique:
                                    break
                        cleaned_map[uri] = cleaned
                    except:
                        cleaned_map[uri] = uri

        return cleaned_map
    
    def generate_xlsx_report(self, ioc_data: Dict[str, List[Tuple[str, str, dict]]],
                            output_path: str, bulletin: str = "", mode: str = "fstek",
                            event_type: str = "Фишинговая рассылка электронной почты. Вредоносные вложения") -> bool:
        """
        Генерирует форматированный .xlsx отчет с 10 столбцами.

        Args:
            ioc_data: Данные IOC в формате Dict[str, List[Tuple[original, cleaned, metadata]]]
            output_path: Путь для сохранения отчета
            bulletin: Бюллетень (для режима ФСТЕК)
            mode: Режим работы - "fstek" или "gossopka"
            event_type: Тип события по умолчанию (для режима ФСТЕК)
        """
        try:
            wb = Workbook()
            ws = wb.active
            ws.title = "IOC Report"
            
            headers = [
                "№", "Дата\nОтчёта", "Статус\nАктивности\nNTA",
                "Статус\nАктивности\nSIEM (Tools)", "Статус\nАктивности\nSIEM (MP)",
                "Тип\nИндикатора", "Индикатор", "IOC", "Бюллетень", "Тип события"
            ]
            ws.append(headers)
            
            header_fill = PatternFill(start_color="D3D3D3", end_color="D3D3D3", fill_type="solid")
            header_font = Font(bold=True)
            header_alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
            
            for col_num in range(1, len(headers) + 1):
                cell = ws.cell(row=1, column=col_num)
                cell.fill = header_fill
                cell.font = header_font
                cell.alignment = header_alignment
            
            uri_smart_map = {}
            if 'URI' in ioc_data:
                uri_smart_map = self._smart_clean_uri(ioc_data['URI'])

            row_num = 2
            counter = 1
            today_date = datetime.now().strftime('%d.%m.%Y')

            for ioc_config in self.ioc_config:
                if not ioc_config.get('enabled', False):
                    continue

                name = ioc_config['name']
                if name in ioc_data and ioc_data[name]:
                    report_type = ioc_config['report_type']
                    nta_status = ioc_config['nta_status']
                    siem_tools_status = ioc_config['siem_tools_status']
                    siem_status = ioc_config['siem_status']

                    for original, cleaned, metadata in ioc_data[name]:
                        display_original = original
                        if name == 'File':
                            display_original = re.sub(r'\s+', ' ', original)

                        ioc_display = cleaned
                        if name == 'URI' and cleaned in uri_smart_map:
                            ioc_display = uri_smart_map[cleaned]

                        if mode == "gossopka":
                            bulletin_num = metadata.get("bulletin_num", "")
                            file_bulletin = f"GosSOPKA {bulletin_num}" if bulletin_num else metadata.get("filename", "")
                            file_event_type = metadata.get("event_type", event_type)
                        else:
                            file_bulletin = bulletin
                            file_event_type = event_type

                        row_data = [
                            counter, today_date, nta_status, siem_tools_status,
                            siem_status, report_type, display_original,
                            ioc_display, file_bulletin, file_event_type
                        ]
                        ws.append(row_data)
                        counter += 1
                        row_num += 1

            thin_border = Border(
                left=Side(style='thin'), right=Side(style='thin'),
                top=Side(style='thin'), bottom=Side(style='thin')
            )
            center_alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
            default_alignment = Alignment(vertical="center", wrap_text=True, horizontal="left")

            for row in ws.iter_rows(min_row=1, max_row=row_num - 1, min_col=1, max_col=len(headers)):
                for cell in row:
                    cell.border = thin_border
                    if cell.row > 1:
                        if cell.column_letter in ('A', 'B', 'C', 'D', 'E', 'F'):
                            cell.alignment = center_alignment
                        else:
                            cell.alignment = default_alignment
                        
                        if cell.column_letter == 'A':
                            cell.fill = header_fill
                            cell.font = header_font

            ws.column_dimensions['A'].width = 4
            ws.column_dimensions['B'].width = 11
            ws.column_dimensions['C'].width = 14
            ws.column_dimensions['D'].width = 14
            ws.column_dimensions['E'].width = 14
            ws.column_dimensions['F'].width = 14
            ws.column_dimensions['G'].width = 90
            ws.column_dimensions['H'].width = 90
            ws.column_dimensions['I'].width = 30
            ws.column_dimensions['J'].width = 64
            
            wb.save(output_path)
            return True
            
        except Exception as e:
            print(f"Ошибка при генерации .xlsx отчета: {e}")
            return False
    
    def generate_queries_report(self, ioc_data: Dict[str, List[Tuple[str, str, dict]]],
                                output_path: str) -> bool:
        """
        Генерирует текстовый файл с объединенными поисковыми запросами.
        """
        try:
            lines = ["=" * 80, "ПОИСКОВЫЕ ЗАПРОСЫ ДЛЯ IOC", "=" * 80, ""]

            for ioc_config in self.ioc_config:
                if not ioc_config.get('enabled', False):
                    continue

                name = ioc_config['name']
                if name in ioc_data and ioc_data[name]:
                    lines.extend([f"\n{'=' * 80}", f"--- {{{name}}} ---", f"{'=' * 80}\n"])

                    cleaned_iocs = [cleaned for _, cleaned, _ in ioc_data[name]]
                    
                    mp10_templates = ioc_config.get('mp10_templates', [])
                    if mp10_templates:
                        lines.append("Для MP10")
                        for template in mp10_templates:
                            queries = [template.replace('{ioc}', ioc) for ioc in cleaned_iocs]
                            lines.append(" OR ".join(queries))
                        lines.append("")
                    
                    nad_templates = ioc_config.get('nad_templates', [])
                    if nad_templates:
                        lines.append("Для NAD")
                        for template in nad_templates:
                            queries = [template.replace('{ioc}', ioc) for ioc in cleaned_iocs]
                            lines.append(" || ".join(queries))
                        lines.append("")
            
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write('\n'.join(lines))
            
            return True
            
        except Exception as e:
            print(f"Ошибка при генерации файла запросов: {e}")
            return False
    
    def generate_query_data(self, ioc_data: Dict[str, List[Tuple[str, str, dict]]]) -> List[Dict[str, Any]]:
        """
        Генерирует структурированные данные запросов для отображения в GUI.
        """
        query_data = []

        for ioc_config in self.ioc_config:
            if not ioc_config.get('enabled', False):
                continue

            name = ioc_config['name']
            if name in ioc_data and ioc_data[name]:
                group_queries = []
                cleaned_iocs = [cleaned for _, cleaned, _ in ioc_data[name]]
                
                for template in ioc_config.get('mp10_templates', []):
                    queries = [template.replace('{ioc}', ioc) for ioc in cleaned_iocs]
                    group_queries.append({
                        'ioc_name': name, 'system': 'MP10',
                        'query': " OR ".join(queries), 'completed': False
                    })
                
                for template in ioc_config.get('nad_templates', []):
                    queries = [template.replace('{ioc}', ioc) for ioc in cleaned_iocs]
                    group_queries.append({
                        'ioc_name': name, 'system': 'NAD',
                        'query': " || ".join(queries), 'completed': False
                    })
                
                if group_queries:
                    query_data.append({
                        'group_name': f"{name} ({ioc_config['report_type']})",
                        'queries': group_queries
                    })

        return query_data

    def generate_filters_xlsx(self, ioc_data: Dict[str, List[Tuple[str, str, dict]]],
                             template_path: str, output_path: str, log_callback=None) -> bool:
        """
        Генерирует файл "Фильтры.xlsx" на основе шаблона.

        Args:
            ioc_data: Данные IOC в формате Dict[str, List[Tuple[original, cleaned, metadata]]]
            template_path: Путь к шаблону "Фильтры (Переделанные).xlsx"
            output_path: Путь для сохранения нового файла фильтров
            log_callback: Функция для логирования (опционально)

        Returns:
            True если успешно, False при ошибке
        """
        def log(message):
            if log_callback:
                log_callback(message)
            else:
                print(message)

        try:
            from openpyxl import load_workbook
            from openpyxl.utils import get_column_letter
            import socket
            import warnings

            warnings.filterwarnings('ignore', category=UserWarning, module='openpyxl')

            log(f"   • Загрузка шаблона: {template_path}")
            wb = load_workbook(template_path)
            log(f"   • Листы в шаблоне: {wb.sheetnames}")

            sheet_mapping = {
                'IP': 'IP-адрес',
                'DNS': 'DNS',
                'URI': 'DNS',
                'Email': 'E-mail',
                'SHA256': 'SHA256',
                'SHA1': 'SHA1',
                'MD5': 'MD5',
                'File': 'Файл',
                'Registry': 'Реестр'
            }

            sheet_data = {}

            log(f"   • Обработка IOC данных...")
            for ioc_type, ioc_list in ioc_data.items():
                if not ioc_list:
                    log(f"      - {ioc_type}: пусто")
                    continue

                log(f"      - {ioc_type}: {len(ioc_list)} записей")
                for original, cleaned, metadata in ioc_list:
                    target_sheet = sheet_mapping.get(ioc_type)
                    filter_value = cleaned

                    if ioc_type == 'URI':
                        try:
                            parsed = urlparse(cleaned if cleaned.startswith('http') else 'http://' + cleaned)
                            domain = parsed.netloc or parsed.path.split('/')[0]
                            filter_value = domain

                            if self._is_ip_address(filter_value):
                                target_sheet = 'IP-адрес'
                                log(f"        URI {cleaned} -> IP-адрес ({filter_value})")
                        except:
                            filter_value = cleaned

                    elif ioc_type == 'DNS':
                        filter_value = cleaned.replace('[.]', '.').replace('[', '').replace(']', '')

                    elif ioc_type == 'Email':
                        filter_value = cleaned.replace('[.]', '.').replace('[', '').replace(']', '')

                    elif ioc_type == 'IP':
                        filter_value = cleaned.replace('[.]', '.').replace('[', '').replace(']', '')

                    if target_sheet:
                        if target_sheet not in sheet_data:
                            sheet_data[target_sheet] = []
                        sheet_data[target_sheet].append(filter_value)

            log(f"   • Распределение по листам:")
            for sheet_name, ioc_list in sheet_data.items():
                log(f"      - {sheet_name}: {len(ioc_list)} записей")

            log(f"   • Запись IOC в листы...")
            for sheet_name, ioc_list in sheet_data.items():
                if sheet_name in wb.sheetnames:
                    ws = wb[sheet_name]
                    for idx, ioc in enumerate(ioc_list, start=2):
                        ws.cell(row=idx, column=2, value=ioc)
                    log(f"      ✓ {sheet_name}: записано {len(ioc_list)} записей")
                else:
                    log(f"      ✗ {sheet_name}: лист не найден в шаблоне!")

            log(f"   • Сохранение файла: {output_path}")
            wb.save(output_path)
            log(f"   ✓ Файл фильтров успешно создан")
            return True

        except Exception as e:
            print(f"Ошибка при генерации фильтров: {e}")
            return False

    def _is_ip_address(self, value: str) -> bool:
        """Проверяет, является ли строка IP-адресом."""
        try:
            import socket
            socket.inet_aton(value)
            return True
        except:
            return False