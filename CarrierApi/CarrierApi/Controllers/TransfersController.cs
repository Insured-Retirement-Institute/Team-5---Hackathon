using CarrierApi.Models;
using Microsoft.AspNetCore.Mvc;
using Microsoft.AspNetCore.SignalR;
using CarrierApi.Hubs;

namespace CarrierApi.Controllers;

[ApiController]
[Route("ats/v1/transfers")]
public class TransfersController(IHubContext<TransferHub> hubContext) : ControllerBase
{
    [HttpPost]
    public async Task<ActionResult<TransferResponse>> CreateTransfer([FromBody] TransferRequest request)
    {
        await hubContext.Clients.All.SendAsync("ReceiveTransfer", request);
        return Ok(new TransferResponse 
        { 
            Id = Guid.NewGuid().ToString(),
            State = "Submitted"
        });
    }
}
