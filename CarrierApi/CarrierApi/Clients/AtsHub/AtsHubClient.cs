using CarrierApi.Configuration;
using CarrierApi.Models;
using System.Text.Json;

namespace CarrierApi.Clients.AtsHub;

public interface IAtsHubClient
{
    Task SendStatus(AtsStatus status);
}

public class AtsHubClient(HttpClient client, AtsHubSettings settings) : IAtsHubClient
{
    public async Task SendStatus(AtsStatus status)
    {
        ArgumentNullException.ThrowIfNull(status);

        const string route = $"ats/status";
        status.CarrierId = settings.CarrierId;
        var options = new JsonSerializerOptions
        {
            PropertyNamingPolicy = JsonNamingPolicy.CamelCase
        };
        var response = await client.PostAsJsonAsync(route, status, options);
        response.EnsureSuccessStatusCode();
    }
}
