using Sts2Emulator.Core;
using Sts2Emulator.Core.Run;

namespace Sts2Emulator.Interop;

public static partial class NativeExports
{
    // Arena-to-rewards lifecycle adapter; see docs/NATIVE-COMPATIBILITY.md.
    // Burning Blood's run-side behavior is also modeled in the pinned upstream
    // RunRewardGenerator. The arena API otherwise omits that victory callback.
    private static void LabApplyVictoryBoundary(CombatState state, bool terminal, bool won, bool alreadyWon)
    {
        if (!terminal || !won || alreadyWon) return;
        if (state.Relics.Any(r => r.DefId == RunConstants.RelicBurningBlood))
            state.PlayerHp = Math.Min(state.PlayerMaxHp, state.PlayerHp + 6);
        // At rewards, combat block has expired (also observed in the random trace).
        state.PlayerBlock = 0;
        // The starter benchmark's combat powers also expire before rewards.
        state.PlayerBuffs.Clear();
    }
}
