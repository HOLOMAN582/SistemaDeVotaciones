from contextlib import asynccontextmanager
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import Base, engine
from app.routers import auth, candidates, votes, voters

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_: FastAPI):
    from app.config import get_settings

    settings = get_settings()
    if settings.jwt_secret_key == "change-this-development-secret":
        logger.warning("JWT_SECRET_KEY usa el valor de desarrollo; cámbialo antes de publicar.")
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title="API de Votaciones",
    description="API RESTful para gestionar votantes, candidatos y votos.",
    version="1.0.0",
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5500",
        "http://127.0.0.1:5500",
    ],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(voters.router)
app.include_router(candidates.router)
app.include_router(votes.router)
app.include_router(auth.router)
