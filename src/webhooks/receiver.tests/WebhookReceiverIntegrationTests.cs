using System.Net;
using System.Security.Cryptography;
using System.Text;
using Microsoft.AspNetCore.Hosting;
using Microsoft.AspNetCore.Mvc.Testing;
using Microsoft.Extensions.Configuration;
using Xunit;

namespace AtsWebhookReceiver.Tests;

public sealed class WebhookReceiverIntegrationTests : IClassFixture<WebhookTestFactory>
{
    private readonly HttpClient _client;

    public WebhookReceiverIntegrationTests(WebhookTestFactory factory)
    {
        _client = factory.CreateClient();
    }

    [Fact]
    public async Task PostWebhook_WithValidSignature_ReturnsProcessed()
    {
        var eventId = $"evt_{Guid.NewGuid():N}";
        var payload = BuildPayload(eventId);
        using var request = BuildSignedRequest(payload, eventId, WebhookTestFactory.SharedSecret);

        using var response = await _client.SendAsync(request);
        var responseBody = await response.Content.ReadAsStringAsync();

        Assert.Equal(HttpStatusCode.OK, response.StatusCode);
        Assert.Contains("processed", responseBody, StringComparison.OrdinalIgnoreCase);
    }

    [Fact]
    public async Task PostWebhook_WithInvalidSignature_ReturnsUnauthorized()
    {
        var eventId = $"evt_{Guid.NewGuid():N}";
        var payload = BuildPayload(eventId);
        using var request = BuildSignedRequest(payload, eventId, "wrong-secret");

        using var response = await _client.SendAsync(request);

        Assert.Equal(HttpStatusCode.Unauthorized, response.StatusCode);
    }

    [Fact]
    public async Task PostWebhook_DuplicateEventId_ReturnsDuplicateIgnored()
    {
        var eventId = $"evt_{Guid.NewGuid():N}";
        var payload = BuildPayload(eventId);

        using var firstRequest = BuildSignedRequest(payload, eventId, WebhookTestFactory.SharedSecret);
        using var firstResponse = await _client.SendAsync(firstRequest);
        Assert.Equal(HttpStatusCode.OK, firstResponse.StatusCode);

        using var secondRequest = BuildSignedRequest(payload, eventId, WebhookTestFactory.SharedSecret);
        using var secondResponse = await _client.SendAsync(secondRequest);
        var secondBody = await secondResponse.Content.ReadAsStringAsync();

        Assert.Equal(HttpStatusCode.OK, secondResponse.StatusCode);
        Assert.Contains("duplicate_ignored", secondBody, StringComparison.OrdinalIgnoreCase);
    }

    private static HttpRequestMessage BuildSignedRequest(string payload, string eventId, string secret)
    {
        var signature = ComputeSignature(payload, secret);
        var request = new HttpRequestMessage(HttpMethod.Post, "/hooks/ats-status")
        {
            Content = new StringContent(payload, Encoding.UTF8, "application/json")
        };

        request.Headers.Add("X-ATS-Event-Id", eventId);
        request.Headers.Add("X-ATS-Signature", $"sha256={signature}");
        return request;
    }

    private static string ComputeSignature(string payload, string secret)
    {
        using var hmac = new HMACSHA256(Encoding.UTF8.GetBytes(secret));
        var hash = hmac.ComputeHash(Encoding.UTF8.GetBytes(payload));
        return Convert.ToHexString(hash).ToLowerInvariant();
    }

    private static string BuildPayload(string eventId) =>
        $$"""
        {
          "eventId": "{{eventId}}",
          "eventType": "transfer.status.updated",
          "occurredAt": "2026-02-24T20:09:12Z",
          "source": "centralized-hub",
          "data": {
            "transferId": "tr_abc123",
            "previousState": "VALIDATION",
            "state": "PROCESSING",
            "reasonCodes": ["ALL_REQUIREMENTS_SATISFIED"],
            "npn": "17439285"
          }
        }
        """;
}

public sealed class WebhookTestFactory : WebApplicationFactory<Program>, IDisposable
{
    public const string SharedSecret = "integration-test-shared-secret";
    private readonly string? _originalEnvVar;

    public WebhookTestFactory()
    {
        _originalEnvVar = Environment.GetEnvironmentVariable("ATS_WEBHOOK_SECRET");
        Environment.SetEnvironmentVariable("ATS_WEBHOOK_SECRET", null);
    }

    protected override void ConfigureWebHost(IWebHostBuilder builder)
    {
        builder.ConfigureAppConfiguration((_, configBuilder) =>
        {
            configBuilder.AddInMemoryCollection(new Dictionary<string, string?>
            {
                ["AtsWebhook:Secret"] = SharedSecret
            });
        });
    }

    protected override void Dispose(bool disposing)
    {
        Environment.SetEnvironmentVariable("ATS_WEBHOOK_SECRET", _originalEnvVar);
        base.Dispose(disposing);
    }
}
