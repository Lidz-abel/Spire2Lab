// Synthetic clock and execution facts; runs the production gate without game DLLs.
using System;
using System.Text.Json;
using STS2_MCP;

string? line;
while ((line = Console.ReadLine()) != null)
{
    using var input = JsonDocument.Parse(line);
    var gate = new SettlementGate(input.RootElement.GetProperty("frequency").GetInt64());
    foreach (var observation in input.RootElement.GetProperty("observations").EnumerateArray())
    {
        bool settled = gate.Observe(observation.GetProperty("token").GetString()!,
            observation.GetProperty("idle").GetBoolean(),
            observation.GetProperty("timestamp").GetInt64());
        Console.WriteLine(JsonSerializer.Serialize(settled));
    }
}
