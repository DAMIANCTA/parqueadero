import base64
import hashlib
import hmac
import json
import threading
import time
import urllib.error
import urllib.request
from collections import defaultdict, deque
from typing import Any

from fastapi import Depends, HTTPException, Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse


LOCAL_AUDIT_EVENTS: list[dict[str, Any]] = []
_RATE_LIMIT_BUCKETS: dict[str, deque[float]] = defaultdict(deque)
_RATE_LIMIT_LOCK = threading.Lock()


def encode_access_token(
    *,
    secret_key: str,
    issuer: str,
    audience: str,
    expires_minutes: int,
    claims: dict[str, Any],
) -> str:
    header = {"alg": "HS256", "typ": "JWT"}
    now = int(time.time())
    payload = {
        **claims,
        "iss": issuer,
        "aud": audience,
        "iat": now,
        "exp": now + (expires_minutes * 60),
    }
    signing_input = f"{_b64encode_json(header)}.{_b64encode_json(payload)}"
    signature = _sign(signing_input, secret_key)
    return f"{signing_input}.{signature}"


def decode_access_token(
    *,
    token: str,
    secret_key: str,
    issuer: str,
    audience: str,
) -> dict[str, Any]:
    if not secret_key:
        raise HTTPException(status_code=500, detail="JWT secret key is not configured")

    try:
        header_segment, payload_segment, signature_segment = token.split(".")
    except ValueError as exc:
        raise HTTPException(status_code=401, detail="Malformed token") from exc

    signing_input = f"{header_segment}.{payload_segment}"
    expected_signature = _sign(signing_input, secret_key)
    if not hmac.compare_digest(signature_segment, expected_signature):
        raise HTTPException(status_code=401, detail="Invalid token signature")

    payload = _b64decode_json(payload_segment)
    if payload.get("iss") != issuer:
        raise HTTPException(status_code=401, detail="Invalid token issuer")
    if payload.get("aud") != audience:
        raise HTTPException(status_code=401, detail="Invalid token audience")
    if int(payload.get("exp", 0)) <= int(time.time()):
        raise HTTPException(status_code=401, detail="Token expired")
    return payload


def get_request_user(request: Request) -> dict[str, Any]:
    user = getattr(request.state, "user", None)
    if user is None:
        raise HTTPException(status_code=401, detail="Authentication required")
    return user


def require_permissions(*required_permissions: str):
    def dependency(request: Request) -> dict[str, Any]:
        user = get_request_user(request)
        granted = set(user.get("permissions", []))
        if "*" in granted:
            return user
        missing = [permission for permission in required_permissions if permission not in granted]
        if missing:
            raise HTTPException(status_code=403, detail=f"Missing permissions: {', '.join(missing)}")
        return user

    return Depends(dependency)


def verify_internal_audit_key(request: Request, expected_key: str) -> None:
    provided_key = request.headers.get("X-Internal-Audit-Key", "")
    if not expected_key or provided_key != expected_key:
        raise HTTPException(status_code=401, detail="Invalid internal audit key")


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(
        self,
        app,
        *,
        limit: int,
        window_seconds: int,
        excluded_paths: set[str] | None = None,
    ) -> None:
        super().__init__(app)
        self.limit = limit
        self.window_seconds = window_seconds
        self.excluded_paths = excluded_paths or set()

    async def dispatch(self, request: Request, call_next):
        if request.url.path in self.excluded_paths:
            return await call_next(request)

        client_ip = _client_ip(request)
        bucket_key = f"{client_ip}:{request.url.path}"
        now = time.time()

        with _RATE_LIMIT_LOCK:
            bucket = _RATE_LIMIT_BUCKETS[bucket_key]
            while bucket and (now - bucket[0]) > self.window_seconds:
                bucket.popleft()
            if len(bucket) >= self.limit:
                return JSONResponse(status_code=429, content={"detail": "Rate limit exceeded"})
            bucket.append(now)

        return await call_next(request)


