import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .database import Base, SessionLocal, engine
from . import models
from .importer import import_all
from .routes.disagreements import router as disagreements_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as session:
        has_seed_data = session.query(models.Location).first() is not None
    if not has_seed_data:
        import_all()
    yield


app = FastAPI(
    title="DealerOS API",
    lifespan=lifespan
)

allowed_origins = [
    "http://localhost:3000",
    "https://dealeros-azure.vercel.app",
]
cors_origins = os.getenv("CORS_ALLOW_ORIGINS")
if cors_origins:
    allowed_origins.extend(
        origin.strip()
        for origin in cors_origins.split(",")
        if origin.strip()
    )

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_methods=["GET"],
    allow_headers=["*"],
)

app.include_router(disagreements_router)

@app.get("/health")
def health():
    return {"status": "ok"}
