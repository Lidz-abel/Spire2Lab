"""Synthetic pixels verify association/storage/control; never original evidence."""

import base64
import copy
import hashlib
import json
import os
from pathlib import Path
import shutil
import struct
import subprocess
import zlib

from fastapi.testclient import TestClient
import httpx
import pytest

from sts2lab.bridge import BridgeClient, BridgeError, PendingCommand
from sts2lab.contracts import StepRequest
from sts2lab.images import ImageStore, decode_image, png_dimensions
from sts2lab.server import create_app
from sts2lab.simulator import ROOT, Simulator
from sts2lab.traces import read_trace


def png(width=2, height=2, color=b"\x20\x80\xc0"):
    def chunk(kind, data):
        return (
            struct.pack(">I", len(data))
            + kind
            + data
            + struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)
        )

    return (
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0))
        + chunk(b"IDAT", zlib.compress((b"\0" + color * width) * height))
        + chunk(b"IEND", b"")
    )


def payload():
    data = png()
    return {
        "schema": "decision-image-v1",
        "source": "godot_root_viewport",
        "mime_type": "image/png",
        "lab_instance_id": "a" * 32,
        "lab_state_token": "b" * 64,
        "game_assembly_sha256": "c" * 64,
        "lab_mod_sha256": "d" * 64,
        "width": 2,
        "height": 2,
        "frame_before": 10,
        "frame_drawn": 11,
        "captured_at": "2026-10-25T00:00:00+00:00",
        "sha256": hashlib.sha256(data).hexdigest(),
        "png_base64": base64.b64encode(data).decode(),
    }


def test_image_requires_exact_binding_hash_dimensions_and_new_rendered_frame():
    original = payload()
    metadata, pixels = decode_image(original, original)
    assert png_dimensions(pixels) == (2, 2)
    assert "png_base64" not in metadata
    changes = {
        "lab_instance_id": "f" * 32,
        "lab_state_token": "f" * 64,
        "game_assembly_sha256": "f" * 64,
        "lab_mod_sha256": "f" * 64,
        "frame_drawn": 10,
        "frame_before": True,
        "width": 3,
        "sha256": "f" * 64,
        "png_base64": "!invalid!",
        "source": "simulator",
    }
    for key, changed in changes.items():
        with pytest.raises(ValueError):
            decode_image({**original, key: changed}, original)


def test_png_rejects_corruption_truncation_and_decompression_overrun():
    valid = png()
    for data in (
        valid[:-1],
        valid + b"extra",
        valid[:40] + b"bad" + valid[43:],
        b"not png",
    ):
        with pytest.raises(ValueError):
            png_dimensions(data)
    # Valid chunk CRCs cannot disguise oversized pixel rows after decompression.
    data = bytearray(png(4, 4))
    data[16:24] = struct.pack(">II", 2, 2)
    data[29:33] = struct.pack(">I", zlib.crc32(data[12:29]) & 0xFFFFFFFF)
    with pytest.raises(ValueError):
        png_dimensions(bytes(data))


def test_image_store_rejects_changed_files_and_path_escape(tmp_path):
    metadata, pixels = decode_image(payload(), payload())
    store = ImageStore(tmp_path / "images")
    record = store.put("1" * 32, metadata, pixels, "decision:1", "e" * 64)
    assert store.get("1" * 32, record["sha256"]) == pixels
    store.path("1" * 32, record["sha256"]).write_bytes(b"corrupted")
    with pytest.raises(ValueError):
        store.get("1" * 32, record["sha256"])
    with pytest.raises(ValueError):
        store.path("../escape", record["sha256"])
    (store.root / ("2" * 32)).symlink_to(tmp_path)
    with pytest.raises(ValueError):
        store.path("2" * 32, record["sha256"])


