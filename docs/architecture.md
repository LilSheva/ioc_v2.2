# Архитектура системы: Ports & Adapters (Гексагональная архитектура)

Этот документ описывает архитектурный дизайн системы **IOC-Analyzer**, принципы слабой связанности компонентов, управление конфигурацией и потоки данных.

---

## 1. Концепция и правила зависимостей

В основе проекта лежит **Гексагональная архитектура** (также известная как паттерн "Порты и Адаптеры"). Основная цель этого подхода — изолировать бизнес-логику (Ядро) от внешних технологических деталей (баз данных, почтовых серверов, библиотек отрисовки интерфейса, сетевых протоколов).

```
   ┌─────────────────────────────────────────────────────────┐
   │                       Адаптеры                          │
   │   ┌─────────────────────────────────────────────────┐   │
   │   │                    Порты                        │   │
   │   │   ┌─────────────────────────────────────────┐   │   │
   │   │   │                Ядро                     │   │   │
   │   │   │   ┌─────────────────────────────────┐   │   │   │
   │   │   │   │ - Domain Models (models.py)     │   │   │   │
   │   │   │   │ - IOC Parsing (parser/)         │   │   │   │
   │   │   │   │ - Config Manager               │   │   │   │
   │   │   │   │ - AppService (service.py)       │   │   │   │
   │   │   │   └─────────────────────────────────┘   │   │   │
   │   │   │          (Pure Python, no deps)         │   │   │
   │   │   └─────────────────────────────────────────┘   │   │
   │   │     - DocumentPort (Абстрактные             │   │   │
   │   │     - MailPort      контракты ABC)          │   │   │
   │   │     - ExportPort                            │   │   │
   │   │     - SiemPort                              │   │   │
   │   └─────────────────────────────────────────────────┘   │
   │     - docx_adapter.py (python-docx)                     │
   │     - exchange_adapter.py (exchangelib)                 │
   │     - local_fs_adapter.py (openpyxl)                    │
   │     - api_adapter.py (requests)                         │
   │     - tkinter_gui.py (ttkbootstrap)                     │
   └─────────────────────────────────────────────────────────┘
```

### Главный закон архитектуры:
**Ядро никогда не импортирует и не вызывает напрямую код из слоя Адаптеров.**
* Зависимости направлены **внутрь**: Адаптеры знают о Портах и Ядре. Порты знают о моделях Ядра. Ядро знает только о своих внутренних структурах и Портах (через абстрактные интерфейсы).
* Пример: Ядру необходимо сохранить отчет на диск. Оно не вызывает `openpyxl`. Вместо этого оно вызывает метод `export_report` у интерфейса `ExportPort`. Конкретная реализация `LocalFSAdapter` инжектируется в конструктор сервиса ядра на этапе сборки (Dependency Injection).

---

## 2. Структура директорий и модулей

