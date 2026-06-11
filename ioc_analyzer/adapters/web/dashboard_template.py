"""
HTML template for the FastAPI monitoring dashboard.
"""

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>IOC-Analyzer — Панель мониторинга</title>
    <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg-primary: #090d16;
            --bg-secondary: #0f172a;
            --bg-card: rgba(30, 41, 59, 0.4);
            --border-color: rgba(255, 255, 255, 0.08);
            --text-primary: #f8fafc;
            --text-secondary: #94a3b8;
            --accent: #38bdf8;
            --accent-hover: #0ea5e9;
            --success: #10b981;
        }
        body {
            font-family: 'Outfit', sans-serif;
            background-color: var(--bg-primary);
            background-image: 
                radial-gradient(at 0% 0%, rgba(56, 189, 248, 0.08) 0px, transparent 50%),
                radial-gradient(at 100% 100%, rgba(16, 185, 129, 0.05) 0px, transparent 50%);
            color: var(--text-primary);
            margin: 0;
            padding: 30px;
            min-height: 100vh;
            box-sizing: border-box;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
        }
        header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-bottom: 1px solid var(--border-color);
            padding-bottom: 20px;
            margin-bottom: 30px;
        }
        h1 {
            margin: 0;
            font-size: 26px;
            font-weight: 600;
            letter-spacing: -0.5px;
            background: linear-gradient(to right, #38bdf8, #818cf8);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        .badge {
            background: rgba(16, 185, 129, 0.15);
            color: var(--success);
            border: 1px solid rgba(16, 185, 129, 0.3);
            padding: 6px 16px;
            border-radius: 30px;
            font-size: 14px;
            font-weight: 500;
            display: inline-flex;
            align-items: center;
            gap: 6px;
        }
        .badge::before {
            content: '';
            display: inline-block;
            width: 8px;
            height: 8px;
            background-color: var(--success);
            border-radius: 50%;
            box-shadow: 0 0 8px var(--success);
        }
        .grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 24px;
            margin-bottom: 24px;
        }
        @media (max-width: 768px) {
            .grid { grid-template-columns: 1fr; }
        }
        .card {
            background: var(--bg-card);
            backdrop-filter: blur(16px);
            border: 1px solid var(--border-color);
            border-radius: 16px;
            padding: 24px;
            box-shadow: 0 10px 30px -10px rgba(0, 0, 0, 0.5);
            transition: transform 0.2s, border-color 0.2s;
        }
        .card:hover {
            border-color: rgba(56, 189, 248, 0.2);
        }
        .card h2 {
            margin-top: 0;
            font-size: 18px;
            font-weight: 500;
            color: var(--text-secondary);
            border-bottom: 1px solid var(--border-color);
            padding-bottom: 12px;
            margin-bottom: 16px;
        }
        .card-body p {
            margin: 10px 0;
            font-size: 15px;
            color: var(--text-primary);
        }
        .card-body strong {
            color: var(--accent);
        }
        pre {
            background-color: rgba(2, 6, 23, 0.8);
            padding: 16px;
            border-radius: 10px;
            overflow-x: auto;
            font-family: 'Consolas', 'Courier New', monospace;
            font-size: 13px;
            line-height: 1.5;
            max-height: 400px;
            border: 1px solid var(--border-color);
            color: #e2e8f0;
            margin: 0;
        }
        .btn {
            background-color: var(--accent);
            color: #0f172a;
            border: none;
            padding: 10px 20px;
            border-radius: 8px;
            cursor: pointer;
            font-weight: 600;
            font-size: 14px;
            transition: background-color 0.2s, transform 0.1s;
            margin-top: 10px;
        }
        .btn:hover {
            background-color: var(--accent-hover);
        }
        .btn:active {
            transform: scale(0.98);
        }
        ul {
            padding-left: 20px;
            margin: 10px 0;
        }
        li {
            margin-bottom: 6px;
            color: var(--text-primary);
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>IOC-Analyzer — Панель мониторинга</h1>
            <span class="badge" id="status-badge">Служба активна</span>
        </header>
        
        <div class="grid">
            <div class="card">
                <h2>Статус и службы</h2>
                <div class="card-body">
                    <p>Режим работы демона: <strong>Daemon (Exchange EWS)</strong></p>
                    <p>Интервал проверки почты: <strong id="daemon-interval">300 сек</strong></p>
                    <p>Сетевая шара экспорта: <strong id="share-path">...</strong></p>
                    <button class="btn" onclick="refreshData()">Обновить данные</button>
                </div>
            </div>
            <div class="card">
                <h2>Активные листы IOC</h2>
                <div class="card-body" id="config-summary">Загрузка конфигурации...</div>
            </div>
        </div>
        
        <div class="card" style="margin-bottom: 30px;">
            <h2>Последние системные события (Лог daemon)</h2>
            <pre id="logs-container">Загрузка логов...</pre>
        </div>
    </div>
    
    <script>
        async function refreshData() {
            try {
                const logsRes = await fetch('/api/logs');
                const logsData = await logsRes.json();
                document.getElementById('logs-container').innerText = logsData.logs;
                
                const statusRes = await fetch('/api/status');
                const statusData = await statusRes.json();
                document.getElementById('share-path').innerText = statusData.share_path || 'Не настроен';
                document.getElementById('daemon-interval').innerText = (statusData.interval || 300) + ' сек';
            } catch (err) {
                console.error("Ошибка обновления дашборда:", err);
            }
        }
        
        async function loadConfig() {
            try {
                const configRes = await fetch('/api/config');
                const configData = await configRes.json();
                let html = '<ul>';
                (configData.ioc_config || []).forEach(cfg => {
                    html += `<li><strong>${cfg.name}</strong> (${cfg.report_type}): ${cfg.enabled ? '🟢 Включен' : '🔴 Выключен'}</li>`;
                });
                html += '</ul>';
                document.getElementById('config-summary').innerHTML = html;
            } catch (err) {
                document.getElementById('config-summary').innerText = "Ошибка загрузки конфигурации";
            }
        }
        
        // Запуск
        loadConfig();
        refreshData();
        setInterval(refreshData, 5000);
    </script>
</body>
</html>
"""
