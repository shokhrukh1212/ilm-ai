from typing import Annotated, Any

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import PyJWKClient

from .settings import settings

_bearer = HTTPBearer()

_jwks_client: PyJWKClient | None = None


def _get_jwks_client() -> PyJWKClient:
    global _jwks_client
    if _jwks_client is None:
        url = f"{settings.supabase_url}/auth/v1/.well-known/jwks.json"
        _jwks_client = PyJWKClient(url, cache_keys=True)
    return _jwks_client


def _decode_token(token: str) -> dict[str, Any]:
    header = jwt.get_unverified_header(token)
    alg = header.get("alg", "RS256")

    if alg == "HS256":
        if not settings.supabase_jwt_secret:
            raise jwt.InvalidTokenError("SUPABASE_JWT_SECRET is not configured")
        return jwt.decode(  # type: ignore[no-any-return]
            token,
            settings.supabase_jwt_secret,
            algorithms=["HS256"],
            audience="authenticated",
            options={"verify_aud": True},
        )

    # Asymmetric (RS256, ES256, …) — let the JWK declare its own algorithm
    signing_key = _get_jwks_client().get_signing_key_from_jwt(token)
    return jwt.decode(  # type: ignore[no-any-return]
        token,
        signing_key.key,
        algorithms=[signing_key.algorithm_name],
        audience="authenticated",
        options={"verify_aud": True},
    )


def get_current_user_id(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(_bearer)],
) -> str:
    token = credentials.credentials
    try:
        payload = _decode_token(token)
        user_id: str = payload["sub"]
        return user_id
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired")
    except jwt.InvalidTokenError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc))
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
