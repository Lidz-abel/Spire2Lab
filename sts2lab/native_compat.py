"""Explicit, attributed corrections to a generated copy of the pinned engine.

Behavior contract and local-game evidence: docs/NATIVE-COMPATIBILITY.md.
This transforms upstream code; the result is derived, not an independent engine.
"""

NIBBIT_SLICE_CONTEXT = """        if (
            enemy.DefId == KE.Nibbit
            && enemy.CurrentIntent.Type == IntentType.Attack
            && enemy.MoveIndex % 3 == 1
        )
        {
            enemy.Block += BuffSystem.IncomingBlock(6, enemy.Buffs);
        }"""

CORRECTIONS = [
    "v0.107.1-nibbit-slice-block-tough-enemies",
    "starter-arena-burning-blood-victory-boundary",
]


def corrected_native_exports(source: str) -> str:
    declaration = "public static class NativeExports"
    completion = "        combat.LastPlayerWon = result.Terminal && result.PlayerWon;"
    if source.count(declaration) != 1 or source.count(completion) != 2:
        raise ValueError("Pinned native step hooks changed; review terminal boundary")
    return source.replace(
        declaration, "public static partial class NativeExports", 1
    ).replace(
        completion,
        "        LabApplyVictoryBoundary(combat.State, result.Terminal, result.PlayerWon, combat.LastPlayerWon);\n"
        + completion,
    )


def corrected_enemy_ai(source: str) -> str:
    if source.count(NIBBIT_SLICE_CONTEXT) != 1:
        raise ValueError(
            "Pinned Nibbit Slice context changed; review compatibility correction"
        )
    corrected = NIBBIT_SLICE_CONTEXT.replace(
        "BuffSystem.IncomingBlock(6, enemy.Buffs)",
        "BuffSystem.IncomingBlock(Ascension.Value(ascension, Ascension.ToughEnemies, 6, 5), enemy.Buffs)",
    )
    return source.replace(NIBBIT_SLICE_CONTEXT, corrected, 1)
