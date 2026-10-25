// Original Spire2Lab run control on the pinned, attributed STS2MCP transport.
// No game rules, inventory, map, random streams or save files are rewritten.
using System;
using System.Collections;
using System.Collections.Generic;
using System.Diagnostics;
using System.Linq;
using System.Text.Json;
using System.Threading.Tasks;
using Godot;
using MegaCrit.Sts2.Core.Combat;
using MegaCrit.Sts2.Core.Models;
using MegaCrit.Sts2.Core.Models.Characters;
using MegaCrit.Sts2.Core.Nodes;
using MegaCrit.Sts2.Core.Nodes.Cards.Holders;
using MegaCrit.Sts2.Core.Nodes.Combat;
using MegaCrit.Sts2.Core.Nodes.CommonUi;
using MegaCrit.Sts2.Core.Nodes.GodotExtensions;
using MegaCrit.Sts2.Core.Nodes.RestSite;
using MegaCrit.Sts2.Core.Nodes.Rooms;
using MegaCrit.Sts2.Core.Nodes.Screens.CardSelection;
using MegaCrit.Sts2.Core.Nodes.Screens.Overlays;
using MegaCrit.Sts2.Core.Rooms;
using MegaCrit.Sts2.Core.Runs;
using MegaCrit.Sts2.Core.Saves;

namespace STS2_MCP;

public static partial class McpMod
{
    private static Dictionary<string, object?>? LabAct;
    private static readonly SettlementGate LabActSettlement = new(Stopwatch.Frequency);
    private static string? LabActPendingFrom;
    private static string? LabActPendingId;
    private static bool LabActSawBoss;
    private static readonly Dictionary<string, (string Fingerprint, Dictionary<string, object?> Result)> LabActRequests = new();
    private static bool LabActOwned => LabAct != null && RunManager.Instance.IsInProgress;

    private static object? ActField(object instance, string name)
    {
        for (var type = instance.GetType(); type != null; type = type.BaseType)
        {
            var field = type.GetField(name, System.Reflection.BindingFlags.Instance | System.Reflection.BindingFlags.Public | System.Reflection.BindingFlags.NonPublic | System.Reflection.BindingFlags.DeclaredOnly);
            if (field != null) return field.GetValue(instance);
        }
        return null;
    }

    private static Dictionary<string, object?>? ActSection(Dictionary<string, object?> state, string name)
        => state.TryGetValue(name, out var raw) ? raw as Dictionary<string, object?> : null;

    // Public UI facts, read on the game thread. These checks do not click controls.
    private static void AddActUiFacts(Dictionary<string, object?> state)
    {
        var run = RunManager.Instance.IsInProgress ? RunManager.Instance.DebugOnlyGetState() : null;
        var player = run?.Players.FirstOrDefault();
        bool combat = CombatManager.Instance.IsInProgress;
        state["lab_combat_can_act"] = combat && !CombatManager.Instance.PlayerActionsDisabled
            && NPlayerHand.Instance?.CurrentMode == NPlayerHand.Mode.Play && NPlayerHand.Instance.InCardPlay == false;
        if (ActSection(state, "player") is { } p && player != null && p.GetValueOrDefault("potions") is List<Dictionary<string, object?>> potions)
            foreach (var potion in potions)
            {
                var live = player.GetPotionAtSlotIndex((int)potion["slot"]!);
                potion["lab_can_use"] = live != null && combat && live.PassesCustomUsabilityCheck && !live.IsQueued
                    && live.Usage != MegaCrit.Sts2.Core.Entities.Potions.PotionUsage.Automatic;
            }
        if (ActSection(state, "rest_site") is { } rest && rest.GetValueOrDefault("options") is List<Dictionary<string, object?>> options)
        {
            var buttons = NRestSiteRoom.Instance is { } site ? FindAll<NRestSiteButton>(site) : new List<NRestSiteButton>();
            foreach (var option in options)
            {
                int index = buttons.FindIndex(b => b.Option.OptionId == (string?)option["id"]);
                option["index"] = index;
                option["is_enabled"] = index >= 0 && buttons[index].IsVisibleInTree() && buttons[index].Option.IsEnabled;
            }
        }
        state["lab_choice_visible"] = false;
        state["lab_choice_interactive"] = false;
        string phase = state.GetValueOrDefault("state_type") as string ?? "";
        if (phase is "card_select" or "hand_select")
        {
            var selection = ActSection(state, phase);
            var overlay = NOverlayStack.Instance?.Peek();
            Node? prompt = phase == "hand_select" ? NPlayerHand.Instance : overlay as Node;
            bool visible = prompt is CanvasItem canvas && canvas.IsVisibleInTree()
                && (phase != "hand_select" || NPlayerHand.Instance?.IsInCardSelection == true)
                && (phase != "card_select" || overlay is NCardGridSelectionScreen or NChooseACardSelectionScreen);
            var holders = phase == "hand_select"
                ? NPlayerHand.Instance?.ActiveHolders.Cast<NCardHolder>().ToList() ?? new List<NCardHolder>()
                : prompt != null ? FindAllSortedByPosition<NGridCardHolder>(prompt).Cast<NCardHolder>().ToList() : new List<NCardHolder>();
            if (selection?.GetValueOrDefault("cards") is List<Dictionary<string, object?>> cards)
                foreach (var card in cards)
                {
                    int index = (int)card["index"]!;
                    bool valid = index >= 0 && index < holders.Count && holders[index].CardModel?.Id.Entry == (string?)card["id"];
                    card["lab_selectable"] = visible && valid && holders[index].IsVisibleInTree()
                        && ActField(holders[index], "_isClickable") is true;
                    if (prompt != null && ActField(prompt, "_selectedCards") is IEnumerable selected)
                        card["lab_selected"] = valid && selected.Cast<object>().Contains(holders[index].CardModel!);
                }
            state["lab_choice_visible"] = visible;
            if (selection != null)
                state["lab_choice_interactive"] = visible &&
                    (selection.GetValueOrDefault("can_confirm") is true || selection.GetValueOrDefault("can_cancel") is true
                    || (selection.GetValueOrDefault("cards") is List<Dictionary<string, object?>> cs && cs.Any(c => c.GetValueOrDefault("lab_selectable") is true)));
        }
    }

