// Project-authored public choice catalogue and separate act settlement contract.
// The screen data format is provided by the pinned, attributed STS2MCP adapter.
using System;
using System.Collections.Generic;
using System.Linq;
using System.Text.Json;
using System.Text.RegularExpressions;

namespace STS2_MCP;

internal sealed record ActStartRequest(string RequestId, string ExpectedToken,
    string GameSha256, string ModSha256, string Seed)
{
    internal static ActStartRequest Parse(Dictionary<string, JsonElement> data)
    {
        var fields = new HashSet<string> { "action", "lab_request_id", "lab_expected_token",
            "expected_game_sha256", "expected_mod_sha256", "seed", "profile_id" };
        if (data.Keys.Any(k => !fields.Contains(k))) throw new ArgumentException("Unknown act start field");
        string Text(string key) => data.TryGetValue(key, out var value) && value.ValueKind == JsonValueKind.String
            ? value.GetString()! : throw new ArgumentException("Missing string: " + key);
        string Hash(string key) { var s = Text(key); return Regex.IsMatch(s, "\\A[0-9a-f]{64}\\z") ? s : throw new ArgumentException("Invalid hash: " + key); }
        if (Text("action") != "lab_start_act") throw new ArgumentException("Expected lab_start_act");
        var id = Text("lab_request_id");
        if (!Regex.IsMatch(id, "\\A[a-zA-Z0-9_-]{1,128}\\z")) throw new ArgumentException("Invalid request ID");
        if (!data.TryGetValue("profile_id", out var profile) || !profile.TryGetInt32(out int n) || n != 2)
            throw new ArgumentException("Only experiment profile 2 is supported");
        var seed = Text("seed");
        if (!Regex.IsMatch(seed, "\\A[A-Z0-9]{1,24}\\z")) throw new ArgumentException("Seed must be 1–24 uppercase ASCII letters/digits");
        return new(id, Hash("lab_expected_token"), Hash("expected_game_sha256"), Hash("expected_mod_sha256"), seed);
    }
}

internal static class ActBoundary
{
    internal static string? Classify(string phase, bool idle, bool setupIdle, bool visibleChoice, bool interactiveChoice)
    {
        if (!setupIdle) return null;
        if (idle) return "execution_idle";
        if ((phase == "card_select" || phase == "hand_select") && visibleChoice && interactiveChoice)
            return "player_choice";
        return null;
    }
}

internal sealed record ActChoice(string Id, string Kind, string Label, Dictionary<string, object?> Command);

internal static class ActChoices
{
    internal static JsonElement Get(JsonElement e, string key) => e.ValueKind == JsonValueKind.Object && e.TryGetProperty(key, out var v) ? v : default;
    internal static bool Yes(JsonElement e, string key) => Get(e, key).ValueKind == JsonValueKind.True;
    internal static string Text(JsonElement e, string key) => Get(e, key).ValueKind == JsonValueKind.String ? Get(e, key).GetString()! : "";
    internal static IEnumerable<JsonElement> Rows(JsonElement e, string key) => Get(e, key).ValueKind == JsonValueKind.Array ? Get(e, key).EnumerateArray() : Enumerable.Empty<JsonElement>();
    internal static int? Number(JsonElement e, string key) => Get(e, key).ValueKind == JsonValueKind.Number && Get(e, key).TryGetInt32(out int n) ? n : null;

