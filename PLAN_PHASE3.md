# План реализации Фазы 3: Шаги 6, 7, 8 (Регламент для следующего ИИ-агента)

Этот документ содержит детальные инструкции, архитектурные чертежи и код для реализации шагов 6, 7 и 8 в проекте **IOC-Analyzer**. 

---

## 📅 Шаг 6. Доводка логики и проверка автотестов

Перед запуском убедитесь, что все 19 тестов в `1_project/tests/` проходят успешно:
```bash
python -m pytest tests/
```

### Важные нюансы логики для проверки на рабочем хосте:
1. **Права доступа к сетевой шаре**: Адаптер `LocalFSAdapter` (`local_fs_adapter.py`) должен корректно обрабатывать исключения `PermissionError` при попытке перезаписать занятый Excel-файл.
2. **Переменные окружения Exchange (EWS)**: Убедитесь, что переменная `EWS_PASSWORD` (или иная, заданная ключом `password_env_var` в `config.json`) корректно считывается адаптером `exchange_adapter.py`.

---

## 🖥️ Шаг 7. Веб-интерфейс мониторинга (Dashboard)

Необходимо создать легковесную веб-панель управления на базе **FastAPI** и **Uvicorn**, которая считывает лог-файлы и текущую конфигурацию, выводя красивую статистику.

### 7.1. Создание папки адаптера веб-интерфейса:
Создайте директорию `ioc_analyzer/adapters/web/` и пустой `__init__.py`.

### 7.2. Код Веб-дашборда `ioc_analyzer/adapters/web/web_dashboard.py`:
```python
import os
import json
import logging
from typing import Any, Dict
from fastapi import FastAPI
from fastapi.responses import HTMLResponse, JSONResponse
from ioc_analyzer.core.config_manager import ConfigManager

app = FastAPI(title="IOC-Analyzer Dashboard")
logger = logging.getLogger("ioc_analyzer.web")

# Пути к логам и конфигурации
CONFIG_PATH = "config.json"
LOG_FILE_PATH = "app.log"  # Или путь из настроек

def get_last_logs(num_lines: int = 100) -> str:
    if not os.path.exists(LOG_FILE_PATH):
        return "Файл логов еще не создан."
    try:
        with open(LOG_FILE_PATH, "r", encoding="utf-8", errors="ignore") as f:
            lines = f.readlines()
            return "".join(lines[-num_lines:])
    except Exception as e:
        return f"Не удалось прочитать логи: {e}"

@app.get("/", response_class=HTMLResponse)
async def get_dashboard():
    html_content = """
    <!DOCTYPE html>
    <html lang="ru">
    <head>
        <meta charset="UTF-8">
        <title>IOC-Analyzer Dashboard</title>
        <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600&display=swap" rel="stylesheet">
        <style>
            body {
                font-family: 'Outfit', sans-serif;
                background-color: #0f172a;
                color: #e2e8f0;
                margin: 0;
                padding: 20px;
            }
            .container {
                max-width: 1200px;
                margin: 0 auto;
            }
            header {
                display: flex;
                justify-content: space-between;
                align-items: center;
                border-bottom: 1px solid #1e293b;
                padding-bottom: 20px;
                margin-bottom: 30px;
            }
            h1 { margin: 0; font-size: 24px; font-weight: 600; color: #38bdf8; }
            .badge {
                background-color: #10b981;
                color: #ffffff;
                padding: 5px 12px;
                border-radius: 20px;
                font-size: 14px;
                font-weight: bold;
            }
            .grid {
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: 20px;
                margin-bottom: 30px;
            }
            .card {
                background: rgba(30, 41, 59, 0.7);
                backdrop-filter: blur(10px);
                border: 1px solid #334155;
                border-radius: 12px;
                padding: 20px;
            }
            .card h2 { margin-top: 0; font-size: 18px; color: #94a3b8; border-bottom: 1px solid #334155; padding-bottom: 10px; }
            pre {
                background-color: #020617;
                padding: 15px;
                border-radius: 8px;
                overflow-x: auto;
                font-family: monospace;
                font-size: 13px;
                max-height: 300px;
                border: 1px solid #1e293b;
            }
            .btn {
                background-color: #0284c7;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 6px;
                cursor: pointer;
                font-weight: 600;
                transition: background 0.2s;
            }
            .btn:hover { background-color: #0369a1; }
        </style>
    </head>
    <body>
        <div class="container">
            <header>
                <h1>IOC-Analyzer — Панель мониторинга сервера</h1>
                <span class="badge" id="status-badge">Активен</span>
            </header>
            
            <div class="grid">
                <div class="card">
                    <h2>Статус и Аптайм</h2>
                    <p>Режим работы: <strong id="work-mode">Daemon (Exchange EWS)</strong></p>
                    <p>Проверено писем: <strong id="processed-mails">0</strong></p>
                    <button class="btn" onclick="refreshData()">Обновить данные</button>
                </div>
                <div class="card">
                    <h2>Активная конфигурация</h2>
                    <div id="config-summary">Загрузка...</div>
                </div>
            </div>
            
            <div class="card" style="margin-bottom: 30px;">
                <h2>Последние системные события (Лог)</h2>
                <pre id="logs-container">Загрузка логов...</pre>
            </div>
        </div>
        
        <script>
            async function refreshData() {
                try {
                    const statusRes = await fetch('/api/status');
                    const statusData = await statusRes.json();
                    document.getElementById('processed-mails').innerText = statusData.processed_mails || 0;
                    
                    const logsRes = await fetch('/api/logs');
                    const logsData = await logsRes.json();
                    document.getElementById('logs-container').innerText = logsData.logs;
                } catch (err) {
                    console.error("Ошибка обновления дашборда:", err);
                }
            }
            
            async function loadConfig() {
                try {
                    const configRes = await fetch('/api/config');
                    const configData = await configRes.json();
                    let html = '<ul>';
                    configData.ioc_config.forEach(cfg => {
                        html += `<li><strong>${cfg.name}</strong>: ${cfg.enabled ? 'Включен' : 'Выключен'}</li>`;
                    });
                    html += '</ul>';
                    document.getElementById('config-summary').innerHTML = html;
                } catch (err) {
                    document.getElementById('config-summary').innerText = "Ошибка загрузки конфигурации";
                }
            }
            
            // Первоначальная загрузка
            loadConfig();
            refreshData();
            setInterval(refreshData, 5000); // автообновление каждые 5 сек
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)

@app.get("/api/status")
async def get_status():
    # Возвращает статус фонового процесса (можно проверять наличие lock-файла)
    return JSONResponse(content={
        "status": "running",
        "processed_mails": 0,  # Заглушка, можно считывать из файла состояния
        "uptime_seconds": 3600
    })

@app.get("/api/logs")
async def get_logs_endpoint():
    return JSONResponse(content={"logs": get_last_logs(100)})

@app.get("/api/config")
async def get_config_endpoint():
    manager = ConfigManager(CONFIG_PATH)
    return JSONResponse(content=manager.config_data)
```

