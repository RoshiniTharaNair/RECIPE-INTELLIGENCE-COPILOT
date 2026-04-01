from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes.health import router as health_router
from app.api.routes.generate import router as generate_router
from app.api.routes.retrieve import router as retrieve_router
from app.api.routes.generate_detail import router as generate_detail_router
from app.services.embeddings import get_embedding_model
from app.services.retriever import warmup_retriever


@asynccontextmanager
async def lifespan(_app: FastAPI):
    get_embedding_model()
    warmup_retriever()
    yield


app = FastAPI(
    title="Recipe Intelligence Copilot AI Service",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router)
app.include_router(generate_router)
app.include_router(retrieve_router)
app.include_router(generate_detail_router)