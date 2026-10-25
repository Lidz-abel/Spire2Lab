// Pure association gate; tests compile this file without Godot/game assemblies.
using System;
using System.Collections.Generic;

namespace STS2_MCP;

internal sealed class DecisionImageBoundary
{
    private readonly string instance;
    private readonly string token;
    private readonly string game;
    private readonly string mod;

    public DecisionImageBoundary(string instance, string token, string game, string mod)
    {
        this.instance = instance;
        this.token = token;
        this.game = game;
        this.mod = mod;
    }

    public void Validate(Dictionary<string, object?> state, bool pendingAction)
    {
        foreach (var pair in new[] {
            ("lab_instance_id", instance), ("lab_state_token", token),
            ("game_assembly_sha256", game), ("lab_mod_sha256", mod)
        })
            if (!state.TryGetValue(pair.Item1, out var actual) || !Equals(actual, pair.Item2))
                throw new InvalidOperationException("image_binding_changed:" + pair.Item1);
        if (!state.TryGetValue("lab_settled", out var settled) || settled is not true || pendingAction)
            throw new InvalidOperationException("image_state_not_settled");
        if (!state.TryGetValue("lab_execution", out var raw)
            || raw is not Dictionary<string, object?> execution)
            throw new InvalidOperationException("image_execution_state_missing");
        foreach (string key in new[] { "queue_empty", "executor_idle", "play_piles_empty", "hand_idle", "setup_idle" })
            if (!execution.TryGetValue(key, out var idle) || idle is not true)
                throw new InvalidOperationException("image_execution_busy:" + key);
    }

    public static void ValidateFrame(ulong before, ulong after)
    {
        if (after <= before) throw new InvalidOperationException("image_no_new_rendered_frame");
    }
}
