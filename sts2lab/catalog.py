"""Content identity lookup from the pinned upstream tables; no game simulation import."""

import importlib.util
from functools import cache
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]


def entry_name(name):
    return "_".join(re.findall(r"[A-Z]+(?![a-z])|[A-Z]?[a-z]+|\d+", name)).upper()


@cache
def catalog():
    path = ROOT / "vendor/sts2/src/sts2_gym/names.py"
    spec = importlib.util.spec_from_file_location("sts2lab._upstream_names", path)
    names = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = names
    spec.loader.exec_module(names)
    generated = ROOT / "vendor/sts2/src/Sts2Emulator/Generated"
    definitions = names._definitions(generated / "Cards.g.cs", "CardDef")
    cards = {d["Entry"].strip('"'): names.card(i) for i, d in definitions.items()}
    return {
        "cards": cards,
        "enemies": {entry_name(v): v for v in names.enemies().values()},
        "enemy_names": {
            entry_name(v): names.enemy_name(i) for i, v in names.enemies().items()
        },
        "powers": {entry_name(v) + "_POWER": v for v in names.buffs().values()},
        "relics": {entry_name(v): v for v in names.relics().values()},
    }
