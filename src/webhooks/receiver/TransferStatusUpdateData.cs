sealed class TransferStatusUpdateData
{
    public required string TransferId { get; init; }
    public string? Npn { get; init; }
    public string? PreviousState { get; init; }
    public required string State { get; init; }
    public string[]? ReasonCodes { get; init; }
    public string? StatusMessage { get; init; }
    public DateOnly? EffectiveDate { get; init; }
}
