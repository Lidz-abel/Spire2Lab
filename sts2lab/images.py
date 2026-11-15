"""Bounded PNG validation and immutable decision-image storage; no policy input."""

from __future__ import annotations

import base64
from datetime import datetime
import hashlib
from pathlib import Path
import re
import struct
import uuid
import zlib

MAX_PNG_BYTES = 16 * 1024 * 1024
MAX_REPLY_BYTES = 24 * 1024 * 1024
MAX_PIXELS = 16_777_216


def png_dimensions(data):
    """Validate 8-bit, non-interlaced RGB/RGBA PNG with bounded decompression."""
    if len(data) > MAX_PNG_BYTES or data[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError("Invalid or oversized PNG")
    offset, dimensions, compressed, ended = 8, None, bytearray(), False
    while offset < len(data):
        if offset + 12 > len(data):
            raise ValueError("Truncated PNG chunk")
        size = struct.unpack_from(">I", data, offset)[0]
        kind = data[offset + 4 : offset + 8]
        end = offset + 12 + size
        if end > len(data):
            raise ValueError("Truncated PNG data")
        payload = data[offset + 8 : end - 4]
        crc = struct.unpack_from(">I", data, end - 4)[0]
        if zlib.crc32(kind + payload) & 0xFFFFFFFF != crc:
            raise ValueError("PNG checksum mismatch")
        if dimensions is None and kind != b"IHDR":
            raise ValueError("Missing PNG header")
        if kind == b"IHDR":
            if dimensions is not None or size != 13:
                raise ValueError("Invalid PNG header")
            width, height, bits, color, compression, filtering, interlace = (
                struct.unpack(">IIBBBBB", payload)
            )
            if (
                not 0 < width <= 8192
                or not 0 < height <= 8192
                or width * height > MAX_PIXELS
                or bits != 8
                or color not in (2, 6)
                or (compression, filtering, interlace) != (0, 0, 0)
            ):
                raise ValueError("Unsupported PNG dimensions or format")
            dimensions = (width, height)
            stride = width * (3 if color == 2 else 4) + 1
        elif kind == b"IDAT":
            compressed.extend(payload)
        elif kind == b"IEND":
            if size or end != len(data):
                raise ValueError("Invalid PNG ending")
            ended = True
            break
        elif kind[:1].isupper() and kind != b"PLTE":
            raise ValueError("Unsupported critical PNG chunk")
        offset = end
    if not ended or not dimensions or not compressed:
        raise ValueError("Incomplete PNG")
    decoder = zlib.decompressobj()
    try:
        raw = decoder.decompress(compressed, stride * dimensions[1] + 1)
    except zlib.error as exc:
        raise ValueError("Invalid PNG compressed pixels") from exc
    if (
        len(raw) != stride * dimensions[1]
        or not decoder.eof
        or decoder.unused_data
        or decoder.unconsumed_tail
        or any(raw[i] > 4 for i in range(0, len(raw), stride))
    ):
        raise ValueError("Invalid PNG pixel rows")
    return dimensions


def decode_image(payload, expected):
    """Verify the original-process/build/state binding before accepting pixels."""
    if not isinstance(payload, dict):
        raise ValueError("Image reply must be an object")
    if (
        payload.get("schema") != "decision-image-v1"
        or payload.get("source") != "godot_root_viewport"
    ):
        raise ValueError("Unsupported image source/schema")
    if payload.get("mime_type") != "image/png":
        raise ValueError("Unsupported image type")
    for key in (
        "lab_instance_id",
        "lab_state_token",
        "game_assembly_sha256",
        "lab_mod_sha256",
    ):
        if not expected.get(key) or payload.get(key) != expected[key]:
            raise ValueError(f"Image binding mismatch: {key}")
    for key in ("width", "height", "frame_before", "frame_drawn"):
        if type(payload.get(key)) is not int:
            raise ValueError(f"Invalid image integer: {key}")
    if not 0 <= payload["frame_before"] < payload["frame_drawn"]:
        raise ValueError("Image has no newly rendered frame")
    timestamp = datetime.fromisoformat(payload["captured_at"])
    if timestamp.tzinfo is None:
        raise ValueError("Image timestamp requires timezone")
    encoded = payload.get("png_base64")
    if not isinstance(encoded, str) or len(encoded) > (MAX_PNG_BYTES + 2) // 3 * 4:
        raise ValueError("Missing or oversized image data")
    try:
        png = base64.b64decode(encoded, validate=True)
    except (ValueError, TypeError) as exc:
        raise ValueError("Invalid image encoding") from exc
    if hashlib.sha256(png).hexdigest() != payload.get("sha256"):
        raise ValueError("Image content hash mismatch")
    if png_dimensions(png) != (payload["width"], payload["height"]):
        raise ValueError("Image dimensions mismatch")
    # Only declared presentation metadata escapes the raw bridge response.
    fields = (
        "schema",
        "source",
        "mime_type",
        "lab_instance_id",
        "lab_state_token",
        "game_assembly_sha256",
        "lab_mod_sha256",
        "width",
        "height",
        "frame_before",
        "frame_drawn",
        "captured_at",
        "sha256",
    )
    return {key: payload[key] for key in fields}, png


class ImageStore:
    def __init__(self, root):
        self.root = Path(root).resolve()

    def path(self, run_id, sha256):
        if not re.fullmatch(r"[0-9a-f]{32}", run_id) or not re.fullmatch(
            r"[0-9a-f]{64}", sha256
        ):
            raise ValueError("Invalid image identifier")
        folder = (self.root / run_id).resolve()
        path = (folder / (sha256 + ".png")).resolve()
        if not folder.is_relative_to(self.root) or not path.is_relative_to(folder):
            raise ValueError("Image path escapes storage")
        return path

    def put(self, run_id, metadata, png, decision_id, observation_sha256):
        if hashlib.sha256(png).hexdigest() != metadata["sha256"]:
            raise ValueError("Image content changed before storage")
        path = self.path(run_id, metadata["sha256"])
        path.parent.mkdir(parents=True, exist_ok=True)
        if path.exists():
            self.get(run_id, metadata["sha256"])
        else:
            temporary = path.with_suffix(f".{uuid.uuid4().hex}.tmp")
            try:
                with temporary.open("xb") as stream:
                    stream.write(png)
                temporary.replace(path)
            finally:
                temporary.unlink(missing_ok=True)
        return {
            **metadata,
            "status": "available",
            "run_id": run_id,
            "decision_id": decision_id,
            "observation_sha256": observation_sha256,
            "url": f"/api/runs/{run_id}/images/{metadata['sha256']}.png",
        }

    def get(self, run_id, sha256):
        path = self.path(run_id, sha256)
        if path.stat().st_size > MAX_PNG_BYTES:
            raise ValueError("Oversized stored image")
        data = path.read_bytes()
        if hashlib.sha256(data).hexdigest() != sha256:
            raise ValueError("Stored image hash mismatch")
        return data
