FROM mcr.microsoft.com/dotnet/sdk:10.0 AS build
WORKDIR /src

COPY src/webhooks/receiver/AtsWebhookReceiver.csproj src/webhooks/receiver/
RUN dotnet restore src/webhooks/receiver/AtsWebhookReceiver.csproj

COPY . .
RUN dotnet publish src/webhooks/receiver/AtsWebhookReceiver.csproj -c Release -o /app/publish /p:UseAppHost=false

FROM mcr.microsoft.com/dotnet/aspnet:10.0 AS runtime
WORKDIR /app
COPY --from=build /app/publish .

ENV ASPNETCORE_URLS=http://+:8080
EXPOSE 8080

ENTRYPOINT ["dotnet", "AtsWebhookReceiver.dll"]
