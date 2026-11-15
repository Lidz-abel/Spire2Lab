using System;

namespace STS2_MCP;

// Project-owned temporal gate. The caller supplies game-thread execution facts.
// Stable public fields while an action is running are never a decision boundary.
public sealed class SettlementGate
{
    private readonly long _frequency;
    private string? _lastToken;
    private long _quietSince;
    private bool _wasIdle;

    public SettlementGate(long timestampFrequency)
    {
        if (timestampFrequency <= 0) throw new ArgumentOutOfRangeException(nameof(timestampFrequency));
        _frequency = timestampFrequency;
    }

    public bool Observe(string token, bool executionIdle, long timestamp)
    {
        if (_lastToken != token || !_wasIdle || !executionIdle)
        {
            _lastToken = token;
            _wasIdle = executionIdle;
            _quietSince = timestamp;
            return false;
        }
        return (timestamp - _quietSince) / (double)_frequency >= 0.25;
    }
}
