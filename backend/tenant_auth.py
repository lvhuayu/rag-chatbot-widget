"""Tenant authentication helpers for ingestion and API-key token exchange."""

import json
import sqlite3
from contextlib import closing
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Optional, Set
from urllib.parse import urlsplit

import jwt


class TenantAuthError(Exception):
    def __init__(self, status_code: int, detail: str):
        super().__init__(detail)
        self.status_code = status_code
        self.detail = detail


@dataclass(frozen=True)
class SiteIdentity:
    site_id: str
    subject_type: str
    subject_id: str
    origin: Optional[str] = None


def _normalize_origin(origin: Optional[str]) -> Optional[str]:
    if not origin:
        return None
    parsed = urlsplit(origin.strip())
    if parsed.scheme not in ("http", "https") or not parsed.hostname:
        raise TenantAuthError(403, "Invalid request origin")
    host = parsed.hostname.lower()
    port = parsed.port
    if port and not (
        (parsed.scheme == "http" and port == 80)
        or (parsed.scheme == "https" and port == 443)
    ):
        host = f"{host}:{port}"
    return f"{parsed.scheme.lower()}://{host}"


def _allowed_origins(value: Optional[str]) -> Set[str]:
    if not value:
        return set()
    try:
        parsed = json.loads(value)
        entries = parsed if isinstance(parsed, list) else [parsed]
    except (json.JSONDecodeError, TypeError):
        entries = value.split(",")
    origins = set()
    for entry in entries:
        entry = str(entry).strip()
        if not entry:
            continue
        if entry == "*":
            origins.add("*")
        else:
            origins.add(_normalize_origin(entry))
    return origins


def _validate_origin(allowed_value: Optional[str], request_origin: Optional[str]) -> Optional[str]:
    allowed = _allowed_origins(allowed_value)
    origin = _normalize_origin(request_origin)
    if "*" in allowed:
        return origin
    if not origin or origin not in allowed:
        raise TenantAuthError(403, "Origin is not allowed for this API key")
    return origin


def issue_api_key_token(
    database_path: str,
    api_key: Optional[str],
    request_origin: Optional[str],
    secret: str,
    algorithm: str,
    expires_in: int = 3600,
) -> tuple[str, str]:
    if not api_key:
        raise TenantAuthError(400, "apiKey is required")
    with closing(sqlite3.connect(database_path)) as connection:
        row = connection.execute(
            """
            SELECT id, site_id, allowed_origins
            FROM api_keys
            WHERE api_key = ? AND is_active = 1
            """,
            (api_key,),
        ).fetchone()
    if not row:
        raise TenantAuthError(401, "Invalid or inactive apiKey")
    key_id, site_id, allowed_value = row
    origin = _validate_origin(allowed_value, request_origin)
    payload = {
        "tokenType": "api_key",
        "apiKeyId": key_id,
        "siteId": site_id,
        "origin": origin,
        "exp": datetime.now(timezone.utc) + timedelta(seconds=expires_in),
    }
    return jwt.encode(payload, secret, algorithm=algorithm), site_id


def authenticate_site_token(
    database_path: str,
    token: Optional[str],
    request_origin: Optional[str],
    secret: str,
    algorithm: str,
) -> SiteIdentity:
    if not token:
        raise TenantAuthError(401, "Authentication required")
    try:
        payload = jwt.decode(token, secret, algorithms=[algorithm])
    except jwt.PyJWTError as error:
        raise TenantAuthError(401, "Invalid or expired token") from error

    api_key_id = payload.get("apiKeyId")
    if api_key_id:
        with closing(sqlite3.connect(database_path)) as connection:
            row = connection.execute(
                """
                SELECT site_id, allowed_origins
                FROM api_keys
                WHERE id = ? AND is_active = 1
                """,
                (api_key_id,),
            ).fetchone()
        if not row:
            raise TenantAuthError(401, "API key is inactive or no longer exists")
        site_id, allowed_value = row
        if payload.get("siteId") != site_id:
            raise TenantAuthError(403, "Token tenant does not match API key tenant")
        origin = _validate_origin(allowed_value, request_origin)
        if payload.get("origin") != origin:
            raise TenantAuthError(403, "Token origin does not match request origin")
        return SiteIdentity(site_id, "api_key", api_key_id, origin)

    user_id = payload.get("id")
    if not user_id or payload.get("is_admin"):
        raise TenantAuthError(403, "Token is not scoped to a tenant")
    requested_site = payload.get("siteId")
    with closing(sqlite3.connect(database_path)) as connection:
        if requested_site:
            row = connection.execute(
                "SELECT site_id FROM sites WHERE site_id = ? AND user_id = ?",
                (requested_site, user_id),
            ).fetchone()
        else:
            row = connection.execute(
                """
                SELECT site_id
                FROM sites
                WHERE user_id = ?
                ORDER BY created_at ASC, site_id ASC
                LIMIT 1
                """,
                (user_id,),
            ).fetchone()
    if not row:
        raise TenantAuthError(403, "Authenticated user has no accessible site")
    return SiteIdentity(row[0], "user", user_id)


def resolve_site_id(identity: SiteIdentity, requested_site_id: Optional[str]) -> str:
    if requested_site_id and requested_site_id != identity.site_id:
        raise TenantAuthError(403, "Request tenant does not match authenticated tenant")
    return identity.site_id
