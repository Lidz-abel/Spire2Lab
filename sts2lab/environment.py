"""Project-owned backend contract; contains no native or original-game imports."""

from collections.abc import Awaitable
from typing import Literal, Protocol, runtime_checkable

from .contracts import Observation, StepResult, StrictModel


class BranchProvenance(StrictModel):
    """Controller metadata, deliberately separate from policy observations."""

    branch_id: str
    parent_branch_id: str | None = None
    parent_decision_id: str | None = None
    operation: Literal[
        "root", "snapshot", "sample_world", "restore", "public_opening"
    ] = "root"


class UnsupportedCapability(ValueError):
    def __init__(self, backend, operation):
        super().__init__(f"{backend} does not support {operation}")
        self.backend, self.operation = backend, operation


class UnsupportedOperations:
    """Explicit rejection for optional operations; backends override supported ones."""

    def reset(self, *, encounter=None, seed=None):
        raise UnsupportedCapability(self.backend, "reset")

    def snapshot(self):
        raise UnsupportedCapability(self.backend, "snapshot")

    def restore(self, snapshot):
        raise UnsupportedCapability(self.backend, "restore")

    def sample_world(self, search_seed):
        raise UnsupportedCapability(self.backend, "sample_world")


@runtime_checkable
class Environment(Protocol):
    backend: str
    capabilities: dict[str, bool]
    manifest: dict
    encounter: str
    seed: int | None
    sequence: int
    branch_provenance: BranchProvenance | None

    def observe(self) -> Observation: ...
    def step(
        self, action_id: str, decision_id: str, *, request_id: str | None = None
    ) -> StepResult | Awaitable[StepResult]: ...
    def reset(
        self, *, encounter: str | None = None, seed: int | None = None
    ) -> Observation: ...
    def snapshot(self) -> "Environment": ...
    def restore(self, snapshot: "Environment") -> Observation: ...
    def sample_world(self, search_seed: int) -> "Environment": ...
    def close(self) -> None | Awaitable[None]: ...
