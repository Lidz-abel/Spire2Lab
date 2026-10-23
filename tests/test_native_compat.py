"""A pinned-context correction must never silently patch a different upstream move."""

import pytest

from sts2lab.native_compat import (
    corrected_enemy_ai,
    corrected_native_exports,
    NIBBIT_SLICE_CONTEXT,
)


@pytest.mark.parametrize(
    "source",
    [
        "",
        NIBBIT_SLICE_CONTEXT * 2,
        NIBBIT_SLICE_CONTEXT.replace("KE.Nibbit", "KE.Other"),
    ],
)
def test_unknown_or_ambiguous_enemy_source_is_refused(source):
    with pytest.raises(ValueError, match="context changed"):
        corrected_enemy_ai(source)


def test_missing_terminal_hooks_are_refused():
    with pytest.raises(ValueError, match="step hooks changed"):
        corrected_native_exports("public static class NativeExports {}")
