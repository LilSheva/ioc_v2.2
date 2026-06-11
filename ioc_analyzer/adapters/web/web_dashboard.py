import os
import json
import logging
from typing import Any, Dict
from fastapi import FastAPI
from fastapi.responses import HTMLResponse, JSONResponse
from ioc_analyzer.core.config_manager import ConfigManager
from ioc_analyzer.adapters.web.dashboard_template import HTML_TEMPLATE

app = FastAPI(title="IOC-Analyzer Monitor")
logger = logging.getLogger("ioc_analyzer.web")

CONFIG_PATH = "config.json"
LOG_FILE_PATH = "app.log"

def get_last_logs(num_lines: int = 100) -> str:
    if not os.path.exists(LOG_FILE_PATH):
        return "Файл логов (app.log) еще не создан фоновым демоном."
    try:
        with open(LOG_FILE_PATH, "r", encoding="utf-8", errors="ignore") as f:
            lines = f.readlines()
            return "".join(lines[-num_lines:])
    except Exception as e:
        return f"Не удалось прочитать логи: {e}"

@app.get("/", response_class=HTMLResponse)
async def get_dashboard():
    return HTMLResponse(content=HTML_TEMPLATE)

@app.get("/api/status")
async def get_status():
    manager = ConfigManager(CONFIG_PATH)
    config = manager.config_data
    return JSONResponse(content={
        "status": "running",
        "share_path": config.get("network_share_path", ""),
        "interval": config.get("daemon_interval_seconds", 300),
    })

@app.get("/api/logs")
async def get_logs_endpoint():
    return JSONResponse(content={"logs": get_last_logs(100)})

@app.get("/api/config")
async def get_config_endpoint():
    manager = ConfigManager(CONFIG_PATH)
    return JSONResponse(content=manager.config_data)
