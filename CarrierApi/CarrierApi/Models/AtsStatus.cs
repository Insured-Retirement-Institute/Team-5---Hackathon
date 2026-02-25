namespace CarrierApi.Models;

public record AtsStatus
{
    public string ReceivingFein { get; set; }
    public string ReleasingFein { get; set; }
    public string CarrierId { get; set; }
    public string Status { get; set; }
    public string Npn { get; set; }
    public List<RequirementDto> Requirements { get; set; } = [];

    public record RequirementDto
    {
        public string Code { get; set; }
        public string Status { get; set; }
        public string Details { get; set; }
    }
}