    private static string? BuildActState(Dictionary<string, object?> state, bool executionIdle)
    {
        AddActUiFacts(state);
        if (LabAct == null) return null;
        state["lab_act"] = LabAct;
        var run = RunManager.Instance.IsInProgress ? RunManager.Instance.DebugOnlyGetState() : null;
        bool guarded = run != null && run.Players.Count == 1 && run.Players[0].Character.Id.Entry == "IRONCLAD"
            && run.AscensionLevel == 0 && SaveManager.Instance.CurrentProfileId == 2 && !RunManager.Instance.ShouldSave;
        if (!guarded || LabAct.GetValueOrDefault("status") as string != "active") return null;
        bool alive = run!.Players[0].Creature.IsAlive;
        bool boss = run.CurrentActIndex == 0 && run.CurrentRoom?.RoomType == RoomType.Boss;
        if (boss && CombatManager.Instance.IsInProgress) LabActSawBoss = true;
        bool won = LabActSawBoss && alive && !CombatManager.Instance.IsInProgress
            && ((boss && state.GetValueOrDefault("state_type") as string == "rewards") || run.CurrentActIndex > 0);
        LabAct["should_save"] = RunManager.Instance.ShouldSave;
        LabAct["boss_seen"] = LabActSawBoss;
        LabAct["outcome"] = !alive ? "lost" : won ? "act_complete" : "ongoing";
        state["lab_act_choices"] = won || !alive ? new List<ActChoice>() : ActChoices.Build(JsonSerializer.SerializeToElement(state));
        string phase = state.GetValueOrDefault("state_type") as string ?? "";
        return ActBoundary.Classify(phase, executionIdle, !LabSetupBusy,
            state.GetValueOrDefault("lab_choice_visible") is true, state.GetValueOrDefault("lab_choice_interactive") is true);
    }

    private static Dictionary<string, object?> ExecuteLabStartAct(Dictionary<string, JsonElement> data)
    {
        ActStartRequest request;
        try { request = ActStartRequest.Parse(data); }
        catch (Exception ex) when (ex is ArgumentException or InvalidOperationException) { return Error(ex.Message); }
        string fingerprint = LabHash(JsonSerializer.Serialize(data.OrderBy(k => k.Key).ToDictionary(k => k.Key, k => k.Value)));
        if (LabActRequests.TryGetValue(request.RequestId, out var prior))
            return prior.Fingerprint == fingerprint ? prior.Result : Error("lab_request_id_conflict");
        if (LabSetupBusy || LabPendingFrom != null || LabActPendingFrom != null) return Error("lab_operation_pending");
        if (LabActRequests.Count >= 4096) return Error("Act request ledger full; restart required");
        var state = BuildLabGameState();
        if (!Equals(state["lab_state_token"], request.ExpectedToken)) return Error("lab_stale_state");
        if (LabAssemblySha != request.GameSha256 || LabModSha != request.ModSha256) return Error("lab_build_mismatch");
        if (state["lab_settled"] is not true || RunManager.Instance.IsInProgress || !Equals(state.GetValueOrDefault("menu_screen"), "main")) return Error("Settled main menu required");
        if (SaveManager.Instance.CurrentProfileId != 2) return Error("lab_wrong_profile");
        LabSetupBusy = true;
        LabScenario = null;
        LabActSawBoss = false;
        LabAct = new() { ["version"] = "single-act-v1", ["initializer"] = "normal_seeded_non_saving",
            ["request_id"] = request.RequestId, ["seed"] = request.Seed, ["profile_id"] = 2,
            ["should_save"] = false, ["status"] = "starting", ["outcome"] = "ongoing" };
        var result = new Dictionary<string, object?> { ["status"] = "ok", ["lab_request_id"] = request.RequestId };
        LabActRequests.Add(request.RequestId, (fingerprint, result));
        _ = StartLabAct(request);
        return result;
    }

