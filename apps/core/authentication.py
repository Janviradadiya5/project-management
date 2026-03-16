import uuid
from datetime import datetime, timedelta, timezone

import jwt
from django.conf import settings
from rest_framework.authentication import BaseAuthentication

from apps.core.exceptions import AuthTokenInvalidOrExpiredException

_ALGORITHM = "HS256"
ACCESS_TOKEN_TTL_MINUTES = 15
REFRESH_TOKEN_TTL_DAYS = 7


def _secret() -> str:
    return settings.SECRET_KEY


def generate_access_token(user_id: str) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user_id),
        "type": "access",
        "iat": now,
        "exp": now + timedelta(minutes=ACCESS_TOKEN_TTL_MINUTES),
        "jti": str(uuid.uuid4()),
    }
    return jwt.encode(payload, _secret(), algorithm=_ALGORITHM)


def generate_refresh_token(user_id: str) -> tuple[str, str]:
    """Returns (encoded_token, jti)."""
    now = datetime.now(timezone.utc)
    jti = str(uuid.uuid4())
    payload = {
        "sub": str(user_id),
        "type": "refresh",
        "iat": now,
        "exp": now + timedelta(days=REFRESH_TOKEN_TTL_DAYS),
        "jti": jti,
    }
    return jwt.encode(payload, _secret(), algorithm=_ALGORITHM), jti


def decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, _secret(), algorithms=[_ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise AuthTokenInvalidOrExpiredException()
    except jwt.InvalidTokenError:
        raise AuthTokenInvalidOrExpiredException()


class JWTAuthentication(BaseAuthentication):
    def authenticate(self, request):
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return None
        token = auth_header[len("Bearer "):]
        payload = decode_token(token)
        if payload.get("type") != "access":
            raise AuthTokenInvalidOrExpiredException()
        from apps.users.models import User  # avoid circular import at module level
        try:
            user = User.objects.get(id=payload["sub"], is_active=True)
        except User.DoesNotExist:
            raise AuthTokenInvalidOrExpiredException()
        return (user, payload)

    def authenticate_header(self, request) -> str:
        return "Bearer"

