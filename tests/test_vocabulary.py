"""Public encoding independence and explicit rejection of incompatible data."""

import copy
import json
from types import SimpleNamespace

import pytest

from test_original import raw_state
from sts2lab.contracts import PROTOCOL_VERSION
from sts2lab.gym_env import CombatEnv, ENCODING_VERSION
from sts2lab.original import normalize_original
from sts2lab.policies import Policy
from sts2lab.traces import TraceWriter, load_semantic_trace, read_trace
from sts2lab.vocabulary import (
    ContentVocabulary,
    UnknownContent,
    VOCABULARY_PATH,
    vocabulary,
)


def encode_public_only(observation):
    env = CombatEnv()
    # No native handle, names table, HTTP client or backend numeric IDs exist here.
    env.sim = SimpleNamespace(observe=lambda: observation)
    encoded = env._encode()
    assert env.observation_space.contains(encoded)
    return encoded


def test_encoding_accepts_original_public_observation_without_backend_tables():
    raw = raw_state()
    raw["player"]["hand"][0]["native_id"] = 999999  # ignored transport metadata
    observation, _ = normalize_original(raw, "synthetic")
    encoded = encode_public_only(observation)
    assert "native_id" not in observation.model_dump_json()
    assert encoded["hand"][0, 0] == vocabulary().token("cards", "STRIKE_IRONCLAD")
    assert encoded["enemies"][0, 0] == vocabulary().token("enemies", "Nibbit")
    assert encoded["relics"][0, 0] == vocabulary().token("relics", "BurningBlood")
    assert encoded["action_mask"].sum() == len(observation.legal_actions)
    assert not encoded["hand"][5:].any()


def test_unknown_content_cannot_become_padding():
    observation, _ = normalize_original(raw_state(), "synthetic")
    changed = observation.model_copy(
        update={
            "hand": [
                observation.hand[0].model_copy(update={"type_id": "FUTURE_CARD"}),
                *observation.hand[1:],
            ]
        }
    )
    with pytest.raises(UnknownContent, match="cards/FUTURE_CARD"):
        encode_public_only(changed)
    with pytest.raises(UnknownContent, match="intents/FutureIntent"):
        vocabulary().token("intents", "FutureIntent")


@pytest.mark.parametrize(
    "mutation",
    [
        lambda d: d.update(padding_token=1),
        lambda d: d["categories"]["cards"].update(BASH=0),
        lambda d: d["categories"]["cards"].update(BASH=True),
        lambda d: d["categories"]["cards"].update(BASH=2),
    ],
)
def test_invalid_vocabulary_is_rejected(mutation):
    data = json.loads(VOCABULARY_PATH.read_bytes())
    mutation(data)
    with pytest.raises(ValueError):
        ContentVocabulary(json.dumps(data).encode())


def test_vocabulary_fingerprint_and_freeze():
    current = vocabulary()
    data = json.loads(VOCABULARY_PATH.read_bytes())
    data["categories"]["cards"]["BASH"] = 50
    changed = ContentVocabulary(json.dumps(data).encode())
    assert current.metadata()["sha256"] != changed.metadata()["sha256"]
    with pytest.raises(TypeError):
        current.tables["cards"]["BASH"] = 50
    spec = json.loads((VOCABULARY_PATH.parents[1] / "ENCODING.json").read_text())
    assert spec["version"] == ENCODING_VERSION
    assert spec["semantic_protocol"] == PROTOCOL_VERSION
    assert spec["intent_ids"] == {"padding": 0, **current.tables["intents"]}


@pytest.mark.parametrize("encounter", ["nibbits-weak", "slimes-weak", "sludge-spinner"])
@pytest.mark.parametrize("policy_name", ["random", "heuristic"])
def test_supported_battles_remain_encodable_through_termination(encounter, policy_name):
    env = CombatEnv(encounter)
    policy = Policy(policy_name, 0)
    try:
        encoded, info = env.reset(seed=3)
        assert info["content_vocabulary"] == vocabulary().metadata()
        assert info["encoding_version"] == "combat-entities-v3"
        while True:
            decision = policy.decide(env.sim.observe())
            index = next(
                i
                for i, action in enumerate(env.actions)
                if action.action_id == decision.selected_action_id
            )
            encoded, reward, terminated, truncated, _ = env.step(index)
            assert env.observation_space.contains(encoded)
            if terminated or truncated:
                assert not encoded["action_mask"].any()
                break
    finally:
        env.close()


def test_old_semantic_trace_requires_migration_without_rewriting_it(tmp_path):
    observation, _ = normalize_original(raw_state(), "synthetic")
    old = copy.deepcopy(observation.model_dump())
    old["protocol_version"] = "0.2.0"
    old["hand"][0]["native_id"] = 472
    path = tmp_path / "old-protocol.jsonl"
    writer = TraceWriter(path)
    writer.append(
        "session_started",
        {"metadata": {"backend": "original_game"}, "observation": old},
    )
    writer.close()
    before = path.read_bytes()
    assert read_trace(path)[0]["data"]["observation"] == old
    with pytest.raises(ValueError, match="Protocol migration required"):
        load_semantic_trace(path, "original_game")
    assert path.read_bytes() == before
