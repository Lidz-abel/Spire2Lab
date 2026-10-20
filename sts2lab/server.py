"""Loopback HTTP API and local dashboard. SSH forwards this to the Windows browser."""

from contextlib import asynccontextmanager
import asyncio
import json
import httpx
from pathlib import Path
from typing import Literal

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, ConfigDict, Field

from .bridge import BridgeError, OutcomeUnknown
from .acceptance import read_acceptance_status
from .contracts import StepRequest, PROTOCOL_VERSION
from .runtime import Lab
from .simulator import CONFIG, ROOT
from .traces import read_trace


def create_app(data_dir=None, *, original_factory=None):
    lab = Lab(data_dir, original_factory=original_factory)

    @asynccontextmanager
    async def lifespan(app):
        await lab.new_session()
        task = asyncio.create_task(lab.worker())
        yield
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass
        await lab.close()

    app = FastAPI(title="STS2 Lab", version=PROTOCOL_VERSION, lifespan=lifespan)
    app.state.lab = lab

    @app.middleware("http")
    async def same_origin(request: Request, call_next):
        # Local control surface: block cross-site browser mutations without a token.
        origin = request.headers.get("origin")
        if request.method not in ("GET", "HEAD", "OPTIONS") and origin:
            from urllib.parse import urlsplit

            if urlsplit(origin).netloc != request.headers.get("host"):
                from fastapi.responses import JSONResponse

                return JSONResponse(
                    {"detail": "Cross-origin control request rejected"}, status_code=403
                )
        return await call_next(request)

    @app.exception_handler(ValueError)
    @app.exception_handler(BridgeError)
    async def invalid(request, exc):
        from fastapi.responses import JSONResponse

        return JSONResponse(
            {"detail": str(exc), "outcome_unknown": isinstance(exc, OutcomeUnknown)},
            status_code=409,
        )

    @app.exception_handler(RuntimeError)
    @app.exception_handler(httpx.HTTPError)
    async def unavailable(request, exc):
        from fastapi.responses import JSONResponse

        return JSONResponse(
            {"detail": str(exc), "error_code": "environment_unavailable"},
            status_code=503,
        )

    @app.get("/api/health")
    async def health():
        acceptance = await asyncio.to_thread(read_acceptance_status)
        return {
            "status": "ok",
            "protocol": PROTOCOL_VERSION,
            "game_target": CONFIG["game_version"],
            "original_game_verified": acceptance["verified"],
            "verification_scope": acceptance["scope"],
            "global_game_parity_proven": False,
        }

    @app.get("/api/acceptance")
    async def acceptance_status():
        return await asyncio.to_thread(read_acceptance_status)

    @app.get("/api/state")
    async def state():
        return lab.view()

    class SessionConfig(BaseModel):
        model_config = ConfigDict(extra="forbid")
        backend: Literal["native_simulator", "original_game"] = "native_simulator"
        encounter: str = "nibbits-weak"
        seed: int = Field(default=1, ge=0, lt=2**31)
        policy: str = "heuristic"
        policy_seed: int = 0

    @app.post("/api/session")
    async def new_session(config: SessionConfig):
        return await lab.new_session(**config.model_dump())

    @app.post("/api/step")
    async def step(command: StepRequest):
        return await lab.step(command)

    @app.post("/api/reconcile")
    async def reconcile():
        return await lab.reconcile()

    class ArchiveRequest(BaseModel):
        model_config = ConfigDict(extra="forbid")
        run_id: str = Field(pattern=r"^[0-9a-f]{32}$")

    @app.post("/api/archive")
    async def archive(command: ArchiveRequest):
        return await lab.archive(command.run_id)

    class Control(BaseModel):
        model_config = ConfigDict(extra="forbid")
        running: bool
        delay: float | None = Field(default=None, ge=0.1, le=5)

    @app.post("/api/control")
    async def control(command: Control):
        return await lab.control(**command.model_dump())

    @app.get("/api/events")
    async def events(request: Request):
        async def stream():
            revision = -1
            while not await request.is_disconnected():
                if lab.revision != revision:
                    view = lab.view()
                    revision = view["revision"]
                    yield f"id: {revision}\nevent: state\ndata: {json.dumps(view, ensure_ascii=False)}\n\n"
                else:
                    yield ": heartbeat\n\n"
                await asyncio.sleep(0.25)

        return StreamingResponse(
            stream(),
            media_type="text/event-stream",
            headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
        )

    @app.get("/api/runs")
    async def runs():
        results = []
        for path in sorted(
            lab.data_dir.glob("*.jsonl"), key=lambda p: p.stat().st_mtime, reverse=True
        )[:100]:
            with path.open() as f:
                header = json.loads(f.readline())
            meta = header["data"]["metadata"]
            results.append(
                {
                    "run_id": path.stem,
                    "encounter": meta["encounter"],
                    "seed": meta["seed"],
                    "policy": meta["policy"],
                    "backend": meta["backend"],
                }
            )
        return results

    @app.get("/api/runs/{run_id}")
    async def replay(run_id: str):
        try:
            return read_trace(lab.trace_path(run_id))
        except FileNotFoundError:
            raise HTTPException(404, "Run not found")

    @app.get("/api/runs/{run_id}/download")
    async def download(run_id: str):
        try:
            return FileResponse(lab.trace_path(run_id), filename=f"{run_id}.jsonl")
        except FileNotFoundError:
            raise HTTPException(404, "Run not found")

    @app.get("/api/config")
    async def config():
        return CONFIG

    @app.get("/")
    async def index():
        return FileResponse(ROOT / "web/index.html")

    app.mount("/static", StaticFiles(directory=ROOT / "web"), name="static")
    return app


app = create_app()
