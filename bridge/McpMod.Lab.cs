// Lab transport instrumentation for pinned STS2MCP. Game actions still use the
// original PlayCardAction / EndTurn paths. Compiled against the user's game DLLs.
using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.IO;
using System.Linq;
using System.Security.Cryptography;
using System.Text;
using System.Text.Json;
using MegaCrit.Sts2.Core.Combat;
using MegaCrit.Sts2.Core.Nodes.Rooms;
using MegaCrit.Sts2.Core.Runs;
using MegaCrit.Sts2.Core.Models;

namespace STS2_MCP;

public static partial class McpMod
{
    private static readonly string LabInstance = Guid.NewGuid().ToString("N");
    private static readonly Dictionary<string, (string Fingerprint, Dictionary<string, object?> Result)> LabRequests = new();
    private static readonly Queue<string> LabRequestOrder = new();
    private static string? LabAssemblySha;
    private static string? LabModSha;
    private static readonly SettlementGate LabSettlement = new(Stopwatch.Frequency);
    private static string? LabPendingFrom;
    private static string? LabLastRequestId;

    private static string LabHash(string text) => Convert.ToHexString(SHA256.HashData(Encoding.UTF8.GetBytes(text))).ToLowerInvariant();

    private static bool LabHasEnchantment(CardModel card)
    {
        // Refuse an unknown API instead of silently calling an unread modifier absent.
        // The exact property is verified against the user's assembly during live setup.
        var property = card.GetType().GetProperty("Enchantment",
            System.Reflection.BindingFlags.Instance | System.Reflection.BindingFlags.Public | System.Reflection.BindingFlags.NonPublic);
        if (property == null) throw new InvalidOperationException("Lab cannot verify card Enchantment on this game build");
        return property.GetValue(card) != null;
    }

    // Called only on the game thread, like the original BuildGameState.
    private static Dictionary<string, object?> BuildLabGameState()
    {
        var state = BuildGameState();
        LabAssemblySha ??= Convert.ToHexString(SHA256.HashData(File.ReadAllBytes(typeof(RunManager).Assembly.Location))).ToLowerInvariant();
        LabModSha ??= Convert.ToHexString(SHA256.HashData(File.ReadAllBytes(typeof(McpMod).Assembly.Location))).ToLowerInvariant();
        state["lab_instance_id"] = LabInstance;
        state["lab_protocol"] = 1;
        state["game_assembly_sha256"] = LabAssemblySha;
        state["lab_mod_sha256"] = LabModSha;
        state["lab_capabilities"] = new[] { "scenario_staging_v1", "execution_idle_v1", "decision_images_v1" };
        state["lab_profile_id"] = MegaCrit.Sts2.Core.Saves.SaveManager.Instance.CurrentProfileId;
        if (LabScenario != null) state["lab_scenario"] = LabScenario;
        bool inRun = RunManager.Instance.IsInProgress;
        bool queueEmpty = !inRun || RunManager.Instance.ActionQueueSet?.IsEmpty == true;
        var executor = inRun ? RunManager.Instance.ActionExecutor : null;
        bool executorIdle = !inRun || (executor != null && !executor.IsRunning && executor.CurrentlyRunningAction == null);
        var run = inRun ? RunManager.Instance.DebugOnlyGetState() : null;
        bool playPilesEmpty = !inRun || (run != null && run.Players.Count > 0 && run.Players.All(p =>
            p.PlayerCombatState is { } combat ? combat.PlayPile.IsEmpty : !CombatManager.Instance.IsInProgress));
        bool handIdle = NCombatRoom.Instance?.Ui?.Hand?.InCardPlay != true;
        bool executionIdle = queueEmpty && executorIdle && playPilesEmpty && handIdle && !LabSetupBusy;
        state["lab_execution"] = new Dictionary<string, object?> {
            ["queue_empty"] = queueEmpty, ["executor_idle"] = executorIdle,
            ["play_piles_empty"] = playPilesEmpty, ["hand_idle"] = handIdle,
            ["setup_idle"] = !LabSetupBusy
        };
        string token = LabHash(JsonSerializer.Serialize(state));
        long now = Stopwatch.GetTimestamp();
        bool settled = LabSettlement.Observe(token, executionIdle, now);
        bool actionable = false;
        if (state.TryGetValue("battle", out var value) && value is Dictionary<string, object?> battle)
        {
            actionable = battle.TryGetValue("is_play_phase", out var play) && play is true
                && !CombatManager.Instance.PlayerActionsDisabled
                && NCombatRoom.Instance?.Ui?.Hand?.InCardPlay != true;
        }
        // Clearing a pending command requires a changed, settled state. Polling an
        // unchanged actionable state immediately after enqueue is not completion.
        if (LabPendingFrom != null && token != LabPendingFrom && settled)
            LabPendingFrom = null;
        state["lab_state_token"] = token;
        state["lab_settled"] = settled;
        state["lab_action_ready"] = actionable && settled && LabPendingFrom == null && !LabSetupBusy;
        // Transport provenance is added AFTER hashing; acknowledging a request must
        // not by itself look like a changed game state.
        state["lab_last_request_id"] = LabLastRequestId;
        return state;
    }

    private static Dictionary<string, object?> ExecuteLabAction(string action, Dictionary<string, JsonElement> data)
    {
        if (action == "lab_prepare") return ExecuteLabPrepare(data);
        if (LabSetupBusy) return Error("lab_scenario_setup_pending");
        if (action != "play_card" && action != "end_turn")
            return ExecuteAction(action, data);
        if (!data.TryGetValue("lab_request_id", out var requestIdValue) || requestIdValue.ValueKind != JsonValueKind.String
            || !data.TryGetValue("lab_expected_token", out var expectedValue) || expectedValue.ValueKind != JsonValueKind.String)
            return Error("Lab-controlled combat requires lab_request_id and lab_expected_token.");
        string id = requestIdValue.GetString()!;
        if (id.Length == 0 || id.Length > 128) return Error("Invalid lab_request_id");
        string fingerprint = LabHash(JsonSerializer.Serialize(data.OrderBy(kv => kv.Key).ToDictionary(kv => kv.Key, kv => kv.Value)));
        if (LabRequests.TryGetValue(id, out var previous))
            return previous.Fingerprint == fingerprint ? previous.Result : Error("lab_request_id_conflict");
        var state = BuildLabGameState();
        if (!Equals(state["lab_state_token"], expectedValue.GetString()))
            return Error("lab_stale_state");
        if (state["lab_action_ready"] is not true)
            return Error("lab_not_ready");
        var result = ExecuteAction(action, data);
        result["lab_request_id"] = id;
        LabRequests[id] = (fingerprint, result);
        LabRequestOrder.Enqueue(id);
        if (LabRequestOrder.Count > 4096) LabRequests.Remove(LabRequestOrder.Dequeue());
        if (result.TryGetValue("status", out var status) && Equals(status, "ok"))
        {
            LabPendingFrom = expectedValue.GetString();
            LabLastRequestId = id;
        }
        return result;
    }
}