    private static async Task StartLabAct(ActStartRequest request)
    {
        try
        {
            var game = NGame.Instance ?? throw new InvalidOperationException("Game scene unavailable");
            var run = await game.StartNewSingleplayerRun(ModelDb.Character<Ironclad>(), false,
                ActModel.GetDefaultList(), Array.Empty<ModifierModel>(), request.Seed, GameMode.Standard, 0, null);
            if (SaveManager.Instance.CurrentProfileId != 2 || RunManager.Instance.ShouldSave || run.Players.Count != 1 || run.AscensionLevel != 0)
                throw new InvalidOperationException("Act startup guard failed");
            // Observe the actual opening. No debug floor, RNG or inventory edits.
            LabAct!["status"] = "active";
            LabAct["initial_floor"] = run.TotalFloor;
        }
        catch (Exception ex) { LabAct!["status"] = "failed"; LabAct["error"] = ex.ToString(); }
        finally { LabSetupBusy = false; }
    }

    private static Dictionary<string, object?> ExecuteLabAct(Dictionary<string, JsonElement> data)
    {
        var fields = new HashSet<string> { "action", "choice_id", "lab_expected_token", "lab_request_id" };
        if (data.Keys.Any(k => !fields.Contains(k)) || fields.Any(k => !data.TryGetValue(k, out var value) || value.ValueKind != JsonValueKind.String)) return Error("Invalid act command fields");
        string id = data["lab_request_id"].GetString()!, token = data["lab_expected_token"].GetString()!;
        if (id.Length is < 1 or > 128 || token.Length != 64) return Error("Invalid act request ID/token");
        string fingerprint = LabHash(JsonSerializer.Serialize(data.OrderBy(k => k.Key).ToDictionary(k => k.Key, k => k.Value)));
        if (LabActRequests.TryGetValue(id, out var prior)) return prior.Fingerprint == fingerprint ? prior.Result : Error("lab_request_id_conflict");
        if (LabActRequests.Count >= 4096) return Error("Act request ledger full; restart required");
        var state = BuildLabGameState();
        if (!Equals(state["lab_state_token"], token)) return Error("lab_stale_state");
        if (state.GetValueOrDefault("lab_act_ready") is not true || !LabActOwned) return Error("lab_act_not_ready");
        var choices = state.GetValueOrDefault("lab_act_choices") as List<ActChoice>;
        var selected = choices?.SingleOrDefault(c => c.Id == data["choice_id"].GetString());
        if (selected == null) return Error("lab_illegal_act_choice");
        Dictionary<string, object?> result;
        // Reserve the request before invoking a game action. An exception may
        // follow a partial side effect; it must never make a retry execute twice.
        result = new() { ["status"] = "unknown", ["lab_request_id"] = id, ["error"] = "execution_in_progress" };
        LabActRequests.Add(id, (fingerprint, result));
        LabActPendingFrom = token;
        LabActPendingId = id;
        try
        {
            if (selected.Kind == "lab_open_shop")
            {
                var shop = NMerchantRoom.Instance ?? throw new InvalidOperationException("Shop unavailable");
                shop.OpenInventory();
                result = new() { ["status"] = "ok" };
            }
            else if (selected.Kind == "lab_close_shop")
            {
                var shop = NMerchantRoom.Instance ?? throw new InvalidOperationException("Shop unavailable");
                var back = FindFirst<NBackButton>(shop);
                if (back?.IsEnabled != true || !back.IsVisibleInTree()) throw new InvalidOperationException("Shop close unavailable");
                back.ForceClick();
                result = new() { ["status"] = "ok" };
            }
            else if (selected.Kind == "lab_open_chest")
            {
                var tree = Engine.GetMainLoop() as SceneTree;
                var chest = tree != null ? FindFirst<NTreasureRoom>(tree.Root)?.GetNodeOrNull<NClickableControl>("Chest") : null;
                if (chest?.IsEnabled != true) throw new InvalidOperationException("Chest unavailable");
                chest.ForceClick();
                result = new() { ["status"] = "ok" };
            }
            else
            {
                var command = selected.Command.ToDictionary(k => k.Key, k => JsonSerializer.SerializeToElement(k.Value));
                result = ExecuteAction(selected.Kind, command);
            }
            result["lab_request_id"] = id;
            if (Equals(result.GetValueOrDefault("status"), "ok")) LabLastRequestId = id;
            else { result["status"] = "unknown"; result["error"] = "handler_failed_after_dispatch"; }
        }
        catch (Exception ex) { result["error"] = "execution_outcome_unknown: " + ex.Message; }
        LabActRequests[id] = (fingerprint, result);
        return result;
    }
}
