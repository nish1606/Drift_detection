from __future__ import annotations

import uuid
from collections.abc import Callable

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse, Response

from backend.core.exceptions import FraudGovernanceError


class RequestContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable[[Request], Response]) -> Response:
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        request.state.request_id = request_id
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response


def exception_response(exc: Exception) -> JSONResponse:
    status_code = 400 if isinstance(exc, FraudGovernanceError) else 500
    return JSONResponse(
        status_code=status_code,
        content={"detail": str(exc), "error_type": exc.__class__.__name__},
    )
