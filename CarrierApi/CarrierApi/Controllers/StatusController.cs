using CarrierApi.Clients.AtsHub;
using CarrierApi.Models;
using Microsoft.AspNetCore.Mvc;

namespace CarrierApi.Controllers;

[ApiController]
[Route("ats/v1/status")]
public class StatusController(IAtsHubClient atsHub) : ControllerBase
{
    [HttpPost]
    public async Task<IActionResult> SendStatus([FromBody] AtsStatus status)
    {
        await atsHub.SendStatus(status);
        return Ok();
    }
}
