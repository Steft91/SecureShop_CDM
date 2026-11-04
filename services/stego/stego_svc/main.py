from fastapi import FastAPI
from stego_svc.config import Settings, load_settings
from stego_svc.routes import router

def create_app(settings: Settings | None = None, **_):
    app = FastAPI(title="stego")
    app.state.settings = settings or load_settings()
    app.include_router(router)
    @app.get("/health")
    def health(): return {"status": "ok"}
    return app

app = create_app()
