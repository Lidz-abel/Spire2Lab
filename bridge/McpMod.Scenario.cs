using System;
using System.Collections;
using System.Collections.Generic;
using System.Linq;
using System.Reflection;
using System.Text.Json;
using System.Threading.Tasks;
using Godot;
using MegaCrit.Sts2.Core.Combat;
using MegaCrit.Sts2.Core.Entities.Players;
using MegaCrit.Sts2.Core.Entities.Rngs;
using MegaCrit.Sts2.Core.Map;
using MegaCrit.Sts2.Core.Models;
using MegaCrit.Sts2.Core.Models.Characters;
using MegaCrit.Sts2.Core.Models.Events;
using MegaCrit.Sts2.Core.Nodes;
using MegaCrit.Sts2.Core.Random;
using MegaCrit.Sts2.Core.Rooms;
using MegaCrit.Sts2.Core.Runs;
using MegaCrit.Sts2.Core.Saves;

namespace STS2_MCP;

// Project-owned experiment setup. All card/enemy effects remain in the game.
// This explicitly creates debug-staged, non-saving runs in experiment profile 2.
public static partial class McpMod
{
    private static bool LabSetupBusy;
    private static Dictionary<string, object?>? LabScenario;
    private static readonly Dictionary<string, (string Fingerprint, Dictionary<string, object?> Result)> LabSetupRequests = new();

    private static Dictionary<string, object?> ExecuteLabPrepare(Dictionary<string, JsonElement> data)
    {
        ScenarioRequest request;
        try { request = ScenarioRequest.Parse(data); }
        catch (ArgumentException ex) { return Error(ex.Message); }
        string fingerprint = LabHash(JsonSerializer.Serialize(data.OrderBy(k => k.Key).ToDictionary(k => k.Key, k => k.Value)));
        if (LabSetupRequests.TryGetValue(request.RequestId, out var prior))
            return prior.Fingerprint == fingerprint ? prior.Result : Error("lab_request_id_conflict");
        if (LabSetupBusy || LabPendingFrom != null) return Error("lab_operation_pending");
        if (LabSetupRequests.Count >= 4096) return Error("Restart the bridge before more setup requests");
        var state = BuildLabGameState();
        if (request.ExpectedToken != (string)state["lab_state_token"]!) return Error("lab_stale_state");
        if (request.GameSha256 != LabAssemblySha || request.ModSha256 != LabModSha) return Error("lab_build_mismatch");
        if (state["lab_settled"] is not true) return Error("lab_not_settled");
        if (SaveManager.Instance.CurrentProfileId != request.ProfileId) return Error("lab_wrong_profile");
        if (RunManager.Instance.IsInProgress || !state.TryGetValue("menu_screen", out var menu) || !Equals(menu, "main"))
            return Error("Return to the main menu before preparing a new experiment");
        // Check every reflection dependency before creating a run.
        try { ValidateScenarioApi(); }
        catch (Exception ex) { return Error("Unsupported scenario API: " + ex.Message); }
        LabSetupBusy = true;
        LabScenario = new() {
            ["initializer_version"] = ScenarioRequest.Version,
            ["method"] = "debug_staged_non_saving_run",
            ["request_id"] = request.RequestId, ["status"] = "starting",
            ["seed"] = request.Seed, ["encounter"] = request.Encounter,
            ["profile_id"] = request.ProfileId, ["should_save"] = false,
            ["game_sha256"] = LabAssemblySha, ["mod_sha256"] = LabModSha
        };
        var result = new Dictionary<string, object?> { ["status"] = "ok", ["lab_request_id"] = request.RequestId, ["message"] = "Scenario preparation accepted; poll lab_scenario.status" };
        LabSetupRequests.Add(request.RequestId, (fingerprint, result));
        _ = PrepareLabScenario(request); // Starts on the Godot thread; never Task.Run.
        return result;
    }

    private static FieldInfo ScenarioSeedField => typeof(RunRngSet).GetField("<Seed>k__BackingField", BindingFlags.Instance | BindingFlags.NonPublic)
        ?? throw new MissingFieldException("RunRngSet.Seed backing field");
    private static FieldInfo ScenarioStreamsField => typeof(RunRngSet).GetField("_rngs", BindingFlags.Instance | BindingFlags.NonPublic)
        ?? throw new MissingFieldException("RunRngSet._rngs");
    private static MethodInfo ScenarioCreateRng => typeof(RunRngSet).GetMethod("CreateRng", BindingFlags.Instance | BindingFlags.NonPublic, null, new[] { typeof(RunRngType) }, null)
        ?? throw new MissingMethodException("RunRngSet.CreateRng");

    private static void ValidateScenarioApi()
    {
        if (ScenarioSeedField.FieldType != typeof(uint)) throw new InvalidOperationException("Run seed type changed");
        if (!typeof(IDictionary).IsAssignableFrom(ScenarioStreamsField.FieldType)) throw new InvalidOperationException("Run streams type changed");
        if (ScenarioCreateRng.ReturnType != typeof(Rng)) throw new InvalidOperationException("RNG factory type changed");
    }

    private static void GuardScenarioProfile(ScenarioRequest request)
    {
        if (SaveManager.Instance.CurrentProfileId != request.ProfileId) throw new InvalidOperationException("Experiment profile changed during setup");
        if (RunManager.Instance.ShouldSave) throw new InvalidOperationException("Experimental run must not save");
    }

