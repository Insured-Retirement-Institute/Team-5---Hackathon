using CarrierApi.Models;
using Microsoft.AspNetCore.Mvc;
using CarrierApi.Clients.TransferRepo;

namespace CarrierApi.Controllers;

[ApiController]
[Route("ats/v1/transfers")]
public class TransfersController(ITransferRepository repository) : ControllerBase
{
    [HttpPost]
    public async Task<ActionResult<TransferResponse>> CreateTransfer([FromBody] TransferRequest request)
    {
        var id = Guid.NewGuid().ToString();
        await repository.SaveTransferAsync(id, request);
        return Ok(new TransferResponse 
        { 
            Id = id,
            State = "Submitted"
        });
    }

    [HttpGet]
    public async Task<ActionResult> GetRecentTransfers()
    {
        var transfers = await repository.GetRecentTransfersAsync();
        return Ok(transfers.Select(t => new { t.Id, t.Timestamp, t.Request }));
    }
}