### 7.3. Скрипт запуска `run_web.py`:
Создайте в корне `1_project/run_web.py` для запуска панели на порту 8000:
```python
import uvicorn

if __name__ == "__main__":
    print("Запуск панели мониторинга IOC-Analyzer на http://localhost:8000")
    uvicorn.run("ioc_analyzer.adapters.web.web_dashboard:app", host="0.0.0.0", port=8000, reload=True)
```

---

## 🐙 Шаг 8. Слияние Git-веток и вынос проекта в корень

Этот шаг должен быть выполнен аккуратно, чтобы сохранить историю коммитов.

### 8.1. Выполнение слияния (Git Merge)
Все действия выполняются внутри локального каталога `branch_main` (который настроен на ветку `main`):

```bash
# 1. Перейти в каталог branch_main
cd "d:\Рабочая Папка\ioc_parser_srv\branch_main"

# 2. Обновить информацию о всех ветках с сервера
git fetch --all

# 3. Слить поочередно все ветки в main (с фиксацией автокоммитов)
git merge origin/upd -m "Merge branch upd"
git merge origin/feature/server-mode-api-blocking -m "Merge branch feature/server-mode-api-blocking"
git merge origin/claude/review-project-mrNwv -m "Merge branch claude/review-project-mrNwv"
```
*(При возникновении конфликтов слияния — разрешайте их в пользу новой Hexagonal-структуры).*

### 8.2. Выгрузка нового парсера в корень ветки `main`
После завершения слияния веток:
1. Удалите старые legacy папки и файлы в корне `branch_main` (такие как `src/`, `main.py` и т.д.).
2. Скопируйте все содержимое папки `1_project/` (включая `ioc_analyzer/`, `docs/`, `tests/`, `run_*.py`, `config.json`, `agents.md`, `README.md` и т.д.) непосредственно в корень каталога `branch_main`.
3. Зарегистрируйте все изменения в git:
   ```bash
   git add .
   git commit -m "Refactor project to Hexagonal Architecture (v2.3) with FastAPI Dashboard and tests"
   git push origin main
   ```

### 8.3. Очистка рабочего каталога `ioc_parser_srv`
Теперь нужно превратить основной каталог `d:\Рабочая Папка\ioc_parser_srv\` в чистый репозиторий.

1. **Скопируйте** папку `.git` из `d:\Рабочая Папка\ioc_parser_srv\branch_main\` непосредственно в корень `d:\Рабочая Папка\ioc_parser_srv\`.
2. **Скопируйте** все файлы проекта (новые скрипты `run_*.py`, папку `ioc_analyzer`, `docs`, `tests`, `config.json`, `agents.md`) из `d:\Рабочая Папка\ioc_parser_srv\1_project\` в корень `d:\Рабочая Папка\ioc_parser_srv\`.
3. **Удалите** папки с временными ветками и промежуточными проектами:
   - `1_project`
   - `branch_main`
   - `branch_feature_server_mode`
   - `branch_upd`
   - `branch_claude_review`
4. **Оставьте нетронутыми**:
   - `.test_doc/` (папка с тестовыми бюллетенями для pytest).
5. **Проверка**:
   Запустите из корня рабочей папки:
   ```bash
   python -m pytest tests/
   python run_web.py
   python run_gui.py
   ```
   Вся система должна запускаться и проходить тесты на 100% прямо из корня репозитория.
