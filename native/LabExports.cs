using System.Runtime.InteropServices;
using System.Text.Json;
using Sts2Emulator.Core;
using Sts2Emulator.Core.Effects;

namespace Sts2Emulator.Interop;

// Only observational code. No alternate card effects or enemy rules live here.
public static partial class NativeExports
{
    [UnmanagedCallersOnly(EntryPoint = "Sts2Lab_ApiVersion")]
    public static int LabApiVersion() => 1;

    private static void Buffs(Utf8JsonWriter w, string key, List<BuffState> buffs)
    {
        w.WriteStartArray(key);
        foreach (var b in buffs.OrderBy(b => (int)b.Id))
        {
            w.WriteStartObject(); w.WriteString("type_id", b.Id.ToString());
            w.WriteNumber("amount", b.Magnitude); w.WriteEndObject();
        }
        w.WriteEndArray();
    }

    private static void Card(Utf8JsonWriter w, CardInstance c, CombatState s)
    {
        var d = GeneratedData.Cards.Get(c.DefId);
        w.WriteStartObject();
        w.WriteNumber("native_id", c.DefId); w.WriteString("type_id", d.Entry);
        w.WriteString("name", d.Name); w.WriteString("card_type", d.Type.ToString());
        w.WriteBoolean("upgraded", c.Upgraded); w.WriteString("target", d.Target.ToString());
        w.WriteNumber("cost", CombatEngine.EffectiveCost(c, s));
        w.WriteNumber("printed_damage", d.BaseDamage + (c.Upgraded ? d.UpgradeDamage : 0));
        w.WriteNumber("printed_block", d.BaseBlock + (c.Upgraded ? d.UpgradeBlock : 0));
        w.WriteNumber("bonus_damage", c.BonusDamage);
        w.WriteString("enchantment", c.Enchantment.ToString()); w.WriteNumber("enchant_amount", c.EnchantAmount);
        w.WriteBoolean("free_this_turn", c.FreeThisTurn);
        w.WriteEndObject();
    }

    private static void Cards(Utf8JsonWriter w, string key, IEnumerable<CardInstance> cards, CombatState s)
    {
        w.WriteStartArray(key);
        foreach (var c in cards) Card(w, c, s);
        w.WriteEndArray();
    }

    private static void IntentJson(Utf8JsonWriter w, Intent intent, EnemyState enemy, CombatState s)
    {
        w.WriteStartObject(); w.WriteString("type", intent.Type.ToString());
        w.WriteBoolean("deals_damage", intent.Type == IntentType.Attack || intent.CarriesDamage);
        w.WriteNumber("magnitude", intent.AnnouncedDamage(enemy.Buffs, s.PlayerBuffs, RelicEffects.WeakMultiplierDeltaAgainstPlayer(s)));
        w.WriteNumber("hits", intent.Hits); w.WriteEndObject();
    }

    // Hidden order is sorted BEFORE serialization. The separate debug flag is never used
    // by the policy, dashboard or Gym observation. That path exists only for verification.
    [UnmanagedCallersOnly(EntryPoint = "Sts2Lab_Observe")]
    public static unsafe int LabObserve(int handle, int debug, byte* output, int capacity)
    {
        try
        {
            if (handle < 0 || handle >= _pool.Length || _pool[handle] is not { } combat) return -1;
            var s = combat.State;
            using var stream = new MemoryStream();
            using (var w = new Utf8JsonWriter(stream))
            {
                w.WriteStartObject();
                w.WriteNumber("turn", s.Turn); w.WriteNumber("encounter_native_id", s.EncounterId);
                w.WriteString("phase", s.PendingSelection is null ? "combat" : "card_selection");
                w.WriteStartObject("player");
                w.WriteNumber("hp", s.PlayerHp); w.WriteNumber("max_hp", s.PlayerMaxHp);
                w.WriteNumber("block", s.PlayerBlock); w.WriteNumber("energy", s.Energy);
                w.WriteNumber("max_energy", s.MaxEnergy); w.WriteNumber("gold", s.PlayerGold);
                Buffs(w, "powers", s.PlayerBuffs); w.WriteEndObject();
                Cards(w, "hand", s.Hand, s);
                // Full card value sort avoids leaking hidden order through stable sorting
                // of different instances with the same definition id.
                Cards(w, "draw_pile", s.DrawPile.OrderBy(c => c.ToString(), StringComparer.Ordinal), s);
                Cards(w, "discard_pile", s.DiscardPile.OrderBy(c => c.ToString(), StringComparer.Ordinal), s);
                Cards(w, "exhaust_pile", s.ExhaustPile.OrderBy(c => c.ToString(), StringComparer.Ordinal), s);
                Cards(w, "known_top", s.DrawPile.Take(s.KnownTopCount), s);
                Cards(w, "known_bottom", s.DrawPile.TakeLast(s.KnownBottomCount), s);
                w.WriteStartArray("enemies");
                for (int i = 0; i < s.Enemies.Count; i++)
                {
                    var e = s.Enemies[i];
                    if (e.Hp <= 0) continue;
                    w.WriteStartObject(); w.WriteNumber("slot", i); w.WriteNumber("native_id", e.DefId);
                    w.WriteNumber("hp", e.Hp); w.WriteNumber("max_hp", e.MaxHp); w.WriteNumber("block", e.Block);
                    Buffs(w, "powers", e.Buffs);
                    w.WriteStartArray("intents"); IntentJson(w, e.CurrentIntent, e, s);
                    if (e.SecondaryIntent is { } secondary) IntentJson(w, secondary, e, s);
                    w.WriteEndArray(); w.WriteEndObject();
                }
                w.WriteEndArray();
                w.WriteStartArray("relics");
                foreach (var r in s.Relics)
                {
                    w.WriteStartObject(); w.WriteNumber("native_id", r.DefId);
                    w.WriteNumber("counter", r.Counter); w.WriteEndObject();
                }
                w.WriteEndArray();
                w.WriteStartArray("legal_indices");
                foreach (int a in CombatEngine.ValidActions(s)) w.WriteNumberValue(a);
                w.WriteEndArray();
                if (debug != 0)
                {
                    Cards(w, "debug_draw_order", s.DrawPile, s);
                    w.WriteNumber("debug_seed", combat.Seed);
                }
                w.WriteEndObject();
            }
            byte[] bytes = stream.ToArray();
            if (capacity >= bytes.Length && output != null) bytes.CopyTo(new Span<byte>(output, capacity));
            return bytes.Length;
        }
        catch { return -2; }
    }
}
