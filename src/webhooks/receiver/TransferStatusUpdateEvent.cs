sealed class TransferStatusUpdateEvent
{
    public required string EventId { get; init; }
    public required string EventType { get; init; }
    public required DateTimeOffset OccurredAt { get; init; }
    public required string Source { get; init; }
    public required TransferStatusUpdateData Data { get; init; }
}
