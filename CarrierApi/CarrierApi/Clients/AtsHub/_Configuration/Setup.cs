using CarrierApi.Clients.AtsHub;
using CarrierApi.Configuration;
using System.Net.Http.Headers;
using System.Text.Json;

namespace CarrierApi.Clients.AtsHub.Configuration;

public static class Setup
{
    public static IServiceCollection AddAtsClient(this IServiceCollection services, IConfiguration config)
    {
        services.AddSingleton(config
            .GetSection($"AtsHub")
            .Get<AtsHubSettings>()
            ?? throw new Exception("Cannot find AtsHub settings."));

        var productInfo = new ProductInfoHeaderValue("CarrierApi", "1.0.0");

        services.AddHttpClient<IAtsHubClient, AtsHubClient>((services, client) =>
        {
            var settings = services.GetRequiredService<AtsHubSettings>();
            client.BaseAddress = new Uri(settings.Url);
            client.DefaultRequestHeaders.UserAgent.Add(productInfo);
        });

        return services;
    }
}
