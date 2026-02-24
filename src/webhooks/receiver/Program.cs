using System.Security.Cryptography;
using System.Text;
using System.Text.Json;

var builder = WebApplication.CreateBuilder(args);

const string secretConfigKey = "AtsWebhook:Secret";
const string secretEnvVar = "ATS_WEBHOOK_SECRET";

var app = builder.Build();

var dedupStore = new EventDedupStore(TimeSpan.FromHours(24));

app.MapGet("/health", () => Results.Ok(new { status = "ok" }));

app.MapPost("/hooks/ats-status", async (HttpContext httpContext, ILogger<Program> logger) =>
{
    var secret = Environment.GetEnvironmentVariable(secretEnvVar)
                 ?? builder.Configuration[secretConfigKey];

    if (string.IsNullOrWhiteSpace(secret))
    {
        logger.LogError("Webhook secret is not configured. Set environment variable {EnvVar} or configuration key {ConfigKey}.", secretEnvVar, secretConfigKey);
        return Results.Problem("Receiver is not configured.", statusCode: StatusCodes.Status500InternalServerError);
    }

    if (!httpContext.Request.Headers.TryGetValue("X-ATS-Signature", out var signatureValues))
    {
        return Results.Unauthorized();
    }

    if (!httpContext.Request.Headers.TryGetValue("X-ATS-Event-Id", out var eventIdValues))
    {
        return Results.BadRequest(new { error = "Missing X-ATS-Event-Id header." });
    }

    var eventId = eventIdValues.ToString();
    if (string.IsNullOrWhiteSpace(eventId))
    {
        return Results.BadRequest(new { error = "X-ATS-Event-Id cannot be empty." });
    }

    httpContext.Request.EnableBuffering();
    byte[] bodyBytes;

    using (var memoryStream = new MemoryStream())
    {
        await httpContext.Request.Body.CopyToAsync(memoryStream);
        bodyBytes = memoryStream.ToArray();
        httpContext.Request.Body.Position = 0;
    }

    var providedSignature = NormalizeSignature(signatureValues.ToString());
    var expectedSignature = ComputeHmacSha256Hex(bodyBytes, secret);

    if (!SecureEqualsHex(providedSignature, expectedSignature))
    {
        logger.LogWarning("Invalid webhook signature for event id {EventId}.", eventId);
        return Results.Unauthorized();
    }

    TransferStatusUpdateEvent? webhookEvent;
    try
    {
        webhookEvent = JsonSerializer.Deserialize<TransferStatusUpdateEvent>(bodyBytes, new JsonSerializerOptions
        {
            PropertyNameCaseInsensitive = true
        });
    }
    catch (JsonException)
    {
        return Results.BadRequest(new { error = "Invalid JSON payload." });
    }

    if (webhookEvent is null)
    {
        return Results.BadRequest(new { error = "Empty payload." });
    }

    if (!string.Equals(webhookEvent.EventType, "transfer.status.updated", StringComparison.Ordinal))
    {
        return Results.BadRequest(new { error = "Unsupported eventType." });
    }

    if (!string.Equals(webhookEvent.EventId, eventId, StringComparison.Ordinal))
    {
        return Results.BadRequest(new { error = "Header event id does not match payload eventId." });
    }

    if (!dedupStore.TryRegister(eventId))
    {
        logger.LogInformation("Duplicate webhook event ignored. Event id: {EventId}", eventId);
        return Results.Ok(new { status = "duplicate_ignored", eventId });
    }

    logger.LogInformation(
        "Processed transfer status update. EventId={EventId}, TransferId={TransferId}, PreviousState={PreviousState}, State={State}, Npn={Npn}",
        webhookEvent.EventId,
        webhookEvent.Data.TransferId,
        webhookEvent.Data.PreviousState,
        webhookEvent.Data.State,
        webhookEvent.Data.Npn);

    return Results.Ok(new { status = "processed", eventId });
});

app.Run();

static string ComputeHmacSha256Hex(byte[] payload, string secret)
{
    using var hmac = new HMACSHA256(Encoding.UTF8.GetBytes(secret));
    var hash = hmac.ComputeHash(payload);
    return Convert.ToHexString(hash).ToLowerInvariant();
}

static string NormalizeSignature(string signature)
{
    const string prefix = "sha256=";
    return signature.StartsWith(prefix, StringComparison.OrdinalIgnoreCase)
        ? signature[prefix.Length..].Trim().ToLowerInvariant()
        : signature.Trim().ToLowerInvariant();
}

static bool SecureEqualsHex(string leftHex, string rightHex)
{
    if (leftHex.Length != rightHex.Length)
    {
        return false;
    }

    try
    {
        var leftBytes = Convert.FromHexString(leftHex);
        var rightBytes = Convert.FromHexString(rightHex);
        return CryptographicOperations.FixedTimeEquals(leftBytes, rightBytes);
    }
    catch (FormatException)
    {
        return false;
    }
}

public partial class Program;
