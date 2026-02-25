import json
from typing import Any

from fastapi import Body, FastAPI, Request
from fastapi.responses import JSONResponse, Response

from get_agent_transfer import lambda_handler as get_agent_transfer_handler
from list_agents import lambda_handler as list_agents_handler
from post_agent_transfer import lambda_handler as post_agent_transfer_handler

app = FastAPI(title="ATS Agents Local API")


def _invoke_lambda(
    handler,
    method: str,
    path_parameters: dict[str, str] | None = None,
    query_parameters: dict[str, str] | None = None,
    headers: dict[str, str] | None = None,
    body: dict[str, Any] | None = None,
):
    event = {
        "httpMethod": method,
        "pathParameters": path_parameters or {},
        "queryStringParameters": query_parameters or {},
        "headers": headers or {},
        "body": json.dumps(body) if body is not None else None,
    }

    result = handler(event, None)
    status_code = int(result.get("statusCode", 200))
    response_headers = result.get("headers") or {}
    raw_body = result.get("body")

    if raw_body is None or raw_body == "":
        return Response(status_code=status_code, headers=response_headers)

    try:
        parsed = json.loads(raw_body)
        return JSONResponse(
            content=parsed,
            status_code=status_code,
            headers=response_headers,
        )
    except (TypeError, json.JSONDecodeError):
        return Response(
            content=str(raw_body),
            status_code=status_code,
            headers=response_headers,
            media_type="text/plain",
        )


@app.get("/ats/agents")
async def list_agents(request: Request):
    query_parameters = dict(request.query_params)
    headers = dict(request.headers)
    return _invoke_lambda(
        list_agents_handler,
        method="GET",
        query_parameters=query_parameters,
        headers=headers,
    )


@app.get("/ats/agents/{id}/transfer")
async def get_agent_transfer(id: str, request: Request):
    headers = dict(request.headers)
    return _invoke_lambda(
        get_agent_transfer_handler,
        method="GET",
        path_parameters={"id": id},
        headers=headers,
    )


@app.post("/ats/agents/{id}/transfer")
async def post_agent_transfer(id: str, request: Request, payload: dict[str, Any] = Body(...)):
    headers = dict(request.headers)
    return _invoke_lambda(
        post_agent_transfer_handler,
        method="POST",
        path_parameters={"id": id},
        headers=headers,
        body=payload,
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("local_api:app", host="0.0.0.0", port=8010, reload=True)
