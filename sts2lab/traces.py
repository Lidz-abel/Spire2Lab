"""Append-only trace with explicit provenance and hash-chain integrity."""

import json
import time
from pathlib import Path
from .contracts import canonical_json, digest, Observation, PROTOCOL_VERSION


class TraceWriter:
    def __init__(self, path: Path):
        path.parent.mkdir(parents=True, exist_ok=True)
        self.file = path.open("x", encoding="utf-8")
        self.sequence = 0
        self.previous = "0" * 64

    def append(self, kind, data):
        event = {
            "sequence": self.sequence,
            "kind": kind,
            "timestamp": time.time(),
            "previous_hash": self.previous,
            "data": data,
        }
        event["hash"] = digest(event)
        self.file.write(canonical_json(event) + "\n")
        self.file.flush()
        self.previous = event["hash"]
        self.sequence += 1
        return event

    def close(self):
        self.file.close()


def read_trace(path):
    events = []
    previous = "0" * 64
    with open(path, encoding="utf-8") as stream:
        for index, line in enumerate(stream):
            event = json.loads(line)
            claimed = event.pop("hash")
            if (
                event["sequence"] != index
                or event["previous_hash"] != previous
                or digest(event) != claimed
            ):
                raise ValueError(f"Trace integrity error at event {index}")
            event["hash"] = claimed
            events.append(event)
            previous = claimed
    return events


def load_semantic_trace(path, backend):
    events = read_trace(path)
    if not events or events[0]["kind"] != "session_started":
        raise ValueError("Missing session header")
    header = events[0]["data"]
    if header["metadata"]["backend"] != backend:
        raise ValueError(f"Expected a {backend} trace")
    observations = [Observation.model_validate(header["observation"])]
    transitions = []
    pending = None
    ended = False
    closed = False
    for event in events[1:]:
        kind, data = event["kind"], event["data"]
        if closed:
            raise ValueError("Trace contains events after session closure")
        if kind in ("session_closed", "session_archived"):
            closed = True
        if kind == "action_submitted":
            if pending is not None or ended:
                raise ValueError("Overlapping action or action after terminal state")
            pending = data
        elif kind == "transition":
            if (
                pending is None
                or data["request_id"] != pending["request"]["request_id"]
            ):
                raise ValueError("Transition has no matching command")
            before = observations[-1]
            if pending["request"]["decision_id"] != before.decision_id:
                raise ValueError("Command was submitted against a different decision")
            action = data["action"]
            if action != pending["action"] or action not in [
                a.model_dump() for a in before.legal_actions
            ]:
                raise ValueError(
                    "Recorded transition action is not the submitted legal action"
                )
            obs = Observation.model_validate(data["observation"])
            observations.append(obs)
            transitions.append(data)
            ended = data["terminated"] or data["truncated"]
            pending = None
        elif kind == "infrastructure_error":
            raise ValueError("Trace contains an infrastructure error")
    if pending is not None:
        raise ValueError("Trace ends with an unresolved command")
    if any(o.protocol_version != PROTOCOL_VERSION for o in observations):
        raise ValueError("Protocol migration required before comparing this trace")
    return header["metadata"], observations, transitions
