from pathlib import Path
from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

def configure(app: FastAPI):
    static = Path(__file__).resolve().parent.parent / 'static'
    app.mount('/static', StaticFiles(directory=static), name='static')
    @app.get('/', include_in_schema=False)
    def home():
        return FileResponse(static / 'index.html')
    @app.get('/health')
    def health():
        return {'status': 'ok', 'data': 'synthetic-demo', 'version': '1.0.0'}
