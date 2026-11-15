using System;
using System.Collections.Generic;
using System.Linq;
using System.Text.Json;
using System.Text.RegularExpressions;

namespace STS2_MCP;

// Project-owned input contract. No game implementation or hidden state is imported.
internal sealed record ScenarioRequest(string RequestId, string ExpectedToken,
    string GameSha256, string ModSha256, int Seed, string Encounter, int ProfileId)
{
    internal const string Version = "starter-staging-v1";
    internal static readonly IReadOnlyDictionary<string, string> Encounters =
        new Dictionary<string, string> {
            ["nibbits-weak"] = "NibbitsWeak", ["slimes-weak"] = "SlimesWeak",
            ["sludge-spinner"] = "SludgeSpinnerWeak"
        };

    internal static ScenarioRequest Parse(Dictionary<string, JsonElement> data)
    {
        var fields = new HashSet<string> { "action", "lab_request_id", "lab_expected_token",
            "expected_game_sha256", "expected_mod_sha256", "seed", "encounter", "profile_id" };
        if (data.Keys.Any(k => !fields.Contains(k))) throw new ArgumentException("Unknown staging field");
        string Text(string key) => data.TryGetValue(key, out var value) && value.ValueKind == JsonValueKind.String
            ? value.GetString()! : throw new ArgumentException($"Missing string: {key}");
        int Number(string key) => data.TryGetValue(key, out var value) && value.ValueKind == JsonValueKind.Number && value.TryGetInt32(out int n)
            ? n : throw new ArgumentException($"Missing integer: {key}");
        string Hash(string key) { string v = Text(key); return Regex.IsMatch(v, "\\A[0-9a-f]{64}\\z") ? v : throw new ArgumentException($"Invalid hash: {key}"); }
        if (Text("action") != "lab_prepare") throw new ArgumentException("Expected lab_prepare");
        string id = Text("lab_request_id");
        if (!Regex.IsMatch(id, "\\A[a-zA-Z0-9_-]{1,128}\\z")) throw new ArgumentException("Invalid request ID");
        int seed = Number("seed"), profile = Number("profile_id");
        if (seed < 0) throw new ArgumentException("Seed must be in [0, 2^31)");
        if (profile != 2) throw new ArgumentException("Only dedicated experiment profile 2 is supported");
        string encounter = Text("encounter");
        if (!Encounters.ContainsKey(encounter)) throw new ArgumentException("Unsupported staging encounter");
        return new(id, Hash("lab_expected_token"), Hash("expected_game_sha256"), Hash("expected_mod_sha256"), seed, encounter, profile);
    }
}
