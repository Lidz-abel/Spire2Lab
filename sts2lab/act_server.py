"""Act routes: cached live views and stored, read-only replay/image delivery."""

import asyncio
import json

from fastapi import HTTPException
from fastapi.responses import FileResponse, Response
from pydantic import BaseModel, ConfigDict, Field

from .contracts import StepRequest, digest
from .simulator import ROOT
from .traces import read_trace


def install_act_routes(app, act, combat_lab, owner_lock):
    class Start(BaseModel):
        model_config = ConfigDict(extra="forbid")
        seed: str = Field(default="SPIRE2LABACT001", pattern=r"^[A-Z0-9]{1,24}$")

    class Control(BaseModel):
        model_config = ConfigDict(extra="forbid")
        running: bool
        delay: float | None = Field(default=None, ge=0.2, le=10)

    class Archive(BaseModel):
        model_config = ConfigDict(extra="forbid")
        run_id: str = Field(pattern=r"^[0-9a-f]{32}$")

    @app.get("/act")
    async def page():
        return FileResponse(ROOT / "web/act.html")

    @app.get("/api/act/state")
    async def state():
        return act.view()

    @app.post("/api/act/start")
    async def start(command: Start):
        async with owner_lock:
            async with combat_lab.lock:
                if (
                    combat_lab.env
                    and getattr(combat_lab, "metadata", {}).get("backend")
                    == "original_game"
                ):
                    raise ValueError(
                        "Archive the combat controller's original-game session first"
                    )
                return await act.start(command.seed)

    @app.post("/api/act/step")
    async def step(command: StepRequest):
        return await act.step(command)

    @app.post("/api/act/control")
    async def control(command: Control):
        return await act.control(**command.model_dump())

    @app.post("/api/act/reconcile")
    async def reconcile():
        return await act.reconcile()

    @app.post("/api/act/archive")
    async def archive(command: Archive):
        return await act.archive(command.run_id)

    @app.get("/api/act/runs")
    async def runs():
        result = []
        for path in sorted(
            act.data_dir.glob("*.jsonl"), key=lambda p: p.stat().st_mtime, reverse=True
        )[:100]:
            with path.open() as stream:
                header = json.loads(stream.readline())["data"]["metadata"]
            result.append(
                {
                    "run_id": path.stem,
                    "seed": header["seed"],
                    "policy": header["policy"],
                }
            )
        return result

    @app.get("/api/act/runs/{run_id}")
    async def replay(run_id: str):
        try:
            return await asyncio.to_thread(read_trace, act.trace_path(run_id))
        except OSError:
            raise HTTPException(404, "Act trace unavailable")

    @app.get("/api/act/runs/{run_id}/images/{image_sha}.png")
    async def image(run_id: str, image_sha: str):
        try:
            events = await asyncio.to_thread(read_trace, act.trace_path(run_id))
            metadata = events[0]["data"]["metadata"]
            if (
                metadata["backend"] != "original_game"
                or metadata["protocol_version"] != "single-act-v1"
            ):
                raise ValueError("Not an original act")
            obs, linked = None, False
            for event in events:
                if event["kind"] in ("observation", "transition"):
                    obs = event["data"]["observation"]
                if event["kind"] == "decision_image":
                    record = event["data"]
                    if (
                        record.get("status") == "available"
                        and record.get("sha256") == image_sha
                    ):
                        if (
                            not obs
                            or record.get("run_id") != run_id
                            or record.get("decision_id") != obs["decision_id"]
                            or record.get("observation_sha256") != digest(obs)
                        ):
                            raise ValueError("Image association mismatch")
                        linked = True
            if not linked:
                raise ValueError("Image is not bound to the trace")
            data = await asyncio.to_thread(act.images.get, run_id, image_sha)
            return Response(
                data,
                media_type="image/png",
                headers={
                    "Cache-Control": "no-store",
                    "X-Content-Type-Options": "nosniff",
                },
            )
        except (OSError, ValueError, KeyError, TypeError):
            raise HTTPException(404, "Verified act image unavailable")
