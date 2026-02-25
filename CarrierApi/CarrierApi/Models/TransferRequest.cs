namespace CarrierApi.Models;

public record TransferRequest
{
    public AgentDto Agent { get; set; }
    public ImoDto ReleasingImo { get; set; }
    public ImoDto ReceivingImo { get; set; }

    public record AgentDto(string Npn);
    public record ImoDto(string Fein, string Name);
}
