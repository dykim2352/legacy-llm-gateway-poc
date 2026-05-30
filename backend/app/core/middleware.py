import time
from collections.abc import Awaitable, Callable

from fastapi import Request, Response

from app.core.metrics import HTTP_REQUEST_DURATION_SECONDS, HTTP_REQUESTS_TOTAL


async def record_http_metrics(
    request: Request,
    call_next: Callable[[Request], Awaitable[Response]],
) -> Response:
    started_at = time.perf_counter()
    status_code = 500

    try:
        response = await call_next(request)
        status_code = response.status_code
        return response
    finally:
        path = _route_path(request)
        labels = {
            "method": request.method,
            "path": path,
            "status_code": str(status_code),
        }
        HTTP_REQUESTS_TOTAL.labels(**labels).inc()
        HTTP_REQUEST_DURATION_SECONDS.labels(**labels).observe(time.perf_counter() - started_at)


def _route_path(request: Request) -> str:
    route = request.scope.get("route")
    path = getattr(route, "path", None)
    if isinstance(path, str):
        return path
    return request.url.path
