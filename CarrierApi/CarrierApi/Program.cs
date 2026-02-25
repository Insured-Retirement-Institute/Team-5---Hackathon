using CarrierApi.Configuration;
using Microsoft.AspNetCore.HttpOverrides;

var builder = WebApplication.CreateBuilder(args);
var services = builder.Services;
var config = builder.Configuration;

services.Configure<ForwardedHeadersOptions>(options =>
{
    options.ForwardedHeaders = ForwardedHeaders.All;
    options.KnownNetworks.Clear();
    options.KnownProxies.Clear();
});

services.AddHealthChecks();
services.AddTelemetry(config);
services.AddServices(config);
services.AddControllers()
    .AddJsonOptions(options => 
    {
        options.JsonSerializerOptions.PropertyNameCaseInsensitive = true;
    });

services.AddRazorPages();
services.AddSignalR();
services.AddEndpointsApiExplorer();
services.AddSwaggerGen();

var app = builder.Build();

app.UseHealthChecks("/health");
app.UseForwardedHeaders();
app.UseStaticFiles();
app.UseSwagger();
app.UseSwaggerUI();
app.MapControllers();
app.MapRazorPages();
app.MapHub<CarrierApi.Hubs.TransferHub>("/transferHub");
app.Run();