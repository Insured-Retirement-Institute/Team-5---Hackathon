using System.Net.NetworkInformation;

namespace CarrierApi.Configuration;

public record AtsHubSettings
{
    public string Url { get; set; }
    public string CarrierId { get; set; }
}