Каталог [1_project/ioc_analyzer/](file:///d:/Рабочая Папка/ioc_parser_srv/1_project/ioc_analyzer/) делится на:

### 2.1. [core/ (Бизнес-логика)](file:///d:/Рабочая Папка/ioc_parser_srv/1_project/ioc_analyzer/core/)
* [models.py](file:///d:/Рабочая Папка/ioc_parser_srv/1_project/ioc_analyzer/core/models.py) — чистые структуры данных (доменные модели). Не содержат логики ввода-вывода.
* [config_manager.py](file:///d:/Рабочая Папка/ioc_parser_srv/1_project/ioc_analyzer/core/config_manager.py) — управление параметрами приложения, разбор RegExp, слияние настроек.
* [query_builder.py](file:///d:/Рабочая Папка/ioc_parser_srv/1_project/ioc_analyzer/core/query_builder.py) — логика трансляции списков IOC в поисковые запросы для MP10 и NAD.
* [service.py](file:///d:/Рабочая Папка/ioc_parser_srv/1_project/ioc_analyzer/core/service.py) — координатор (`AppService`). Принимает порты в конструкторе, управляет логикой разбора почты, выгрузки отчетов и отправки в SIEM.
* [parser/](file:///d:/Рабочая Папка/ioc_parser_srv/1_project/ioc_analyzer/core/parser/) — логика RegExp-анализа (разбита на `base_parser.py`, `cleaner.py`, `fstek_parser.py`, `gossopka_parser.py`).

### 2.2. [ports/ (Абстрактные контракты)](file:///d:/Рабочая Папка/ioc_parser_srv/1_project/ioc_analyzer/ports/)
Содержит классы-интерфейсы на базе `abc.ABC`. Каждый порт декларирует методы, которые адаптер обязан реализовать:
* `DocumentPort` (чтение файлов).
* `MailPort` (проверка почты Exchange).
* `ExportPort` (генерация xlsx/csv).
* `SiemPort` (отправка данных в SIEM).

### 2.3. [adapters/ (Реализация интеграций)](file:///d:/Рабочая Папка/ioc_parser_srv/1_project/ioc_analyzer/adapters/)
* `document/docx_adapter.py` — обертка над `python-docx` для парсинга структуры абзацев Word.
* `mail/exchange_adapter.py` — клиент Exchange на базе `exchangelib`.
* `export/local_fs_adapter.py` — координатор создания отчетов. Вызывает вспомогательные модули `excel_report.py`, `excel_filters.py`, `csv_report.py` (с использованием `openpyxl`).
* `siem/api_adapter.py` / `mock_siem.py` — адаптеры для отправки IOC по REST API в SIEM.
* `gui/tkinter_gui.py` — графический интерфейс на `ttkbootstrap`.

---

## 3. Внедрение зависимостей (Dependency Injection)

Связывание (wiring) компонентов происходит в точках входа:
* Для автоматической службы (Daemon): [run_daemon.py](file:///d:/Рабочая Папка/ioc_parser_srv/1_project/run_daemon.py)
* Для ручной обработки (GUI): [run_gui.py](file:///d:/Рабочая Папка/ioc_parser_srv/1_project/run_gui.py)

В конструктор `AppService` передаются конкретные экземпляры адаптеров. Это позволяет легко переключаться между живыми системами и моками при тестировании:

```python
# Пример сборки (run_daemon.py / run_gui.py)
app_service = AppService(
    doc_reader=DocxAdapter(),
    mail_reader=ExchangeAdapter(...),
    exporter=LocalFSAdapter(...),
    siem_client=SiemApiAdapter(...),
    settings=config_data
)
```

---

## 4. Схема потока данных (Data Flow)

### 4.1. Автоматический поток (Daemon Mode)
1. Демон запускает бесконечный цикл с таймером сна.
2. `AppService` вызывает `MailPort.fetch_unread_emails()`.
3. Адаптер почты скачивает вложения (`.docx` бюллетени) во временную папку и возвращает структуру `EmailRecord`.
4. Для каждого вложения `AppService` вызывает `DocumentPort.extract_paragraphs()`, получая текст и XML-свойства структуры абзацев.
5. Данные передаются в парсеры ядра (`FstekParser` или `GossopkaParser`).
6. Парсер возвращает очищенные структуры `IOC` с определенными статусами (`block`/`search`/`unblock`).
7. `AppService` вызывает `ExportPort.export_report()` для создания XLSX отчетов и CSV списков в сетевой папке.
8. `AppService` отправляет извлеченные индикаторы в SIEM через `SiemPort.push_indicators()`.
9. `AppService` помечает обработанные письма как прочитанные через `MailPort.mark_as_read()`.

### 4.2. Ручной поток (GUI Mode)
1. Пользователь выбирает файлы в GUI.
2. GUI вызывает парсинг этих файлов через `AppService.parse_local_file()`.
3. Результаты отображаются на вкладках GUI (списки IOC, поисковые запросы, IP для МСЭ).
4. Пользователь нажимает "Сформировать отчеты", GUI вызывает экспорт через `AppService.exporter.export_report()`.
