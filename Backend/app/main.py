from __future__ import annotations

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.approvals import router as approvals_router
from app.api.cases import router as cases_router
from app.api.dashboard import router as dashboard_router
from app.api.runs import router as runs_router
from app.api.suggestions import router as suggestions_router
from app.config import get_settings
from app.dispatch.base import DispatchManager
from app.dispatch.elevenlabs_stub import ElevenLabsStubProvider
from app.dispatch.email_stub import EmailStubProvider
from app.rag.embed import EmbeddingService
from app.rag.retrieve import Retriever
from app.service import SentinelService
from app.storage.clickhouse import ClickHouseClient
from app.storage.schema import run_migrations


settings = get_settings()

logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)

app = FastAPI(title=settings.app_name, version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=settings.cors_origin_list != ["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(dashboard_router)
app.include_router(runs_router)
app.include_router(cases_router)
app.include_router(approvals_router)
app.include_router(suggestions_router)


@app.get("/health")
async def healthcheck() -> dict[str, str]:
    return {"status": "ok"}


@app.on_event("startup")
async def on_startup() -> None:
    clickhouse = ClickHouseClient(settings)
    clickhouse.connect()
    run_migrations(clickhouse)

    embedder = EmbeddingService(settings)
    retriever = Retriever(settings=settings, clickhouse=clickhouse, embedder=embedder)

    dispatch_manager = DispatchManager(
        voice_provider=ElevenLabsStubProvider(dry_run=settings.dispatch_dry_run),
        email_provider=EmailStubProvider(dry_run=settings.dispatch_dry_run),
        dry_run=settings.dispatch_dry_run,
    )

    service = SentinelService(
        settings=settings,
        clickhouse=clickhouse,
        embedder=embedder,
        retriever=retriever,
        dispatch_manager=dispatch_manager,
    )
    await service.initialize()
    app.state.service = service


@app.on_event("shutdown")
async def on_shutdown() -> None:
    service: SentinelService | None = getattr(app.state, "service", None)
    if service is not None:
        await service.close()
