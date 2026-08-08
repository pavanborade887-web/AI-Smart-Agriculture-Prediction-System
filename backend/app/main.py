from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.auth import router as auth_router
from app.api.dashboard import router as dashboard_router
from app.api.agriculture import router as agriculture_router
from app.api.health import router as health_router
from app.core.config import get_settings
from app.core.exceptions import register_exception_handlers
from app.core.logging import configure_logging
from app.db import Base, engine

settings = get_settings()
configure_logging()

@asynccontextmanager
async def lifespan(_: FastAPI):
    Path(settings.uploads_dir).mkdir(parents=True, exist_ok=True)
    Path(settings.model_dir).mkdir(parents=True, exist_ok=True)
    Base.metadata.create_all(bind=engine)
    yield

app = FastAPI(title="AI Smart Agriculture API", version="1.0.0", description="Farm intelligence and prediction platform", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=[settings.frontend_origin], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
app.include_router(auth_router, prefix="/api/v1")
app.include_router(dashboard_router, prefix="/api/v1")
app.include_router(agriculture_router, prefix="/api/v1")
app.include_router(health_router)
register_exception_handlers(app)
