import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "app.api.serv:app",
        host="0.0.0.0",
        port=5000,
        log_level="info",
        reload=True,
        reload_includes=["*.py", "*.yaml", "*.yml"],  # Include YAML files in reload pattern
        reload_dirs=["app", "lib", "config"],  # Watch both app and config directories
    )
