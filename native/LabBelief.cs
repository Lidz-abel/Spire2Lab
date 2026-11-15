using System.Runtime.InteropServices;
using Sts2Emulator.Core;

namespace Sts2Emulator.Interop;

// Project-authored proposal conditioning, NOT an execution/reset API. The Python
// factory calls this only on a newly created independent starter arena. Game rules,
// enemy definitions and the arena itself retain their upstream provenance.
public static partial class NativeExports
{
    [UnmanagedCallersOnly(EntryPoint = "Sts2Lab_ConditionOpening")]
    public static unsafe int LabConditionOpening(
        int handle, int* handIds, int handCount,
        int* enemyIds, int* enemyHps, int enemyCount, int orderSeed)
    {
        try
        {
            if (handle < 0 || handle >= _pool.Length || _pool[handle] is not { } combat)
                return -1;
            var s = combat.State;
            if (handCount != 5 || enemyCount < 1 || enemyCount > 6 || orderSeed < 0 ||
                handIds == null || enemyIds == null || enemyHps == null)
                return -2;
            if (s.Turn != 0 || s.AscensionLevel != 0 || s.PlayerHp != 80 ||
                s.PlayerMaxHp != 80 || s.PlayerGold != 99 || s.PlayerBlock != 0 ||
                s.Energy != 3 || s.Hand.Count != 5 || s.DrawPile.Count != 5 ||
                s.DiscardPile.Count != 0 || s.ExhaustPile.Count != 0 ||
                s.KnownTopCount != 0 || s.KnownBottomCount != 0 ||
                s.PendingSelection != null || s.Enemies.Count != enemyCount)
                return 0;

            // Validate everything before changing any field of the independent world.
            var remaining = s.Hand.Concat(s.DrawPile).ToList();
            var inventory = remaining.GroupBy(c => GeneratedData.Cards.Get(c.DefId).Entry)
                .ToDictionary(g => g.Key, g => g.Count());
            if (inventory.Count != 3 || inventory.GetValueOrDefault("STRIKE_IRONCLAD") != 5 ||
                inventory.GetValueOrDefault("DEFEND_IRONCLAD") != 4 ||
                inventory.GetValueOrDefault("BASH") != 1 ||
                remaining.Any(c => c != new CardInstance(c.DefId, false))) return 0;
            var hand = new List<CardInstance>(5);
            for (int i = 0; i < handCount; i++)
            {
                int index = remaining.FindIndex(c => c.DefId == handIds[i]);
                if (index < 0) return 0;
                hand.Add(remaining[index]);
                remaining.RemoveAt(index);
            }
            var usedHps = new HashSet<int>();
            for (int i = 0; i < enemyCount; i++)
            {
                var e = s.Enemies[i];
                if (e.DefId != enemyIds[i] || e.Hp != e.MaxHp || e.Block != 0 ||
                    e.DefId is not (KE.Nibbit or KE.LeafSlimeS or KE.TwigSlimeS or
                                    KE.LeafSlimeM or KE.TwigSlimeM or KE.SludgeSpinner)) return 0;
                var band = GeneratedData.Enemies.Get(e.DefId).HpBand(0);
                int hp = enemyHps[i];
                if (hp < band.Min || hp > band.Max) return 0;
                if (usedHps.Contains(hp) && Enumerable.Range(band.Min, band.Max-band.Min+1)
                    .Any(value => !usedHps.Contains(value))) return 0;
                usedHps.Add(hp);
            }
            // New unknown order has its own proposal randomness. No actual actor's
            // order or RNG is an argument. Keep arena RNG counters/latent AI as sampled.
            var order = new Random(orderSeed);
            for (int i = remaining.Count-1; i > 0; i--)
            {
                int j = order.Next(i+1);
                (remaining[i], remaining[j]) = (remaining[j], remaining[i]);
            }
            s.Hand = hand;
            s.DrawPile = remaining;
            for (int i = 0; i < enemyCount; i++)
                s.Enemies[i].Hp = s.Enemies[i].MaxHp = enemyHps[i];
            return 1;
        }
        catch { return -3; }
    }
}
