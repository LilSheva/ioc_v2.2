# План доработки IOC Parser v2.2 — трекинг сессии

## Статус: ✅ Реализовано (требует тестирования на реальных документах)

---

## Контекст проекта

GUI-утилита на Python (ttkbootstrap/tkinter) для парсинга IOC из .docx файлов.
Режимы: ФСТЕК и ГосСОПКА. Типы IOC: IP, DNS, URI, File, Email, SHA256, SHA1, MD5, Registry.

Ключевые файлы:
- `src/model/ioc_parser_v21_fixed.py` — парсер IOC, метод `find_all_raw_matches`
- `src/model/config_manager.py` — конфиг (`DEFAULT_CONFIG`), `save_config`, `_load_config`
- `src/controller/app_controller.py` — контроллер, `process_files`, `generate_reports`
- `src/view/tabs/main_tab.py` — главная вкладка, диалог результатов (`_generate_reports`)
- `src/view/tabs/ip_tab.py` — вкладка IP управления
- `src/view/tabs/settings_tab.py` — вкладка настроек IOC

---

## Задачи

### ✅ / ❌ / 🔄 / ⚠️ — готово / не начато / в работе / требует уточнения

---

### 1. Фикс бага: email `abc.qwe.zxc@mail[.]ru` разбивается на домен + email
**Статус:** ✅ Реализована защитная мера + требует тестирования

**Что сделано:**
- В `find_all_raw_matches` все матчи email обрабатываются через `sorted(set(matches), key=len, reverse=True)` — длинные матчи обрабатываются первыми
- Добавлена проверка `if match not in working_text: continue` — пропускаем матч если он уже был заменён пробелами (как часть более длинного)
- Переход на `finditer` + позиционная замена для IP, DNS, хешей

**Требует:** тестирования на реальном документе с `abc.qwe.zxc@mail[.]ru`

---

### 2. API: хранение URL и ключа в конфиге, без шифрования
**Статус:** ✅ Реализовано

- `config_manager.py`: `api_url` и `api_key` на верхнем уровне JSON-конфига
- `app_controller.py`: `get_api_url/set_api_url/get_api_key/set_api_key`
- `_load_config` читает api_url/api_key из файла, `save_config` сохраняет
- В GUI не отображается

---

### 3. Модуль отправки IP на API
**Статус:** ✅ Реализовано

Файл: `src/model/api_sender.py`
- `send_to_api(ip_list, source_name, api_url, api_key)`
- Статусы: OK, ERROR_DUPLICATE, ERROR_DENY_NET, прочие
- try/except ConnectionError, Timeout, HTTPError

---

### 4. Blacklist и Exclusions для всех типов IOC
**Статус:** ✅ Реализовано

- `DEFAULT_CONFIG`: добавлены `blacklist: []` и `exclusions: []` ко всем типам кроме File
- `_migrate_ioc_fields()`: при загрузке старого конфига добавляет пустые поля
- Парсер: `_get_ioc_filters(ioc_name)`, `_passes_filters(...)`, `_extract_with_finditer(...)`
- IP, DNS, хеши: finditer + позиционная замена справа налево + фильтрация
- Email: sorted by length desc + проверка blacklist/exclusions
- URI: позиционная замена уже была, добавлена фильтрация
- File: без изменений (использует file_blacklist/filename_exclusions)
- `settings_tab.py`: UI-редактор для blacklist/exclusions (аналогично MP10/NAD)
- `_save_config`: сохраняет blacklist/exclusions для не-File типов; file_blacklist/filename_exclusions для File

---

### 5. Улучшение финального диалога "Отчёты созданы"
**Статус:** ✅ Реализовано

`main_tab.py` → `_generate_reports`:
- Строка про BDU-файл (если создан)
- Кол-во IP на блокировку + подсказка перейти на вкладку
- Предупреждение про IP на разблокировку (если ГосСОПКА)

---

### 6. Предупреждение в IP-вкладке (секция разблокировки)
**Статус:** ✅ Реализовано

`ip_tab.py` → `_create_unblock_section`: добавлен Label с текстом про ручную разблокировку

---

## Порядок выполнения

1 → 2 → 3 → 4 → 5 → 6

Задачи 2 и 3 связаны (конфиг нужен для sender'а).
Задача 1 независима, можно делать в любом порядке.

---

## Заметки

- Проект собирается в `.exe` через PyInstaller — не использовать сторонние крипто-библиотеки
- `requests` уже есть в зависимостях (используется в проекте)
- GUI: ttkbootstrap поверх tkinter
- Конфиг сохраняется в `ioc_parser_settings.json` рядом с `.exe`
