# Нюансы реализации: Адаптеры (Adapters Layer)

Этот документ содержит технические детали и спецификацию внешних интеграций, расположенных в директории [ioc_analyzer/adapters/](file:///d:/Рабочая Папка/ioc_parser_srv/1_project/ioc_analyzer/adapters/).

---

## 1. Чтение документов: DocxAdapter ([adapters/document/docx_adapter.py](file:///d:/Рабочая Папка/ioc_parser_srv/1_project/ioc_analyzer/adapters/document/docx_adapter.py))

* **Библиотека**: `python-docx`
* **Извлечение границ абзацев для ГосСОПКА**:
  - Для детекции визуальных разделителей (горизонтальных линий) адаптер исследует XML-структуру свойств абзаца (`w:pPr`).
  - Метод проверяет наличие элемента границ `w:pBdr` и его дочерних элементов `w:top` или `w:bottom`.
  - Если такие элементы найдены, устанавливаются флаги `has_top_border` или `has_bottom_border` в возвращаемой структуре `ParagraphData`. Это позволяет делить бюллетень ГосСОПКА на изолированные секции.

---

## 2. Работа с почтой: ExchangeAdapter ([adapters/mail/exchange_adapter.py](file:///d:/Рабочая Папка/ioc_parser_srv/1_project/ioc_analyzer/adapters/mail/exchange_adapter.py))

* **Библиотека**: `exchangelib` (взамен старого `win32com.client` и Outlook COM Automation).
* **Схема подключения**:
  - Подключение настраивается через конфигурационные параметры почтового сервера: email, username, server.
  - Пароль извлекается из переменной окружения, имя которой задано в конфиге ключом `"password_env_var"` (по умолчанию `EWS_PASSWORD`).
* **Абстракция и работа с ID писем**:
  - Exchange Web Services (EWS) идентифицирует письма через составной ключ: уникальный `item.id` и динамический `item.changekey` (меняющийся при каждом изменении объекта).
  - В доменную модель `EmailRecord` адаптер передает поле `mail_id` в виде составной строки: `"{item.id}:{item.changekey}"`.
  - При вызове метода `mark_as_read(mail_id)` адаптер:
    1. Парсит строку `mail_id`, разбивая её по символу `:`.
    2. Извлекает объект сообщения из папки Exchange по `id` и `changekey`.
    3. Устанавливает свойство `is_read = True`.
    4. Сохраняет изменения на сервере Exchange с помощью `save(update_fields=['is_read'])`.

---

## 3. Экспорт данных: LocalFSAdapter ([adapters/export/](file:///d:/Рабочая Папка/ioc_parser_srv/1_project/ioc_analyzer/adapters/export/))

Экспорт отчетов разделен на три вспомогательных модуля:
1. **[excel_report.py](file:///d:/Рабочая Папка/ioc_parser_srv/1_project/ioc_analyzer/adapters/export/excel_report.py)** — генерация основного отчета со всеми IOC, их статусами и контекстом.
2. **[excel_filters.py](file:///d:/Рабочая Папка/ioc_parser_srv/1_project/ioc_analyzer/adapters/export/excel_filters.py)** — таблица поисковых запросов для MP10 и NAD.
3. **[csv_report.py](file:///d:/Рабочая Папка/ioc_parser_srv/1_project/ioc_analyzer/adapters/export/csv_report.py)** — простые списки (TXT/CSV) для заливки на межсетевые экраны.

### Особенности реализации экспорта:
* **Дизайн таблиц**: Стилизация выполняется с помощью `openpyxl`. Используются современные шрифты (Outfit / Inter) и гармоничные цветовые схемы (темно-серый заголовок, чередующиеся цвета строк HSL, четкие границы).
* **Блокировки и защита от сбоев**:
  - Если результирующий Excel-файл уже открыт аналитиком в MS Excel, операционная система заблокирует его для перезаписи.
  - Адаптер `LocalFSAdapter` реализует логику **безопасных попыток записи с таймаутом** (safe write retries). При возникновении ошибки `PermissionError` адаптер делает до 5 попыток с интервалом в 1 секунду. Если файл так и не освободился, пользователю выводится информативное окно с просьбой закрыть документ.

---

## 4. Сайт блокировки IP: IpBlockApiAdapter ([adapters/ip_block/api_adapter.py](file:///d:/Рабочая Папка/ioc_parser_srv/1_project/ioc_analyzer/adapters/ip_block/api_adapter.py))

* **Библиотека**: `requests`
* **Принцип**: POST `[{"ip": "...", "comment": "..."}]` на `api_url` из `config.json`, заголовок `X-API-KEY: api_key`.
* **Ответ**: список `{"id"|"ip", "status", "text"}` — маппится в per-IP статусы для GUI.
* **Не путать с SIEM**: это отдельный внешний сервис блокировки IP, логика перенесена из legacy `api_sender.py`.

---

## 5. Графический интерфейс: TkinterGUI ([adapters/gui/](file:///d:/Рабочая Папка/ioc_parser_srv/1_project/ioc_analyzer/adapters/gui/))

Графический интерфейс спроектирован на базе библиотеки `ttkbootstrap` (надстройка над `tkinter`, дающая современный плоский дизайн и готовую темную тему оформления).

### Дробление для соблюдения лимита < 250 строк:
Главный класс [tkinter_gui.py](file:///d:/Рабочая Папка/ioc_parser_srv/1_project/ioc_analyzer/adapters/gui/tkinter_gui.py) собирает интерфейс из отдельных вкладок (Tabs), расположенных в папке [gui/tabs/](file:///d:/Рабочая Папка/ioc_parser_srv/1_project/ioc_analyzer/adapters/gui/tabs/):
* **`main_tab.py`** — выбор файлов и запуск генерации отчетов (логика кликов вынесена в `main_actions.py`).
* **`ip_tab.py`** — отображение списков IP-адресов на блокировку и разблокировку (сплит с `ip_sections.py`).
* **`results_tab.py`** — отображение MP10 и NAD поисковых строк (сплит с `results_sections.py`).
* **`settings_tab.py`** — управление RegExp-выражениями индикаторов и их сохранение в `config.json` (сплит с `settings_widgets.py`).
* **`info_tab.py`** — встроенная инструкция пользователя.

Такое разделение позволяет поддерживать чистоту кода и легко ориентироваться в UI-компонентах.
