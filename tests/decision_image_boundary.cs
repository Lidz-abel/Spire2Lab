// Synthetic boundary checks; this does not load the game or capture real pixels.
using System;
using System.Collections.Generic;
using STS2_MCP;

Dictionary<string, object?> State() => new() {
    ["lab_instance_id"] = "instance", ["lab_state_token"] = "token",
    ["game_assembly_sha256"] = "game", ["lab_mod_sha256"] = "mod",
    ["lab_settled"] = true,
    ["lab_execution"] = new Dictionary<string, object?> {
        ["queue_empty"] = true, ["executor_idle"] = true, ["play_piles_empty"] = true,
        ["hand_idle"] = true, ["setup_idle"] = true
    }
};
var gate = new DecisionImageBoundary("instance", "token", "game", "mod");
int passed = 0;
void Refuses(Action action)
{
    try { action(); }
    catch (InvalidOperationException) { passed++; return; }
    throw new Exception("Unsafe image boundary was accepted");
}
gate.Validate(State(), false); passed++;
foreach (string key in new[] { "lab_instance_id", "lab_state_token", "game_assembly_sha256", "lab_mod_sha256" })
{
    var state = State(); state[key] = "changed";
    Refuses(() => gate.Validate(state, false));
}
foreach (string key in new[] { "queue_empty", "executor_idle", "play_piles_empty", "hand_idle", "setup_idle" })
{
    var state = State(); ((Dictionary<string, object?>)state["lab_execution"]!)[key] = false;
    Refuses(() => gate.Validate(state, false));
}
var unsettled = State(); unsettled["lab_settled"] = false;
Refuses(() => gate.Validate(unsettled, false));
Refuses(() => gate.Validate(State(), true));
var missing = State(); missing.Remove("lab_execution");
Refuses(() => gate.Validate(missing, false));
DecisionImageBoundary.ValidateFrame(10, 11); passed++;
Refuses(() => DecisionImageBoundary.ValidateFrame(10, 10));
Refuses(() => DecisionImageBoundary.ValidateFrame(10, 0));
Console.WriteLine(passed);