@pytest.mark.asyncio
async def test_bridge_capture_is_read_only_and_rejects_stale_or_unresolved_state():
    wire = payload()
    state = {
        **wire,
        "lab_protocol": 1,
        "lab_settled": True,
        "lab_capabilities": ["decision_images_v1"],
    }
    seen = []

    def handler(request):
        seen.append((request.method, request.url.path))
        return httpx.Response(
            200, json=wire if request.url.path.endswith("/image") else state
        )

    client = BridgeClient(
        "c" * 64, mod_sha256="d" * 64, transport=httpx.MockTransport(handler)
    )
    try:
        assert (await client.capture_image(state))[1] == png()
        count = len(seen)
        with pytest.raises(BridgeError):
            await client.capture_image({**state, "lab_state_token": "f" * 64})
        assert len(seen) == count + 1
        client.pending = PendingCommand("request", "token", {})
        with pytest.raises(BridgeError):
            await client.capture_image(state)
        assert len(seen) == count + 1
        assert all(method == "GET" for method, _ in seen)
    finally:
        await client.close()


def test_runtime_images_follow_observation_and_replay_never_captures_again(tmp_path):
    class SyntheticImageEnvironment(Simulator):
        capabilities = {**Simulator.capabilities, "original_pixels": True}
        last_capture = {"evidence_kind": "synthetic_image_fixture"}
        captures = 0

        async def capture_image(self):
            self.captures += 1
            if self.captures > 1:
                raise BridgeError("synthetic changed state")
            return decode_image(payload(), payload())

    environments = []

    async def factory(encounter):
        env = SyntheticImageEnvironment(encounter, 1)
        environments.append(env)
        return env

    app = create_app(tmp_path / "runs", original_factory=factory)
    with TestClient(app) as client:
        state = client.post("/api/session", json={"backend": "original_game"}).json()
        image = state["decision_image"]
        assert image["status"] == "available"
        assert image["decision_id"] == state["observation"]["decision_id"]
        run_id = state["metadata"]["run_id"]
        assert client.get(image["url"]).content == png()
        assert client.get(f"/api/runs/{run_id}/images/{'0'*64}.png").status_code == 404
        state = client.post(
            "/api/step",
            json={
                "request_id": "one",
                "decision_id": state["observation"]["decision_id"],
            },
        ).json()
        assert (
            state["status"] == "paused"
            and state["decision_image"]["status"] == "unavailable"
        )
        assert "url" not in state["decision_image"]
        assert image["decision_id"] != state["decision_image"]["decision_id"]
        trace = client.get(f"/api/runs/{run_id}").json()
        images = [e["data"] for e in trace if e["kind"] == "decision_image"]
        assert [i["status"] for i in images] == ["available", "unavailable"]
        count = environments[0].captures
        assert client.get(image["url"]).status_code == 200
        assert environments[0].captures == count
        app.state.lab.images.path(run_id, image["sha256"]).write_bytes(b"changed")
        assert client.get(image["url"]).status_code == 404
        client.post("/api/archive", json={"run_id": run_id}).raise_for_status()
        assert (
            read_trace(app.state.lab.trace_path(run_id))[-1]["kind"]
            == "session_archived"
        )


def test_production_csharp_image_gate_rejects_changed_state_busy_execution_and_old_frames(
    tmp_path,
):
    sdk = ROOT / ".tools/dotnet/dotnet"
    dotnet = str(sdk) if sdk.exists() else shutil.which("dotnet")
    if not dotnet:
        pytest.skip(".NET 9 SDK required for the synthetic C# image gate test")
    for source in (
        ROOT / "bridge/DecisionImageBoundary.cs",
        ROOT / "tests/decision_image_boundary.cs",
    ):
        shutil.copy2(source, tmp_path / source.name)
    project = tmp_path / "Images.csproj"
    project.write_text(
        '<Project Sdk="Microsoft.NET.Sdk"><PropertyGroup><OutputType>Exe</OutputType><TargetFramework>net9.0</TargetFramework><Nullable>enable</Nullable></PropertyGroup></Project>'
    )
    result = subprocess.run(
        [dotnet, "build", str(project), "-c", "Release", "--nologo"],
        capture_output=True,
        text=True,
        timeout=60,
        env={**os.environ, "DOTNET_CLI_TELEMETRY_OPTOUT": "1"},
    )
    assert result.returncode == 0, result.stdout + result.stderr
    result = subprocess.run(
        [dotnet, str(tmp_path / "bin/Release/net9.0/Images.dll")],
        capture_output=True,
        text=True,
        timeout=10,
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "16"
