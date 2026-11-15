// Synthetic checks of the production catalogue and gate; no game code runs.
using System;
using System.Collections.Generic;
using System.Text.Json;
using STS2_MCP;

string? line;
while ((line = Console.ReadLine()) != null)
{
    try
    {
        using var doc = JsonDocument.Parse(line);
        var root = doc.RootElement;
        object result = root.GetProperty("mode").GetString() switch {
            "start" => ActStartRequest.Parse(JsonSerializer.Deserialize<Dictionary<string, JsonElement>>(root.GetProperty("data"))!),
            "choices" => ActChoices.Build(root.GetProperty("data")),
            "boundary" => new { boundary = ActBoundary.Classify(root.GetProperty("phase").GetString()!,
                root.GetProperty("idle").GetBoolean(), root.GetProperty("setup_idle").GetBoolean(),
                root.GetProperty("visible").GetBoolean(), root.GetProperty("interactive").GetBoolean()) },
            _ => throw new ArgumentException("Unknown mode")
        };
        Console.WriteLine(JsonSerializer.Serialize(new { accepted = true, result }));
    }
    catch (Exception ex) { Console.WriteLine(JsonSerializer.Serialize(new { accepted = false, error = ex.GetType().Name })); }
}
