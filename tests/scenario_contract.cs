// Executes only Spire2Lab's input contract against synthetic JSON. No game DLLs.
using System;
using System.Collections.Generic;
using System.Text.Json;
using STS2_MCP;

string? line;
while ((line = Console.ReadLine()) != null)
{
    try
    {
        var parsed = JsonSerializer.Deserialize<Dictionary<string, JsonElement>>(line)!;
        var request = ScenarioRequest.Parse(parsed);
        Console.WriteLine(JsonSerializer.Serialize(new { accepted = true, seed = request.Seed,
            encounter = request.Encounter, profile = request.ProfileId }));
    }
    catch (ArgumentException ex)
    {
        Console.WriteLine(JsonSerializer.Serialize(new { accepted = false, error = ex.Message }));
    }
}