class AuthenticationMiddleware(BaseHTTPMiddleware):
    def __init__(
        self,
        app,
        *,
        secret_key: str,
        issuer: str,
        audience: str,
        public_paths: set[str] | None = None,
        public_path_prefixes: tuple[str, ...] | None = None,
    ) -> None:
        super().__init__(app)
        self.secret_key = secret_key
        self.issuer = issuer
        self.audience = audience
        self.public_paths = public_paths or set()
        self.public_path_prefixes = public_path_prefixes or tuple()

    async def dispatch(self, request: Request, call_next):
        if (
            request.method == "OPTIONS"
            or request.url.path in self.public_paths
            or any(request.url.path.startswith(prefix) for prefix in self.public_path_prefixes)
        ):
            request.state.user = None
            return await call_next(request)

        authorization = request.headers.get("Authorization", "")
        scheme, _, token = authorization.partition(" ")
        if scheme.lower() != "bearer" or not token:
            return JSONResponse(status_code=401, content={"detail": "Bearer token required"})

        try:
            request.state.user = decode_access_token(
                token=token,
                secret_key=self.secret_key,
                issuer=self.issuer,
                audience=self.audience,
            )
        except HTTPException as exc:
            return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})
        return await call_next(request)


class AuditLogMiddleware(BaseHTTPMiddleware):
    def __init__(
        self,
        app,
        *,
        service_name: str,
        audit_enabled: bool,
        audit_service_url: str,
        internal_audit_key: str,
        excluded_paths: set[str] | None = None,
    ) -> None:
        super().__init__(app)
        self.service_name = service_name
        self.audit_enabled = audit_enabled
        self.audit_service_url = audit_service_url.rstrip("/")
        self.internal_audit_key = internal_audit_key
        self.excluded_paths = excluded_paths or set()

    async def dispatch(self, request: Request, call_next):
        started_at = time.time()
        response = await call_next(request)

        if request.url.path in self.excluded_paths:
            return response

        user = getattr(request.state, "user", None)
        event = {
            "service": self.service_name,
            "timestamp": int(time.time()),
            "method": request.method,
            "path": request.url.path,
            "status_code": response.status_code,
            "duration_ms": round((time.time() - started_at) * 1000, 2),
            "client_ip": _client_ip(request),
            "actor_user_id": user.get("sub") if isinstance(user, dict) else None,
            "actor_username": user.get("username") if isinstance(user, dict) else None,
            "actor_roles": user.get("roles", []) if isinstance(user, dict) else [],
        }
        LOCAL_AUDIT_EVENTS.append(event)

        if self.audit_enabled and self.audit_service_url and self.service_name != "audit-service":
            _send_audit_event(
                audit_service_url=self.audit_service_url,
                internal_audit_key=self.internal_audit_key,
                event=event,
            )

        return response


def _send_audit_event(*, audit_service_url: str, internal_audit_key: str, event: dict[str, Any]) -> None:
    try:
        request = urllib.request.Request(
            url=f"{audit_service_url}/audit/logs/internal",
            data=json.dumps(event).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "X-Internal-Audit-Key": internal_audit_key,
            },
            method="POST",
        )
        urllib.request.urlopen(request, timeout=0.5).read()
    except (urllib.error.URLError, TimeoutError, ValueError):
        return


def _client_ip(request: Request) -> str:
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def _sign(value: str, secret_key: str) -> str:
    digest = hmac.new(secret_key.encode("utf-8"), value.encode("utf-8"), hashlib.sha256).digest()
    return _b64encode_bytes(digest)


def _b64encode_json(payload: dict[str, Any]) -> str:
    return _b64encode_bytes(json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8"))


def _b64encode_bytes(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).decode("utf-8").rstrip("=")


def _b64decode_json(segment: str) -> dict[str, Any]:
    padding = "=" * (-len(segment) % 4)
    decoded = base64.urlsafe_b64decode(f"{segment}{padding}".encode("utf-8"))
    return json.loads(decoded.decode("utf-8"))
