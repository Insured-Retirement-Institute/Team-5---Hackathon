using Amazon.DynamoDBv2;
using Amazon.DynamoDBv2.Model;
using CarrierApi.Configuration;
using CarrierApi.Models;
using System.Text.Json;

namespace CarrierApi.Clients.TransferRepo;

public interface ITransferRepository
{
    Task SaveTransferAsync(string id, TransferRequest request);
    Task<List<(string Id, long Timestamp, TransferRequest Request)>> GetRecentTransfersAsync(int limit = 5);
}

public class TransferRepository : ITransferRepository
{
    private readonly IAmazonDynamoDB _dynamoDB;
    private readonly string _tableName;

    public TransferRepository(IAmazonDynamoDB dynamoDB, AtsHubSettings settings)
    {
        _dynamoDB = dynamoDB;
        var carrierName = settings.CarrierId;
        _tableName = $"carrier-{carrierName.ToLower().Replace(" ", "-")}-requests";
    }

    public async Task SaveTransferAsync(string id, TransferRequest request)
    {
        var item = new Dictionary<string, AttributeValue>
        {
            ["Id"] = new AttributeValue { S = id },
            ["Timestamp"] = new AttributeValue { N = DateTimeOffset.UtcNow.ToUnixTimeSeconds().ToString() },
            ["Data"] = new AttributeValue { S = JsonSerializer.Serialize(request) }
        };

        await _dynamoDB.PutItemAsync(_tableName, item);
    }

    public async Task<List<(string Id, long Timestamp, TransferRequest Request)>> GetRecentTransfersAsync(int limit = 5)
    {
        var response = await _dynamoDB.ScanAsync(new ScanRequest
        {
            TableName = _tableName,
            Limit = 100
        });

        return [.. response.Items
            .Select(item => (
                Id: item["Id"].S,
                Timestamp: long.Parse(item["Timestamp"].N),
                Request: JsonSerializer.Deserialize<TransferRequest>(item["Data"].S)!
            ))
            .OrderByDescending(x => x.Timestamp)
            .Take(limit)];
    }
}
