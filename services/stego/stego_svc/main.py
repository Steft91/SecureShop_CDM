from fastapi import FastAPI
from stego_svc.config import Settings, load_settings
from stego_svc.routes import router
from shared.service_auth import ServiceAuth
from shared.web import create_base_app

def create_app(settings: Settings | None = None, *, service_auth: ServiceAuth | None = None):
    settings = settings or load_settings()
    app = create_base_app(
        title="stego",
        settings=settings,
        engine=None,
        service_auth=service_auth or ServiceAuth.from_secrets("stego"),
    )
    app.include_router(router)
    return app

app = create_app()