    // Only observed, enabled choices. An unhandled screen yields no gameplay action.
    internal static List<ActChoice> Build(JsonElement state)
    {
        var choices = new List<ActChoice>();
        void Add(string kind, string label, string? indexKey = null, int? index = null, string? target = null)
        {
            var command = new Dictionary<string, object?> { ["action"] = kind };
            if (indexKey != null) { if (index == null || index < 0) return; command[indexKey] = index; }
            if (target != null) command["target"] = target;
            string id = kind + (index != null ? ":" + index : "") + (target != null ? ":" + target : "");
            if (choices.Any(c => c.Id == id)) throw new ArgumentException("Duplicate act choice: " + id);
            choices.Add(new(id, kind, label, command));
        }
        void Proceed(JsonElement section) { if (Yes(section, "can_proceed")) Add("proceed", "Proceed"); }
        var phase = Text(state, "state_type");
        var player = Get(state, "player");
        switch (phase)
        {
            case "map":
                foreach (var node in Rows(Get(state, "map"), "next_options"))
                    Add("choose_map_node", $"{Text(node, "type")} ({Number(node, "col")}, {Number(node, "row")})", "index", Number(node, "index"));
                break;
            case "rewards":
                var rewards = Get(state, "rewards");
                foreach (var reward in Rows(rewards, "items"))
                    if (Text(reward, "type") != "potion" || Rows(player, "potions").Count() < Number(player, "max_potion_slots"))
                        Add("claim_reward", Text(reward, "description"), "index", Number(reward, "index"));
                Proceed(rewards);
                break;
            case "card_reward":
                var offer = Get(state, "card_reward");
                foreach (var card in Rows(offer, "cards")) Add("select_card_reward", Text(card, "name"), "index", Number(card, "index"));
                if (Yes(offer, "can_skip")) Add("skip_card_reward", "Skip card reward");
                break;
            case "rest_site":
                var rest = Get(state, "rest_site");
                foreach (var option in Rows(rest, "options"))
                    if (Yes(option, "is_enabled")) Add("choose_rest_option", Text(option, "name"), "index", Number(option, "index"));
                Proceed(rest);
                break;
            case "shop":
                var shop = Get(state, "shop");
                if (Yes(shop, "lab_can_open")) Add("lab_open_shop", "Open shop");
                if (Yes(shop, "lab_inventory_open"))
                    foreach (var item in Rows(shop, "items"))
                    {
                        var price = Number(item, "price");
                        if (price >= 0 && price <= Number(player, "gold") && Yes(item, "is_stocked") && Yes(item, "can_afford")
                            && (Text(item, "category") != "potion" || Rows(player, "potions").Count() < Number(player, "max_potion_slots")))
                            Add("shop_purchase", Text(item, "category") + " · " + (Text(item, "card_name") + Text(item, "relic_name") + Text(item, "potion_name")) + " · " + price + " gold", "index", Number(item, "index"));
                    }
                if (Yes(shop, "lab_can_close")) Add("lab_close_shop", "Close shop inventory");
                if (!Yes(shop, "lab_inventory_open")) Proceed(shop);
                break;
            case "event":
                var ev = Get(state, "event");
                if (Yes(ev, "in_dialogue")) Add("advance_dialogue", "Continue dialogue");
                else foreach (var option in Rows(ev, "options"))
                    if (Get(option, "is_locked").ValueKind == JsonValueKind.False && Yes(option, "lab_enabled"))
                        Add("choose_event_option", Text(option, "title"), "index", Number(option, "index"));
                break;
            case "treasure":
                var treasure = Get(state, "treasure");
                if (Yes(treasure, "lab_can_open")) Add("lab_open_chest", "Open chest");
                foreach (var relic in Rows(treasure, "relics")) Add("claim_treasure_relic", Text(relic, "name"), "index", Number(relic, "index"));
                Proceed(treasure);
                break;
            case "card_select":
            case "hand_select":
                var selection = Get(state, phase);
                bool hand = phase == "hand_select";
                if (!Yes(selection, "preview_showing"))
                    foreach (var card in Rows(selection, "cards"))
                        if (Yes(card, "lab_selectable")) Add(hand ? "combat_select_card" : "select_card", Text(card, "name"), "index", Number(card, "index"));
                if (Yes(selection, "can_confirm")) Add(hand ? "combat_confirm_selection" : "confirm_selection", "Confirm selection");
                if (!hand && Yes(selection, "can_cancel")) Add("cancel_selection", "Cancel selection");
                break;
            case "monster":
            case "elite":
            case "boss":
                var battle = Get(state, "battle");
                if (!Yes(battle, "is_play_phase") || !Yes(state, "lab_combat_can_act")) break;
                var enemies = Rows(battle, "enemies").Select(e => Text(e, "entity_id")).Where(s => s.Length > 0).ToList();
                foreach (var card in Rows(player, "hand"))
                    if (Yes(card, "can_play"))
                    {
                        var target = Text(card, "target_type");
                        if (target == "AnyEnemy") foreach (var enemy in enemies) Add("play_card", Text(card, "name") + " → " + enemy, "card_index", Number(card, "index"), enemy);
                        else if (new[] { "Self", "None", "AllEnemies", "RandomEnemy" }.Contains(target)) Add("play_card", Text(card, "name"), "card_index", Number(card, "index"));
                    }
                foreach (var potion in Rows(player, "potions"))
                    if (Yes(potion, "lab_can_use"))
                    {
                        if (Text(potion, "target_type") == "AnyEnemy") foreach (var enemy in enemies) Add("use_potion", Text(potion, "name") + " → " + enemy, "slot", Number(potion, "slot"), enemy);
                        else if (new[] { "Self", "None", "AllEnemies", "AnyPlayer", "AnyAlly" }.Contains(Text(potion, "target_type"))) Add("use_potion", Text(potion, "name"), "slot", Number(potion, "slot"));
                    }
                Add("end_turn", "End turn");
                break;
        }
        return choices;
    }
}
