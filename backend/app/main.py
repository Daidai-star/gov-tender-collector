from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.core.config import get_settings
from app.core.database import SessionLocal
from app.core.init_db import ensure_seed_roles_and_admin, init_db

settings = get_settings()
app = FastAPI(title=settings.app_name)

app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)


@app.on_event('startup')
def startup_event() -> None:
    init_db()
    db = SessionLocal()
    try:
        ensure_seed_roles_and_admin(db, settings.seed_admin_username, settings.seed_admin_password)
    finally:
        db.close()


@app.get('/healthz')
def healthz():
    return {'status': 'ok'}


app.include_router(api_router, prefix=settings.api_v1_str)
