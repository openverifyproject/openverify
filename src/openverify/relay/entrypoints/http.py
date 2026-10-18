"""Optional localhost Starlette adapter; graphs/providers are configured by the host."""

from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Route

from openverify.errors import ProtocolError
from openverify.relay.entrypoints.service import GraphService
from openverify.serialization import decode


def create_app(
    service: GraphService | None = None,
    *,
    token: str | None = None,
    max_body_bytes: int = 1024 * 1024,
) -> Starlette:
    host = service if service is not None else GraphService()

    async def health(request: Request) -> JSONResponse:
        return JSONResponse({"status": "ok", "protocol": "draft", "runtime": "relay-0.1"})

    async def verify(request: Request) -> JSONResponse:
        if token is not None:
            import hmac

            if not hmac.compare_digest(request.headers.get("authorization", ""), f"Bearer {token}"):
                return JSONResponse({"code": "UNAUTHORIZED"}, status_code=401)
        body = bytearray()
        async for chunk in request.stream():
            body.extend(chunk)
            if len(body) > max_body_bytes:
                return JSONResponse({"code": "BODY_TOO_LARGE"}, status_code=413)
        try:
            raw = decode(bytes(body))
            if (
                not isinstance(raw, dict)
                or set(raw) != {"graph", "inputs"}
                or not isinstance(raw["graph"], str)
                or not isinstance(raw["inputs"], dict)
            ):
                return JSONResponse({"code": "INVALID_REQUEST"}, status_code=400)
            return JSONResponse(await host.run_graph(raw["graph"], raw["inputs"]))
        except ProtocolError as exc:
            return JSONResponse(exc.as_dict(), status_code=400)

    return Starlette(routes=[Route("/health", health), Route("/verify", verify, methods=["POST"])])


def serve(port: int = 8765) -> None:
    import uvicorn

    uvicorn.run(create_app(), host="127.0.0.1", port=port)
