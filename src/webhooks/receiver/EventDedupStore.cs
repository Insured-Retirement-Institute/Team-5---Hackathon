using System.Collections.Concurrent;

sealed class EventDedupStore
{
    private readonly ConcurrentDictionary<string, DateTimeOffset> _seenEvents = new();
    private readonly TimeSpan _ttl;

    public EventDedupStore(TimeSpan ttl)
    {
        _ttl = ttl;
    }

    public bool TryRegister(string eventId)
    {
        var now = DateTimeOffset.UtcNow;
        CleanupExpired(now);
        return _seenEvents.TryAdd(eventId, now.Add(_ttl));
    }

    private void CleanupExpired(DateTimeOffset now)
    {
        foreach (var entry in _seenEvents)
        {
            if (entry.Value <= now)
            {
                _seenEvents.TryRemove(entry.Key, out _);
            }
        }
    }
}
