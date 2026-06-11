import uvicorn

if __name__ == "__main__":
    print("Запуск панели мониторинга IOC-Analyzer на http://localhost:8000")
    uvicorn.run("ioc_analyzer.adapters.web.web_dashboard:app", host="0.0.0.0", port=8000, reload=True)
