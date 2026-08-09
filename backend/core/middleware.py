from __future__ import annotations

import time
import uuid
from collections.abc import Callable
from dataclasses import dataclass, field
from threading import Lock

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse, Response

from backend.core.exceptions import FraudGovernanceError


@dataclass
class _RateLimitBucket:
    limit: int
    window: float
    requests: list[float] = field(default_factory=list)
    lock: Lock = field(default_factory=Lock)


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, limit: int = 60, window: float = 60.0) -> None:
        super().__init__(app)
        self._limit = limit
        self._window = window
        self._buckets: dict[str, _RateLimitBucket] = {}
        self._lock = Lock()

    async def dispatch(self, request: Request, call_next: Callable[[Request], Response]) -> Response:
        if request.url.path in {"/docs", "/openapi.json", "/redoc", "/health", "/ready"}:
            return await call_next(request)

        client_ip = request.client.host if request.client else "unknown"
        bucket = self._get_bucket(client_ip)

        now = time.time()
        with bucket.lock:
            bucket.requests = [ts for ts in bucket.requests if now - ts < self._window]
            if len(bucket.requests) >= self._limit:
                return JSONResponse(
                    status_code=429,
                    content={"detail": "Rate limit exceeded", "error_type": "RateLimitExceeded"},
                )
            bucket.requests.append(now)

        return await call_next(request)

    def _get_bucket(self, client_ip: str) -> _RateLimitBucket:
        with self._lock:
            if client_ip not in self._buckets:
                self._buckets[client_ip] = _RateLimitBucket(limit=self._limit, window=self._window)
            return self._buckets[client_ip]


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
