using System.Net.Http.Headers;
using System.Security.Cryptography;
using System.Text;
using System.Text.Json;
using System.Text.Json.Nodes;

var allowedStates = new HashSet<string>(StringComparer.OrdinalIgnoreCase)
{
    "SUBMITTED",
    "VALIDATION",
    "PROCESSING",
    "COMPLETED",
    "REJECTED",
    "WITHDRAWN"
};

var webhookUrl = Environment.GetEnvironmentVariable("WEBHOOK_URL")
                 ?? "http://localhost:5000/hooks/ats-status";
var secret = Environment.GetEnvironmentVariable("ATS_WEBHOOK_SECRET")
             ?? "local-dev-shared-secret";
var delayMsRaw = Environment.GetEnvironmentVariable("SENDER_DELAY_MS");
var autoSend = IsEnabled(Environment.GetEnvironmentVariable("SENDER_AUTO_SEND"));
var payloadPath = args.Length > 0
    ? args[0]
    : "src/webhooks/receiver/examples/payload.json";

if (int.TryParse(delayMsRaw, out var delayMs) && delayMs > 0)
{
    Console.WriteLine($"Delaying send by {delayMs}ms...");
    await Task.Delay(delayMs);
}

if (!File.Exists(payloadPath))
{
    Console.Error.WriteLine($"Payload file not found: {payloadPath}");
    Environment.Exit(1);
}

var payloadBytes = await File.ReadAllBytesAsync(payloadPath);
var payloadText = Encoding.UTF8.GetString(payloadBytes);
var templatePayload = JsonNode.Parse(payloadText) as JsonObject
                      ?? throw new InvalidOperationException("Payload must be a valid JSON object.");

var dataObject = templatePayload["data"] as JsonObject
                 ?? throw new InvalidOperationException("Payload must include a data object.");

var currentState = dataObject["state"]?.GetValue<string>();
if (string.IsNullOrWhiteSpace(currentState))
{
    throw new InvalidOperationException("Payload data.state must be provided.");
}

using var httpClient = new HttpClient();
while (true)
{
    var nextState = ReadRequiredState("Enter transfer status to send", allowedStates);
    var eventId = $"evt_{Guid.NewGuid():N}";

    var payloadToSend = BuildPayloadForStatusUpdate(templatePayload, eventId, currentState, nextState);
    var payloadToSendBytes = Encoding.UTF8.GetBytes(payloadToSend);
    var signature = ComputeHmacSha256Hex(payloadToSendBytes, secret);

    using var request = new HttpRequestMessage(HttpMethod.Post, webhookUrl)
    {
        Content = new StringContent(payloadToSend, Encoding.UTF8, "application/json")
    };

    request.Headers.Add("X-ATS-Event-Id", eventId);
    request.Headers.Add("X-ATS-Signature", $"sha256={signature}");
    request.Headers.Accept.Add(new MediaTypeWithQualityHeaderValue("application/json"));

    Console.WriteLine($"Sending to: {webhookUrl}");
    Console.WriteLine($"Payload: {payloadPath}");
    Console.WriteLine($"EventId: {eventId}");
    Console.WriteLine($"PreviousState: {currentState}");
    Console.WriteLine($"State: {nextState}");

    using var response = await httpClient.SendAsync(request);
    var responseBody = await response.Content.ReadAsStringAsync();

    Console.WriteLine($"Request Status: {(int)response.StatusCode} {response.StatusCode}");
    if (!string.IsNullOrWhiteSpace(responseBody))
    {
        Console.WriteLine("Receiver Response:");
        Console.WriteLine(responseBody);
    }

    currentState = nextState;
}

static string BuildPayloadForStatusUpdate(JsonObject templatePayload, string eventId, string previousState, string state)
{
    var payload = templatePayload.DeepClone() as JsonObject
                  ?? throw new InvalidOperationException("Payload template could not be cloned.");

    var dataObject = payload["data"] as JsonObject;
    if (dataObject is null)
    {
        throw new InvalidOperationException("Payload must include a data object.");
    }

    payload["eventId"] = eventId;
    payload["occurredAt"] = DateTimeOffset.UtcNow.ToString("O");
    dataObject["previousState"] = previousState;
    dataObject["state"] = state;

    return payload.ToJsonString(new JsonSerializerOptions
    {
        WriteIndented = false
    });
}

static string ReadRequiredState(string prompt, HashSet<string> allowedStates)
{
    while (true)
    {
        Console.Write($"{prompt} [{string.Join(", ", allowedStates)}]: ");
        var input = Console.ReadLine()?.Trim();
        if (!string.IsNullOrWhiteSpace(input))
        {
            if (allowedStates.Contains(input))
            {
                return input.ToUpperInvariant();
            }

            Console.WriteLine("Invalid status. Please enter one of the allowed values.");
            continue;
        }

        Console.WriteLine("Status is required.");
    }
}

static bool IsEnabled(string? raw)
{
    if (string.IsNullOrWhiteSpace(raw))
    {
        return false;
    }

    return string.Equals(raw, "1", StringComparison.OrdinalIgnoreCase)
        || string.Equals(raw, "true", StringComparison.OrdinalIgnoreCase)
        || string.Equals(raw, "yes", StringComparison.OrdinalIgnoreCase)
        || string.Equals(raw, "y", StringComparison.OrdinalIgnoreCase);
}

static string ComputeHmacSha256Hex(byte[] payload, string secret)
{
    using var hmac = new HMACSHA256(Encoding.UTF8.GetBytes(secret));
    var hash = hmac.ComputeHash(payload);
    return Convert.ToHexString(hash).ToLowerInvariant();
}
