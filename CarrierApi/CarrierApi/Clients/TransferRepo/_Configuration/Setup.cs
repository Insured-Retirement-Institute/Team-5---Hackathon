using Amazon.DynamoDBv2;
using CarrierApi.Clients.AtsHub;

namespace CarrierApi.Clients.TransferRepo.Configuration;

public static class Setup
{
    public static IServiceCollection AddTransferRepo(this IServiceCollection services)
    {
        services.AddAWSService<IAmazonDynamoDB>();
        services.AddScoped<IAtsHubClient, AtsHubClient>();
        services.AddScoped<ITransferRepository, TransferRepository>();

        return services;
    }
}
