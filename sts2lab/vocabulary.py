"""Project-assigned categorical tokens for the declared starter scope.

Game-facing semantic names are content facts. These token assignments are not
upstream enum values and convey no ordinal relationship between game objects.
"""

from functools import cache
import hashlib
import json
from pathlib import Path
from types import MappingProxyType

VOCABULARY_PATH = Path(__file__).resolve().parents[1] / "config/content-v1.json"


class UnknownContent(ValueError):
    pass


class ContentVocabulary:
    def __init__(self, content: bytes):
        data = json.loads(content)
        if not isinstance(data.get("version"), str) or not data["version"]:
            raise ValueError("Content vocabulary needs a version")
        if type(data.get("padding_token")) is not int or data["padding_token"] != 0:
            raise ValueError("Vocabulary reserves token 0 for padding")
        categories = data["categories"]
        required = {"cards", "enemies", "powers", "relics", "intents", "actions"}
        if set(categories) != required:
            raise ValueError("Vocabulary categories differ from the encoding contract")
        tables = {}
        for category, table in categories.items():
            if not table or any(
                not isinstance(name, str) or not name for name in table
            ):
                raise ValueError(f"Invalid semantic names in {category}")
            values = list(table.values())
            if any(
                type(value) is not int or not 1 <= value < 2**30 for value in values
            ):
                raise ValueError(f"Invalid categorical tokens in {category}")
            if len(set(values)) != len(values):
                raise ValueError(f"Duplicate categorical token in {category}")
            tables[category] = MappingProxyType(dict(table))
        self.version = data["version"]
        self.sha256 = hashlib.sha256(content).hexdigest()
        self.tables = MappingProxyType(tables)

    def token(self, category, type_id):
        try:
            return self.tables[category][type_id]
        except KeyError as exc:
            raise UnknownContent(
                f"Content outside {self.version}: {category}/{type_id}"
            ) from exc

    def metadata(self):
        return {"version": self.version, "sha256": self.sha256}


@cache
def vocabulary():
    return ContentVocabulary(VOCABULARY_PATH.read_bytes())
