"""
Модуль для построения SIEM/NAD-запросов по шаблонам.
"""

import re
from typing import Any
from ioc_analyzer.core.parser.cleaner import is_ip_address, smart_clean_uri
from ioc_analyzer.core.models import IOC


def build_query(template: str, ioc_values: list[str], join_op: str) -> str:
    """
    Формирует запрос из шаблона и списка значений IOC (field in ["v1", "v2"]).
    """
    if not ioc_values:
        return ""
    # Пытаемся извлечь имя поля, например src.ip из src.ip = "{ioc}"
    m = re.match(
        r'^(.+?)\s*(?:={1,2}|!=|<>|CONTAINS|contains|LIKE|like|~|IN|in)\s*"\{ioc\}"$', 
        template
    )
    if not m:
        m = re.match(r'^(.+?)\s+"\{ioc\}"$', template)
        
    if m:
        field = m.group(1).rstrip()
        values_str = ", ".join(f'"{v}"' for v in ioc_values)
        return f'{field} in [{values_str}]'
        
    # Резервный вариант: объединяем отдельные шаблоны
    queries = [template.replace('{ioc}', ioc) for ioc in ioc_values]
    return join_op.join(queries)


def generate_query_data(
    indicators: list[IOC], 
    ioc_config: list[dict[str, Any]], 
    uri_clean_mode: str = "domain"
) -> list[dict[str, Any]]:
    """
    Генерирует данные запросов для отображения в GUI и экспорта в фильтры.
    """
    # Распределяем по группам
    merged_data: dict[str, list[str]] = {}
    for ioc in indicators:
        if ioc.ioc_type == 'URI':
            # Перенаправляем URI в IP или DNS
            try:
                from urllib.parse import urlparse
                parsed = urlparse(
                    ioc.clean_value if ioc.clean_value.startswith('http') 
                    else 'http://' + ioc.clean_value
                )
                domain = parsed.netloc or parsed.path.split('/')[0]
            except:
                domain = ioc.clean_value

            if is_ip_address(domain):
                merged_data.setdefault('IP', []).append(domain)
            else:
                merged_data.setdefault('DNS', []).append(domain)
        else:
            merged_data.setdefault(ioc.ioc_type, []).append(ioc.clean_value)

    # Дедупликация
    for key in merged_data:
        merged_data[key] = sorted(list(set(merged_data[key])))

    config_by_name = {cfg['name']: cfg for cfg in ioc_config if cfg.get('enabled', False)}
    type_template_sources: dict[str, list[str]] = {}
    
    for cfg in ioc_config:
        if not cfg.get('enabled', False):
            continue
        name = cfg['name']
        if name == 'URI':
            type_template_sources.setdefault('DNS', []).append(name)
        else:
            type_template_sources.setdefault(name, []).append(name)

    query_data = []
    for cfg in ioc_config:
        if not cfg.get('enabled', False):
            continue

        name = cfg['name']
        if name == 'URI':
            continue

        if name not in merged_data or not merged_data[name]:
            continue

        cleaned_iocs = merged_data[name]
        sources = type_template_sources.get(name, [name])
        mp10_templates = []
        nad_templates = []
        
        for src_name in sources:
            src_cfg = config_by_name.get(src_name, {})
            mp10_templates.extend(src_cfg.get('mp10_templates', []))
            nad_templates.extend(src_cfg.get('nad_templates', []))
            
        mp10_templates = list(dict.fromkeys(mp10_templates))
        nad_templates = list(dict.fromkeys(nad_templates))

        group_queries = []
        for tpl in mp10_templates:
            group_queries.append({
                'ioc_name': name, 'system': 'MP10',
                'query': build_query(tpl, cleaned_iocs, " OR "),
                'template': tpl,
                'join_op': ' OR ',
                'completed': False
            })

        for tpl in nad_templates:
            group_queries.append({
                'ioc_name': name, 'system': 'NAD',
                'query': build_query(tpl, cleaned_iocs, " || "),
                'template': tpl,
                'join_op': ' || ',
                'completed': False
            })

        if group_queries:
            query_data.append({
                'group_name': f"{name} ({cfg['report_type']})",
                'ioc_count': len(cleaned_iocs),
                'cleaned_iocs': cleaned_iocs,
                'queries': group_queries
            })

    return query_data
