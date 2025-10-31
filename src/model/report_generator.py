"""
Модуль для генерации отчетов V2.1 FINAL.
Новая структура: 10 столбцов, объединение запросов через OR/||
ИСПРАВЛЕНИЯ:
- Добавлен импорт 're'.
- Исправлена очистка переносов строк для имен файлов.
- Добавлено форматирование и выравнивание столбцов в Excel.
"""

import re # <<< ИЗМЕНЕНИЕ: ДОБАВЛЕН ИМПОРТ
import os
from typing import Dict, List, Any, Tuple
from urllib.parse import urlparse
from datetime import datetime
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side


class ReportGenerator:
    """Генератор отчетов IOC V2.1 FINAL."""
    
    def __init__(self, ioc_config: List[Dict[str, Any]]):
        """Инициализация генератора отчетов."""
        self.ioc_config = ioc_config
    
    def _smart_clean_uri(self, uris: List[Tuple[str, str]]) -> Dict[str, str]:
        """
        "Умная" очистка URI: сокращает до уникального префикса для одинаковых доменов.
        """
        domain_groups = {}
        for original, cleaned in uris:
            try:
                parsed = urlparse(cleaned if cleaned.startswith('http') else 'http://' + cleaned)
                domain = parsed.netloc or parsed.path.split('/')[0]
                if domain not in domain_groups:
                    domain_groups[domain] = []
                domain_groups[domain].append(cleaned)
            except:
                domain_groups[cleaned] = [cleaned]
        
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
    
    def generate_xlsx_report(self, ioc_data: Dict[str, List[Tuple[str, str]]], 
                            output_path: str, bulletin: str = "") -> bool:
        """
        Генерирует форматированный .xlsx отчет с 10 столбцами.
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
            event_type = "Фишинговая рассылка электронной почты. Вредоносные вложения"

            for ioc_config in self.ioc_config:
                if not ioc_config.get('enabled', False):
                    continue

                name = ioc_config['name']
                if name in ioc_data and ioc_data[name]:
                    report_type = ioc_config['report_type']
                    nta_status = ioc_config['nta_status']
                    siem_tools_status = ioc_config['siem_tools_status']
                    siem_status = ioc_config['siem_status']

                    for original, cleaned in ioc_data[name]:
                        display_original = original
                        if name == 'File':
                            display_original = re.sub(r'\s+', ' ', original)

                        ioc_display = cleaned
                        if name == 'URI' and cleaned in uri_smart_map:
                            ioc_display = uri_smart_map[cleaned]

                        row_data = [
                            counter, today_date, nta_status, siem_tools_status,
                            siem_status, report_type, display_original,
                            ioc_display, bulletin, event_type
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
    
    def generate_queries_report(self, ioc_data: Dict[str, List[Tuple[str, str]]], 
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
                    
                    cleaned_iocs = [cleaned for _, cleaned in ioc_data[name]]
                    
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
    
    def generate_query_data(self, ioc_data: Dict[str, List[Tuple[str, str]]]) -> List[Dict[str, Any]]:
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
                cleaned_iocs = [cleaned for _, cleaned in ioc_data[name]]
                
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