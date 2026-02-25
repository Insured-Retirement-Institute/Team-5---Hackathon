using CarrierApi.Clients.AtsHub.Configuration;
using OpenTelemetry.Resources;
using OpenTelemetry.Trace;

namespace CarrierApi.Configuration;

public static class Setup
{
    public static IServiceCollection AddServices(this IServiceCollection services, IConfiguration config)
    {
        services.AddAtsClient(config);

        return services;
    }

    public static IServiceCollection AddTelemetry(this IServiceCollection services, IConfiguration config)
    {
        services.AddOpenTelemetry()
            .ConfigureResource(r => r
                .AddService("CarrierApi"))
            .WithTracing(t => t
                .AddAspNetCoreInstrumentation()
                .AddHttpClientInstrumentation()
                .AddAWSInstrumentation()
                .AddOtlpExporter());

        return services;
    }
}