    private static void VerifyStarterInventory(Player player)
    {
        var expected = new Dictionary<string, int> { ["STRIKE_IRONCLAD"] = 5, ["DEFEND_IRONCLAD"] = 4, ["BASH"] = 1 };
        var cards = player.Deck.Cards;
        var actual = cards.GroupBy(c => c.Id.Entry).ToDictionary(g => g.Key, g => g.Count());
        if (actual.Count != expected.Count || expected.Any(p => !actual.TryGetValue(p.Key, out var count) || count != p.Value)
            || cards.Any(c => c.IsUpgraded || LabHasEnchantment(c))) throw new InvalidOperationException("Starter deck mismatch");
        if (player.Character.Id.Entry != "IRONCLAD" || player.Creature.CurrentHp != 80 || player.Creature.MaxHp != 80 || player.Gold != 99)
            throw new InvalidOperationException("Starter player state mismatch");
        if (player.Relics.Count != 1 || player.Relics[0].Id.Entry != "BURNING_BLOOD" || player.Potions.Any())
            throw new InvalidOperationException("Starter inventory mismatch");
    }

    private static Dictionary<string, object?> StreamEvidence(RunRngSet rng)
    {
        var output = new Dictionary<string, object?>();
        foreach (DictionaryEntry item in (IDictionary)ScenarioStreamsField.GetValue(rng)!)
        {
            var stream = (Rng)item.Value!;
            output[item.Key.ToString()!] = new Dictionary<string, object?> { ["seed"] = stream.Seed, ["counter"] = stream.Counter };
        }
        return output;
    }

    private static async Task PrepareLabScenario(ScenarioRequest request)
    {
        try
        {
            // ModelDb holds shared canonical definitions. CombatRoom requires a
            // fresh mutable encounter (also used by the pinned upstream debug API).
            var encounter = ModelDb.AllEncounters.Single(e => e.GetType().Name == ScenarioRequest.Encounters[request.Encounter]).ToMutable();
            encounter.AssertMutable();
            LabScenario!["encounter_model_type"] = encounter.GetType().Name;
            LabScenario["encounter_model_mutable"] = encounter.IsMutable;
            // The game's run startup creates character inventory and scene nodes.
            // A display seed is not claimed to hash to the requested numeric seed.
            var game = NGame.Instance ?? throw new InvalidOperationException("Game scene is unavailable");
            var run = await game.StartNewSingleplayerRun(ModelDb.Character<Ironclad>(), false,
                ActModel.GetDefaultList(), Array.Empty<ModifierModel>(), "SPIRE2LAB" + request.Seed,
                GameMode.Standard, 0, null);
            GuardScenarioProfile(request);
            if (run.Players.Count != 1 || run.AscensionLevel != 0) throw new InvalidOperationException("Only single-player A0 is supported");
            var player = run.Players[0];
            VerifyStarterInventory(player);
            if (run.MapPointHistory.SelectMany(a => a).Any(e => e.HasRoomOfType(RoomType.Monster) || e.HasRoomOfType(RoomType.Elite) || e.HasRoomOfType(RoomType.Boss)))
                throw new InvalidOperationException("A combat occurred before scenario initialization");
            // First-profile startup can omit Neow. Establish one explicit noncombat
            // history anchor so the game's next room has actual TotalFloor == 2.
            if (run.TotalFloor == 0)
            {
                run.AppendToMapPointHistory(MapPointType.Ancient, RoomType.Event, ModelDb.Event<Neow>().Id);
                LabScenario!["history_anchor"] = "debug_neow_history_without_event_rewards";
            }
            else LabScenario!["history_anchor"] = "existing_initial_noncombat_room";
            if (run.TotalFloor != 1) throw new InvalidOperationException("Unexpected precombat floor");

            // Explicit numeric-seed initialization, once, before any target battle.
            // Rebuild through the game's own factory, retaining its stream names.
            var rng = run.Rng;
            ScenarioSeedField.SetValue(rng, (uint)request.Seed);
            var streams = (IDictionary)ScenarioStreamsField.GetValue(rng)!;
            streams.Clear();
            foreach (RunRngType kind in Enum.GetValues<RunRngType>())
                streams.Add(kind, ScenarioCreateRng.Invoke(rng, new object[] { kind }));
            if (run.Rng.Seed != (uint)request.Seed || streams.Values.Cast<Rng>().Any(r => r.Counter != 0))
                throw new InvalidOperationException("RNG initialization did not establish the declared seed/counters");
            LabScenario!["rng_initialization"] = "numeric_run_seed_game_named_factories_before_combat";
            LabScenario["rng_before_combat"] = StreamEvidence(rng);
            LabScenario["completed_combats_before"] = 0;
            LabScenario["status"] = "entering_combat";
            await RunManager.Instance.EnterMapCoordDebug(new MapCoord(0, 1), RoomType.Monster, MapPointType.Monster, encounter, false);
            GuardScenarioProfile(request);
            if (run.TotalFloor != 2) throw new InvalidOperationException("Actual game floor differs from 2");
            VerifyStarterInventory(player);
            LabScenario["actual_floor"] = run.TotalFloor;
            LabScenario["rng_after_entry"] = StreamEvidence(rng);
            LabScenario["status"] = "entered";
            // Python still requires settled/actionable state and independent opening
            // validation. Completing EnterRoom is not itself a passed scenario.
        }
        catch (Exception ex)
        {
            LabScenario!["status"] = "failed";
            LabScenario["error"] = ex.ToString();
            GD.PrintErr("[Spire2Lab] Scenario initialization failed: " + ex.Message);
        }
        finally { LabSetupBusy = false; }
    }
}
